#!/bin/python3

SPEC2006_INT_BENCHES = ["400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk", "456.hmmer",
                  "458.sjeng", "462.libquantum", "464.h264ref", "471.omnetpp", "473.astar", "483.xalancbmk"]
SPEC2006_FP_BENCHES = ["410.bwaves", "416.gamess", "433.milc", "434.zeusmp", "435.gromacs", "436.cactusADM",
                  "437.leslie3d", "444.namd", "447.dealII", "450.soplex", "453.povray", "454.calculix",
                  "459.GemsFDTD", "465.tonto", "470.lbm", "481.wrf", "482.sphinx3"]
SPEC2017_INT_BENCHES = ["600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s", 
                  "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s", 
                  "648.exchange2_s", "657.xz_s"]
SPEC2017_FP_BENCHES = ["603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s", "627.cam4_s",
                  "628.pop2_s", "638.imagick_s", "644.nab_s", "649.fotonik3d_s", "654.roms_s"]

def parse_benchmark_logs(log_file_path):
    """
    解析SPEC基准测试日志文件，提取每个测试块
    
    参数:
        log_file_path (str): run_all.log文件的路径
        
    返回:
        list: 包含所有测试块的列表，每个测试块是一个字符串
    """
    try:
        with open(log_file_path, 'r') as file:
            content = file.read()
            
        # 使用正则表达式匹配以'Running'开头，'completed'结尾的块
        import re
        pattern = re.compile(r'Running.*?completed', re.DOTALL)
        benchmarks = pattern.findall(content)
        
        return benchmarks
    except FileNotFoundError:
        print(f"Error: File {log_file_path} not found")
        return []
    except Exception as e:
        print(f"Error parsing log file: {str(e)}")
        return []

def get_bench_name(benchmark_block):
    """
    从benchmark_block中提取基准测试名称
    
    参数:
        benchmark_block (str): 包含基准测试块的字符串
        
    返回:
        str: 纯净的基准测试名称，如'400.perlbench'
    """
    import re
    # 匹配Running行并提取测试名称
    match = re.search(r'Running (.*?)\.\.\.', benchmark_block)
    if match:
        return match.group(1)
    return ""

def get_ref_time(benchmark_block):
    """
    从benchmark_block中提取参考时间(Reftime)
    
    参数:
        benchmark_block (str): 包含基准测试块的字符串
        
    返回:
        float: 参考时间值，如果未找到返回0.0
    """
    import re
    # 查找包含Reftime:的行并提取后面的数字
    match = re.search(r'Reftime:\s*(\d+\.?\d*)', benchmark_block)
    if match:
        return float(match.group(1))
    return 0.0

def get_test_block(benchmark_block):
    """
    从benchmark_block中提取测试时间数据块
    
    参数:
        benchmark_block (str): 包含基准测试块的字符串
        
    返回:
        list: 包含所有测试时间数据块的列表
    """
    import re
    # 匹配所有从'Test'开始到'sys'开头之间的内容
    matches = re.findall(r'(Test.*?sys.*?\n)', benchmark_block, re.DOTALL)
    return [match.strip() for match in matches] if matches else []

def get_real_time(test_block):
    """
    从测试块中提取实际运行时间
    
    参数:
        test_block (str): 包含测试时间数据的字符串
        
    返回:
        float: 实际运行时间值，如果未找到返回0.0
    """
    import re
    # 查找包含'real'的行并提取后面的时间数值
    match = re.search(r'real\s+(\d+\.?\d*)', test_block)
    if match:
        return float(match.group(1))
    return 0.0

def is_int_bench(bench_name):
    return bench_name in SPEC2006_INT_BENCHES + SPEC2017_INT_BENCHES

def is_fp_bench(bench_name):
    return bench_name in SPEC2006_FP_BENCHES + SPEC2017_FP_BENCHES

