#!/bin/sh

# 极简版SPEC分数计算脚本
# 使用POSIX shell语法，不依赖Python
# 仅依赖awk和sed等基本命令

# 检查参数
if [ $# -lt 1 ]; then
    printf "Usage: %s <log_file_path> [clock_rate] [output_file]\n" "$0"
    exit 1
fi

LOG_FILE="$1"
CLOCK_RATE="${2:-1}"
OUTPUT_FILE="${3:-score.csv}"

# 检查日志文件是否存在
if [ ! -f "$LOG_FILE" ]; then
    printf "Error: File %s not found\n" "$LOG_FILE"
    exit 1
fi

# 使用awk解析日志文件并计算分数
awk -v clock_rate="$CLOCK_RATE" -v output_file="$OUTPUT_FILE" '
BEGIN {
    bench_idx = 0
    in_bench = 0
    csv_buffer = ""
}

# 计算中位数
function median(arr, n,    i, j, temp, sorted) {
    if (n == 0) return 0
    for (i = 1; i <= n; i++) sorted[i] = arr[i]
    for (i = 1; i <= n; i++) {
        for (j = i + 1; j <= n; j++) {
            if (sorted[i] > sorted[j]) {
                temp = sorted[i]
                sorted[i] = sorted[j]
                sorted[j] = temp
            }
        }
    }
    if (n % 2 == 1) {
        return sorted[int(n/2) + 1]
    } else {
        return (sorted[n/2] + sorted[n/2 + 1]) / 2
    }
}

# 计算几何平均数
function geomean(arr, n,    i, prod) {
    if (n == 0) return 0
    prod = 1.0
    for (i = 1; i <= n; i++) {
        prod = prod * arr[i]
    }
    return exp(log(prod) / n)
}

# 检查是否为整数基准测试
function is_int(name) {
    if (name == "400.perlbench") return 1
    if (name == "401.bzip2") return 1
    if (name == "403.gcc") return 1
    if (name == "429.mcf") return 1
    if (name == "445.gobmk") return 1
    if (name == "456.hmmer") return 1
    if (name == "458.sjeng") return 1
    if (name == "462.libquantum") return 1
    if (name == "464.h264ref") return 1
    if (name == "471.omnetpp") return 1
    if (name == "473.astar") return 1
    if (name == "483.xalancbmk") return 1
    if (name == "600.perlbench_s") return 1
    if (name == "602.gcc_s") return 1
    if (name == "605.mcf_s") return 1
    if (name == "620.omnetpp_s") return 1
    if (name == "623.xalancbmk_s") return 1
    if (name == "625.x264_s") return 1
    if (name == "631.deepsjeng_s") return 1
    if (name == "641.leela_s") return 1
    if (name == "648.exchange2_s") return 1
    if (name == "657.xz_s") return 1
    return 0
}

# 检查是否为浮点基准测试
function is_fp(name) {
    if (name == "410.bwaves") return 1
    if (name == "416.gamess") return 1
    if (name == "433.milc") return 1
    if (name == "434.zeusmp") return 1
    if (name == "435.gromacs") return 1
    if (name == "436.cactusADM") return 1
    if (name == "437.leslie3d") return 1
    if (name == "444.namd") return 1
    if (name == "447.dealII") return 1
    if (name == "450.soplex") return 1
    if (name == "453.povray") return 1
    if (name == "454.calculix") return 1
    if (name == "459.GemsFDTD") return 1
    if (name == "465.tonto") return 1
    if (name == "470.lbm") return 1
    if (name == "481.wrf") return 1
    if (name == "482.sphinx3") return 1
    if (name == "603.bwaves_s") return 1
    if (name == "607.cactuBSSN_s") return 1
    if (name == "619.lbm_s") return 1
    if (name == "621.wrf_s") return 1
    if (name == "627.cam4_s") return 1
    if (name == "628.pop2_s") return 1
    if (name == "638.imagick_s") return 1
    if (name == "644.nab_s") return 1
    if (name == "649.fotonik3d_s") return 1
    if (name == "654.roms_s") return 1
    return 0
}

# 重复字符串
function repeat(s, n,    result, i) {
    result = ""
    for (i = 1; i <= n; i++) result = result s
    return result
}

# 匹配Running行
/^Running / {
    bench_name = substr($0, 9)
    sub(/\.\.\..*/, "", bench_name)
    bench_idx++
    bench_names[bench_idx] = bench_name
    in_bench = 1
    time_count[bench_idx] = 0
}

# 匹配Reftime行
/^Reftime:/ {
    ref_time[bench_idx] = $2 + 0
}

# 匹配real时间行
/^real / {
    if (in_bench) {
        time_count[bench_idx]++
        real_times[bench_idx, time_count[bench_idx]] = $2 + 0
    }
}

# 匹配completed行
/completed/ {
    in_bench = 0
}

END {
    # 计算最大基准测试名称长度
    max_len = 0
    for (i = 1; i <= bench_idx; i++) {
        if (length(bench_names[i]) > max_len) {
            max_len = length(bench_names[i])
        }
    }
    
    # 计算运行次数
    run_times = 0
    for (i = 1; i <= bench_idx; i++) {
        if (time_count[i] > run_times) {
            run_times = time_count[i]
        }
    }
    
    # 计算分隔线长度
    sep_len = max_len + run_times * 9 + 27
    if (clock_rate != "1") {
        sep_len = sep_len + 9
    }
    
    # 打印表头
    printf "%s\n", repeat("=", sep_len)
    if (clock_rate != "1") {
        printf "%*s\n", sep_len, "Use clock rate: " clock_rate " GHz"
        printf "%s\n", repeat("-", sep_len)
    }
    
    # 表头行
    printf "%-*s ", max_len, "Bench"
    csv_buffer = csv_buffer "Bench,"
    printf "%8s ", "RefTime"
    csv_buffer = csv_buffer "RefTime,"
    for (i = 1; i <= run_times; i++) {
        printf "%8s ", "#" i "Time"
        csv_buffer = csv_buffer "#" i "Time,"
    }
    if (clock_rate != "1") {
        printf "%8s %8s %8s\n", "Median", "Score", "S/GHz"
        csv_buffer = csv_buffer "Median,Score,S/GHz,ClockRate\n"
    } else {
        printf "%8s %8s\n", "Median", "Score"
        csv_buffer = csv_buffer "Median,Score\n"
    }
    printf "%s\n", repeat("-", sep_len)
    
    # 整数基准测试
    int_score_count = 0
    for (i = 1; i <= bench_idx; i++) {
        if (is_int(bench_names[i])) {
            printf "%-*s ", max_len, bench_names[i]
            csv_buffer = csv_buffer bench_names[i] ","
            printf "%8.2f ", ref_time[i]
            csv_buffer = csv_buffer ref_time[i] ","
            
            # 收集时间数据
            for (j = 1; j <= time_count[i]; j++) {
                times_arr[j] = real_times[i, j]
                printf "%8.2f ", real_times[i, j]
                csv_buffer = csv_buffer real_times[i, j] ","
            }
            
            med = median(times_arr, time_count[i])
            score = ref_time[i] / med
            int_score_count++
            int_scores[int_score_count] = score
            
            if (clock_rate != "1") {
                score_ghz = score / clock_rate
                printf "%8.2f %8.2f %8.2f\n", med, score, score_ghz
                csv_buffer = csv_buffer med "," score "," score_ghz "," clock_rate "\n"
            } else {
                printf "%8.2f %8.2f\n", med, score
                csv_buffer = csv_buffer med "," score "\n"
            }
        }
    }
    
    # 整数几何平均
    if (int_score_count > 0) {
        printf "%s\n", repeat("-", sep_len)
        printf "%-*s ", max_len, "INT GEOMEAN"
        csv_buffer = csv_buffer "INT GEOMEAN,"
        printf "%8s ", "-"
        csv_buffer = csv_buffer "-,"
        for (i = 1; i <= run_times; i++) {
            printf "%8s ", "-"
            csv_buffer = csv_buffer "-,"
        }
        int_geo = geomean(int_scores, int_score_count)
        if (clock_rate != "1") {
            int_geo_ghz = int_geo / clock_rate
            printf "%8s %8.2f %8.2f\n", "-", int_geo, int_geo_ghz
            csv_buffer = csv_buffer "-," int_geo "," int_geo_ghz "," clock_rate "\n"
        } else {
            printf "%8s %8.2f\n", "-", int_geo
            csv_buffer = csv_buffer "-," int_geo "\n"
        }
    }
    
    # 检查是否有浮点测试
    has_fp = 0
    for (i = 1; i <= bench_idx; i++) {
        if (is_fp(bench_names[i])) {
            has_fp = 1
            break
        }
    }
    
    if (int_score_count > 0 && has_fp) {
        printf "%s\n", repeat("-", sep_len)
    }
    
    # 浮点基准测试
    fp_score_count = 0
    for (i = 1; i <= bench_idx; i++) {
        if (is_fp(bench_names[i])) {
            printf "%-*s ", max_len, bench_names[i]
            csv_buffer = csv_buffer bench_names[i] ","
            printf "%8.2f ", ref_time[i]
            csv_buffer = csv_buffer ref_time[i] ","
            
            for (j = 1; j <= time_count[i]; j++) {
                times_arr[j] = real_times[i, j]
                printf "%8.2f ", real_times[i, j]
                csv_buffer = csv_buffer real_times[i, j] ","
            }
            
            med = median(times_arr, time_count[i])
            score = ref_time[i] / med
            fp_score_count++
            fp_scores[fp_score_count] = score
            
            if (clock_rate != "1") {
                score_ghz = score / clock_rate
                printf "%8.2f %8.2f %8.2f\n", med, score, score_ghz
                csv_buffer = csv_buffer med "," score "," score_ghz "," clock_rate "\n"
            } else {
                printf "%8.2f %8.2f\n", med, score
                csv_buffer = csv_buffer med "," score "\n"
            }
        }
    }
    
    # 浮点几何平均
    if (fp_score_count > 0) {
        printf "%s\n", repeat("-", sep_len)
        printf "%-*s ", max_len, "FP GEOMEAN"
        csv_buffer = csv_buffer "FP GEOMEAN,"
        printf "%8s ", "-"
        csv_buffer = csv_buffer "-,"
        for (i = 1; i <= run_times; i++) {
            printf "%8s ", "-"
            csv_buffer = csv_buffer "-,"
        }
        fp_geo = geomean(fp_scores, fp_score_count)
        if (clock_rate != "1") {
            fp_geo_ghz = fp_geo / clock_rate
            printf "%8s %8.2f %8.2f\n", "-", fp_geo, fp_geo_ghz
            csv_buffer = csv_buffer "-," fp_geo "," fp_geo_ghz "," clock_rate "\n"
        } else {
            printf "%8s %8.2f\n", "-", fp_geo
            csv_buffer = csv_buffer "-," fp_geo "\n"
        }
    }
    
    # 总几何平均
    if (int_score_count > 0 && fp_score_count > 0) {
        printf "%s\n", repeat("-", sep_len)
        printf "%-*s ", max_len, "GEOMEAN"
        csv_buffer = csv_buffer "GEOMEAN,"
        printf "%8s ", "-"
        csv_buffer = csv_buffer "-,"
        for (i = 1; i <= run_times; i++) {
            printf "%8s ", "-"
            csv_buffer = csv_buffer "-,"
        }
        
        # 合并所有分数
        total_count = int_score_count + fp_score_count
        for (i = 1; i <= int_score_count; i++) {
            all_scores[i] = int_scores[i]
        }
        for (i = 1; i <= fp_score_count; i++) {
            all_scores[int_score_count + i] = fp_scores[i]
        }
        
        total_geo = geomean(all_scores, total_count)
        if (clock_rate != "1") {
            total_geo_ghz = total_geo / clock_rate
            printf "%8s %8.2f %8.2f\n", "-", total_geo, total_geo_ghz
            csv_buffer = csv_buffer "-," total_geo "," total_geo_ghz "," clock_rate "\n"
        } else {
            printf "%8s %8.2f\n", "-", total_geo
            csv_buffer = csv_buffer "-," total_geo "\n"
        }
    }
    printf "%s\n", repeat("=", sep_len)
    
    # 写入CSV文件
    print csv_buffer > output_file
}
' "$LOG_FILE"
