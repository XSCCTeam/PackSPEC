#!/bin/python3
"""
SPEC CPU 测试分数计算脚本

从 SPEC 基准测试运行日志中解析各基准测试的运行时间和参考时间，
计算各测试分数，并输出表格化的分数报告和 CSV/Markdown 格式文件。

功能：
- 解析 run_all.log 中的测试结果（支持 SPEC2006 和 SPEC2017）
- 计算中位运行时间、分数和按主频归一化分数
- 分别计算 INT/FP 以及总的 GEOMEAN（几何平均数）
- 生成格式化的终端输出 + CSV 文件 + Markdown 分数报告

用法:
    python cal_score.py <log_file_path> [clock_rate] [output_file]

参数:
    log_file_path:  SPEC 运行日志文件路径（如 run_all.log）
    clock_rate:     CPU 主频，单位 GHz，默认 1
    output_file:    CSV 输出文件路径，默认 score.csv

示例:
    python cal_score.py run_all.log 2.5 score.csv
"""

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
SPEC2017_INT_RATE_BENCHES = ["500.perlbench_r", "502.gcc_r", "505.mcf_r", "520.omnetpp_r",
                  "523.xalancbmk_r", "525.x264_r", "531.deepsjeng_r", "541.leela_r",
                  "548.exchange2_r", "557.xz_r"]
SPEC2017_FP_RATE_BENCHES = ["503.bwaves_r", "507.cactuBSSN_r", "508.namd_r", "510.parest_r",
                  "511.povray_r", "519.lbm_r", "521.wrf_r", "526.blender_r", "527.cam4_r",
                  "538.imagick_r", "544.nab_r", "549.fotonik3d_r", "554.roms_r"]

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
    """
    判断是否为整数基准测试

    Args:
        bench_name (str): 基准测试名称

    Returns:
        bool: 如果属于 SPEC2006_INT、SPEC2017_INT 或 SPEC2017_INT_RATE 中任一集合则返回 True
    """
    return bench_name in SPEC2006_INT_BENCHES + SPEC2017_INT_BENCHES + SPEC2017_INT_RATE_BENCHES

def is_fp_bench(bench_name):
    """
    判断是否为浮点基准测试

    Args:
        bench_name (str): 基准测试名称

    Returns:
        bool: 如果属于 SPEC2006_FP、SPEC2017_FP 或 SPEC2017_FP_RATE 中任一集合则返回 True
    """
    return bench_name in SPEC2006_FP_BENCHES + SPEC2017_FP_BENCHES + SPEC2017_FP_RATE_BENCHES

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
    """
    获取基准测试的迭代运行次数

    Args:
        benchmarks (list): 解析后的 benchmark block 列表

    Returns:
        int: 每个基准测试的迭代运行次数（从第一个 benchmark 的 test block 数量推断）
    """
    return len(get_test_block(benchmarks[0]))

def get_max_benchname_len(benchmarks):
    """
    获取所有基准测试名称的最大长度

    Args:
        benchmarks (list): 解析后的 benchmark block 列表

    Returns:
        int: 最长基准测试名称的字符数，用于格式化输出对齐
    """
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
            median_time = median(real_times) or 0.01
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
            median_time = median(real_times) or 0.01
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

    # 生成 score.md
    md_output_file = output_file.rsplit('.', 1)[0] + ".md" if '.' in output_file else output_file + ".md"
    generate_score_md(md_output_file, benchmarks, run_time, max_benchname_len, clock_rate)


def generate_score_md(md_output_file, benchmarks, run_time, max_benchname_len, clock_rate):
    """生成 Markdown 格式的分数表格"""
    lines = []

    # 表头
    headers = ["Bench", "RefTime"]
    for i in range(run_time):
        headers.append(f"#{i+1}Time")
    headers.append("Median")
    headers.append("Score")
    if clock_rate != "1":
        headers.append("S/GHz")

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    def format_row(name, ref_time, real_times, median_time, score, score_ghz=None):
        cols = [name, f"{ref_time:.2f}" if ref_time != "-" else "-"]
        for t in real_times:
            cols.append(str(t) if t != "-" else "-")
        cols.append(f"{median_time:.2f}" if median_time != "-" else "-")
        cols.append(f"{score:.2f}" if score != "-" else "-")
        if clock_rate != "1":
            cols.append(f"{score_ghz:.2f}" if score_ghz != "-" else "-")
        return "| " + " | ".join(cols) + " |"

    def format_summary_row(name, score, score_ghz=None):
        cols = [name, "-"]
        for _ in range(run_time):
            cols.append("-")
        cols.append("-")
        cols.append(f"{score:.2f}")
        if clock_rate != "1":
            cols.append(f"{score_ghz:.2f}")
        return "| " + " | ".join(cols) + " |"

    # INT benchmarks
    int_scores = []
    for benchmark_block in benchmarks:
        bench_name = get_bench_name(benchmark_block)
        if is_int_bench(bench_name):
            ref_time = get_ref_time(benchmark_block)
            real_times = [get_real_time(tb) for tb in get_test_block(benchmark_block)]
            median_time = median(real_times) or 0.01
            score = ref_time / median_time
            score_ghz = score / float(clock_rate) if clock_rate != "1" else None
            lines.append(format_row(bench_name, ref_time, real_times, median_time, score, score_ghz))
            int_scores.append(score)

    if int_scores:
        int_geomean = geomean(int_scores)
        int_geomean_ghz = int_geomean / float(clock_rate) if clock_rate != "1" else None
        lines.append(format_summary_row("**INT GEOMEAN**", int_geomean, int_geomean_ghz))

    # FP benchmarks
    fp_scores = []
    for benchmark_block in benchmarks:
        bench_name = get_bench_name(benchmark_block)
        if is_fp_bench(bench_name):
            ref_time = get_ref_time(benchmark_block)
            real_times = [get_real_time(tb) for tb in get_test_block(benchmark_block)]
            median_time = median(real_times) or 0.01
            score = ref_time / median_time
            score_ghz = score / float(clock_rate) if clock_rate != "1" else None
            lines.append(format_row(bench_name, ref_time, real_times, median_time, score, score_ghz))
            fp_scores.append(score)

    if fp_scores:
        fp_geomean = geomean(fp_scores)
        fp_geomean_ghz = fp_geomean / float(clock_rate) if clock_rate != "1" else None
        lines.append(format_summary_row("**FP GEOMEAN**", fp_geomean, fp_geomean_ghz))

    if int_scores and fp_scores:
        all_scores = int_scores + fp_scores
        all_geomean = geomean(all_scores)
        all_geomean_ghz = all_geomean / float(clock_rate) if clock_rate != "1" else None
        lines.append(format_summary_row("**GEOMEAN**", all_geomean, all_geomean_ghz))

    with open(md_output_file, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: cal_score.py <log_file_path> [clock_rate] [output_file] ")
        sys.exit(1)
    clock_rate = "1" if len(sys.argv) < 3 else sys.argv[2]
    output_file = "score.csv" if len(sys.argv) < 4 else sys.argv[3]
    main(sys.argv[1], output_file, clock_rate)