def median(lst):
    """
    计算列表的中位数
    
    参数:
        lst (list): 数值列表
        
    返回:
        float: 中位数，如果列表为空返回0.0
    """
    if not lst:
        return 0.0
    
    sorted_lst = sorted(lst)
    n = len(sorted_lst)
    
    if n % 2 == 1:
        return sorted_lst[n//2]
    else:
        return (sorted_lst[n//2-1] + sorted_lst[n//2]) / 2

def geomean(scores):
    """
    计算列表的几何平均数
    
    参数:
        scores (list): 分数列表
        
    返回:
        float: 几何平均数，如果列表为空返回0.0
    """
    if not scores:
        return 0.0
    
    product = 1.0
    for score in scores:
        product *= score
    
    return product ** (1.0 / len(scores))

def get_run_time(benchmarks):
    return len(get_test_block(benchmarks[0]))

def get_max_benchname_len(benchmarks):
    max_benchname_len = 0
    for benchmark_block in benchmarks:
        bench_name_len = len(get_bench_name(benchmark_block))
        if bench_name_len > max_benchname_len:
            max_benchname_len = bench_name_len
    return max_benchname_len

def main(log_path, output_file, clock_rate):
    benchmarks = parse_benchmark_logs(log_path)
    run_time = get_run_time(benchmarks)
    max_benchname_len = get_max_benchname_len(benchmarks)

    sep_len = max_benchname_len + run_time * 9 + 27
    if clock_rate != "1":
        sep_len = sep_len + 9

    csv_buffer = ""

    # First Line
    print("=" * sep_len)
    if clock_rate != "1":
        print("{:^{}}".format("Use clock rate: " + clock_rate + " GHz", sep_len))
        print("-" * sep_len)
    print("{:<{}} ".format("Bench", max_benchname_len), end="")
    csv_buffer = csv_buffer + "Bench,"
    print("{:>8} ".format("RefTime"), end="")
    csv_buffer = csv_buffer + "RefTime,"
    for i in range(run_time):
        print("{:>8} ".format(f"#{i+1}Time"), end="")
        csv_buffer = csv_buffer + f"#{i+1}Time,"
    if clock_rate != "1":
        print("{:>8} {:>8} {:>8}".format("Median", "Score", "S/GHz"))
        csv_buffer = csv_buffer + "Median,Score,S/GHz,ClockRate\n"
    else:
        print("{:>8} {:>8}".format("Median", "Score"))
        csv_buffer = csv_buffer + "Median,Score\n"
    print("-" * sep_len)
    
    scores = []
    # int Benchmark Lines
    int_scores = []
    for benchmark_block in benchmarks:
        bench_name = get_bench_name(benchmark_block)
        if is_int_bench(bench_name):
            print("{:<{}} ".format(bench_name, max_benchname_len), end="")
            csv_buffer = csv_buffer + f"{bench_name},"
            ref_time = get_ref_time(benchmark_block)
            print("{:>8.2f} ".format(ref_time), end="")
            csv_buffer = csv_buffer + f"{ref_time},"
            real_times = []
            for time_block in get_test_block(benchmark_block):
                real_time = get_real_time(time_block)
                real_times.append(real_time)
                print("{:>8} ".format(real_time), end="")
                csv_buffer = csv_buffer + f"{real_time},"
            median_time = median(real_times)
            score = ref_time/median_time
            if clock_rate!= "1":
                score_ghz = score/float(clock_rate)
                print("{:>8.2f} {:>8.2f} {:>8.2f}".format(median_time, score, score_ghz))
                csv_buffer = csv_buffer + f"{median_time},{score},{score_ghz},{clock_rate}\n"
            else:
                print("{:>8.2f} {:>8.2f}".format(median_time, score))
                csv_buffer = csv_buffer + f"{median_time},{score}\n"
            scores.append(score)
            int_scores.append(score)

    if int_scores:
        # int End Line
        print("-" * sep_len)
        print("{:<{}} ".format("INT GEOMEAN", max_benchname_len), end="")
        csv_buffer = csv_buffer + f"INT GEOMEAN,"
        print("{:>8} ".format("-"), end="")
        csv_buffer = csv_buffer + f"-,"
        for i in range(run_time):
            print("{:>8} ".format(f"-"), end="")
            csv_buffer = csv_buffer + f"-,"
        geomean_score = geomean(int_scores)
        if clock_rate!= "1":
            geomean_score_ghz = geomean_score/float(clock_rate)
            print("{:>8} {:>8.2f} {:>8.2f}".format("-", geomean_score, geomean_score_ghz))
            csv_buffer = csv_buffer + f"-,{geomean_score},{geomean_score_ghz},{clock_rate}\n"
        else:
            print("{:>8} {:>8.2f}".format("-", geomean_score))
            csv_buffer = csv_buffer + f"-,{geomean_score}\n"
    
    bool_fp = False
    for benchmark_block in benchmarks:
        bench_name = get_bench_name(benchmark_block)
        if is_fp_bench(bench_name):
            bool_fp = True
            break
    
    if int_scores and bool_fp:
        print("-" * sep_len)

    # fp Benchmark Lines
    fp_scores = []
    for benchmark_block in benchmarks:
        bench_name = get_bench_name(benchmark_block)
        if is_fp_bench(bench_name):
            print("{:<{}} ".format(bench_name, max_benchname_len), end="")
            csv_buffer = csv_buffer + f"{bench_name},"
            ref_time = get_ref_time(benchmark_block)
            print("{:>8.2f} ".format(ref_time), end="")
            csv_buffer = csv_buffer + f"{ref_time},"
            real_times = []
            for time_block in get_test_block(benchmark_block):
                real_time = get_real_time(time_block)
                real_times.append(real_time)
                print("{:>8} ".format(real_time), end="")
                csv_buffer = csv_buffer + f"{real_time},"
            median_time = median(real_times)
            score = ref_time/median_time
            if clock_rate!= "1":
                score_ghz = score/float(clock_rate)
                print("{:>8.2f} {:>8.2f} {:>8.2f}".format(median_time, score, score_ghz))
                csv_buffer = csv_buffer + f"{median_time},{score},{score_ghz},{clock_rate}\n"
            else:
                print("{:>8.2f} {:>8.2f}".format(median_time, score))
                csv_buffer = csv_buffer + f"{median_time},{score}\n"
            scores.append(score)
            fp_scores.append(score)
    
    if fp_scores:
        # fp End Line
        print("-" * sep_len)
        print("{:<{}} ".format("FP GEOMEAN", max_benchname_len), end="")
        csv_buffer = csv_buffer + f"FP GEOMEAN,"
        print("{:>8} ".format("-"), end="")
        csv_buffer = csv_buffer + f"-,"
        for i in range(run_time):
            print("{:>8} ".format(f"-"), end="")
            csv_buffer = csv_buffer + f"-,"
        geomean_score = geomean(fp_scores)
        if clock_rate!= "1":
            geomean_score_ghz = geomean_score/float(clock_rate)
            print("{:>8} {:>8.2f} {:>8.2f}".format("-", geomean_score, geomean_score_ghz))
            csv_buffer = csv_buffer + f"-,{geomean_score},{geomean_score_ghz},{clock_rate}\n"
        else:
            print("{:>8} {:>8.2f}".format("-", geomean_score))
            csv_buffer = csv_buffer + f"-,{geomean_score}\n"
    
    if int_scores and fp_scores:
        print("-" * sep_len)
        # End Line
        print("{:<{}} ".format("GEOMEAN", max_benchname_len), end="")
        csv_buffer = csv_buffer + f"GEOMEAN,"
        print("{:>8} ".format("-"), end="")
        csv_buffer = csv_buffer + f"-,"
        for i in range(run_time):
            print("{:>8} ".format(f"-"), end="")
            csv_buffer = csv_buffer + f"-,"
        geomean_score = geomean(scores)
        if clock_rate!= "1":
            geomean_score_ghz = geomean_score/float(clock_rate)
            print("{:>8} {:>8.2f} {:>8.2f}".format("-", geomean_score, geomean_score_ghz))
            csv_buffer = csv_buffer + f"-,{geomean_score},{geomean_score_ghz},{clock_rate}\n"
        else:
            print("{:>8} {:>8.2f}".format("-", geomean_score))
            csv_buffer = csv_buffer + f"-,{geomean_score}\n"
    print("=" * sep_len)

    with open(output_file, "w") as f:
        f.write(csv_buffer)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: cal_score.py <log_file_path> [clock_rate] [output_file] ")
        sys.exit(1)
    clock_rate = "1" if len(sys.argv) < 3 else sys.argv[2]
    output_file = "score.csv" if len(sys.argv) < 4 else sys.argv[3]
    main(sys.argv[1], output_file, clock_rate)