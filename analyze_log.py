#!/usr/bin/env python3
"""
分析SPEC CPU2017基准测试日志文件，统计各测试用例的运行时间
"""
from config import *
import re
import sys
from pathlib import Path
import math

# 整数基准测试列表
SPEC2017_INT_BENCHMARKS = {
    '600.perlbench_s': {'ref': 1775, 'train': 101, 'test': 74},
    '602.gcc_s': {'ref': 3982, 'train': 188, 'test': 2},
    '605.mcf_s': {'ref': 4721, 'train': 251, 'test': 40},
    '620.omnetpp_s': {'ref': 1631, 'train': 188, 'test': 16},
    '623.xalancbmk_s': {'ref': 1417, 'train': 271, 'test': 2},
    '625.x264_s': {'ref': 1764, 'train': 153, 'test': 186},
    '631.deepsjeng_s': {'ref': 1433, 'train': 290, 'test': 41},
    '641.leela_s': {'ref': 1706, 'train': 267, 'test': 17},
    '648.exchange2_s': {'ref': 2940, 'train': 210, 'test': 74},
    '657.xz_s': {'ref': 6182, 'train': 86, 'test': 30}
}

# 浮点数基准测试列表
SPEC2017_FP_BENCHMARKS = {
    '603.bwaves_s': {'ref': 58998, 'train': 682, 'test': 117}, 
    '607.cactuBSSN_s': {'ref': 16670, 'train': 122, 'test': 16}, 
    '619.lbm_s': {'ref': 5238, 'train': 802, 'test': 61}, 
    '621.wrf_s': {'ref': 13226, 'train': 291, 'test': 50},
    '627.cam4_s': {'ref': 8863, 'train': 436, 'test': 260}, 
    '628.pop2_s': {'ref': 11873, 'train': 350, 'test': 15}, 
    '638.imagick_s': {'ref': 14426, 'train': 74, 'test': 2}, 
    '644.nab_s': {'ref': 17472, 'train': 583, 'test': 9},
    '649.fotonik3d_s': {'ref': 9116, 'train': 279, 'test': 10},
    '654.roms_s': {'ref': 15745, 'train': 621, 'test': 17}
}

def parse_log_file(log_file):
    """解析日志文件，提取每个基准测试的运行时间
    
    Args:
        log_file: 日志文件路径
        
    Returns:
        dict: 包含每个基准测试及其运行时间的字典
    """
    results = {}
    current_bench = None
    
    with open(log_file, 'r') as f:
        for line in f:
            # 查找基准测试名称
            if 'Running' in line and '..' in line:
                match = re.search(r'Running\s+(\d+\.\w+)', line)
                if match:
                    current_bench = match.group(1)
            # 查找real时间
            elif current_bench and 'real' in line:
                match = re.search(r'real\s+(\d+\.\d+)', line)
                if match:
                    results[current_bench] = float(match.group(1))
                    current_bench = None
                    
    return results

def format_output(results, input_type='ref'):
    """格式化输出结果
    
    按照SPEC CPU2017的格式输出结果，分为整数和浮点数基准测试两部分
    
    Args:
        results: 包含基准测试结果的字典
        input_type: 输入类型（ref/train/test）
    """
    
    # 定义列宽
    bench_width = 18  # 基准测试名称列宽
    num_width = 12    # 数字列宽
    title_width = bench_width + 3*num_width  # 标题总宽度
    
    # 输出表头格式
    header = "{:<{w1}}  {:>{w2}}  {:>{w2}}  {:>{w2}}".format(
        "Benchmark", "Run(s)", "Ref(s)", "Ratio",
        w1=bench_width, w2=num_width-4
    )
    
    def print_title(title):
        """打印美化的标题"""
        print("*" * title_width)
        padding = (title_width - len(title) - 2) // 2
        print("*" + " " * padding + title + " " * (title_width - padding - len(title) - 2) + "*")
        print("*" * title_width)
    
    # 输出整数基准测试结果
    print_title("SPECint 2017")
    print(header)
    print("-" * title_width)

    for bench in SPEC2017_INT_BENCHMARKS.keys():
        ref_time = SPEC2017_INT_BENCHMARKS[bench][input_type]
        if bench in results:
            run_time = max(results[bench], 0.001)
            ratio = ref_time/run_time

            print("{:<{w1}}  {:{w2}.2f}  {:{w2}.2f}  {:{w2}.2f}".format(
                bench, run_time, ref_time, ratio,
                w1=bench_width, w2=num_width-4
            ))
    
    # 检查是否包含所有整数基准测试
    int_ratios = []
    missing_benchmarks = []
    for bench in SPEC2017_INT_BENCHMARKS.keys():
        if bench in results:
            run_time = max(results[bench], 0.001)
            ratio = SPEC2017_INT_BENCHMARKS[bench][input_type] / run_time
            int_ratios.append(ratio)
        else:
            missing_benchmarks.append(bench)
    
    # 如果包含所有测试，计算几何平均分
    if not missing_benchmarks:
        geomean = math.exp(sum(math.log(r) for r in int_ratios) / len(int_ratios))
        print("-" * title_width)
        print("{:<{w1}}  {:{w2}}  {:{w2}}  {:{w2}.2f}".format(
            "SPECint2017_score", "", "", geomean,
            w1=bench_width, w2=num_width-4
        ))
    print()  # 添加最后的空行

    # 输出浮点数基准测试结果
    print_title("SPECfp 2017")
    print(header)
    print("-" * title_width)
    
    for bench in SPEC2017_FP_BENCHMARKS.keys():
        ref_time = SPEC2017_FP_BENCHMARKS[bench][input_type]
        if bench in results:
            run_time = max(results[bench], 0.001)
            ratio = ref_time/run_time

            print("{:<{w1}}  {:{w2}.2f}  {:{w2}.2f}  {:{w2}.2f}".format(
                bench, run_time, ref_time, ratio,
                w1=bench_width, w2=num_width-4
            ))

    # 检查是否包含所有浮点数基准测试
    fp_ratios = []
    missing_benchmarks = []
    for bench in SPEC2017_FP_BENCHMARKS.keys():
        if bench in results:
            run_time = max(results[bench], 0.001)
            ratio = SPEC2017_FP_BENCHMARKS[bench][input_type] / run_time
            fp_ratios.append(ratio)
        else:
            missing_benchmarks.append(bench)
    
    # 如果包含所有测试，计算几何平均分
    if not missing_benchmarks:
        geomean = math.exp(sum(math.log(r) for r in fp_ratios) / len(fp_ratios))
        print("-" * title_width)
        print("{:<{w1}}  {:{w2}}  {:{w2}}  {:{w2}.2f}".format(
            "SPECfp2017_score", "", "", geomean,
            w1=bench_width, w2=num_width-4
        ))
    
    print()  # 添加最后的空行

def main():
    """主程序入口"""
    # 如果提供了命令行参数，使用它作为日志文件路径
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        # 否则使用默认路径
        log_file = str(Path(__file__).parent / 'packed_files' / 'run_llvm19-m64' / 'run_all.log')
    
    if not Path(log_file).exists():
        print(f"错误：找不到日志文件 '{log_file}'")
        sys.exit(1)
        
    results = parse_log_file(log_file)
    format_output(results, "test")

if __name__ == "__main__":
    main()
