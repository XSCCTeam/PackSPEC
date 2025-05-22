#!/usr/bin/python3
import csv
import re
import argparse

"""
perf record -g -o 1.perf.data ./your_program
perf report -n --stdio -i 1.perf.data > perf_report.txt
"""

def parse_perf_report(input_file, output_file):
    # 用于匹配 perf 主体行的正则表达式（包含百分比开头的主行）
    perf_line_regex = re.compile(
        r'^\s*([\d.]+%)\s+([\d.]+%)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\[\S+\])\s+(.*)$'
    )

    # 定义 CSV 表头
    headers = ["Children", "Self", "Samples", "Command", "Shared_Object", "Symbol_Type", "Function"]

    rows = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = perf_line_regex.match(line)
            if match:
                row = list(match.groups())
                rows.append(row)

    # 写入 CSV 文件
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    
    return len(rows)

if __name__ == "__main__":
    # 输入和输出文件路径
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='将 perf 报告转换为 CSV 文件')
    # 添加输入文件路径参数
    parser.add_argument('-i', '--input', default='perf_report.txt', help='输入的 perf 报告文件路径，默认为 perf_report.txt')
    # 添加输出文件路径参数
    parser.add_argument('-o', '--output', default='perf_report.csv', help='输出的 CSV 文件路径，默认为 perf_report.csv')

    # 解析命令行参数
    args = parser.parse_args()

    perf_input_file = args.input
    perf_output_file = args.output
    # 解析并写入 CSV 文件
    rows_len = parse_perf_report(perf_input_file, perf_output_file)
    print(f"Export successful, a total of {rows_len} rows have been extracted and saved as: {perf_output_file}")
