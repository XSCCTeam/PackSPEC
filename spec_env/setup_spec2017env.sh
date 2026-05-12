#!/bin/bash

# SPEC CPU 2017环境设置脚本 - 改进版
# 提供更健全的错误处理、日志记录和用户体验

set -euo pipefail  # 启用更严格的错误检查

# 脚本根目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# 创建 spec2017 目录
mkdir -p spec2017 || error_exit "无法创建 spec2017 目录" 1 

# 颜色和标签定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

INFO_LABEL="${BLUE}[INFO]${NC}"
ATTENTION_LABEL="${YELLOW}[ATTENTION]${NC}"
ERROR_LABEL="${RED}[ERROR]${NC}"
SUCCESS_LABEL="${GREEN}[SUCCESS]${NC}"

# 默认配置
DEFAULT_SPEC2017_URL="http://172.38.10.144/api/v4/projects/66/packages/generic/cpu2017/1.1.9/cpu2017-1.1.9.iso"
DEFAULT_SPEC2017_ISO="$SCRIPT_DIR/spec2017/cpu2017-1.1.9.iso"
DEFAULT_SPEC2017_UNPACK_DIR="$SCRIPT_DIR/spec2017/cpu2017-1.1.9"
DEFAULT_SPEC2017_INSTALL_DIR="$SCRIPT_DIR/spec2017/speccpu2017-v1.1.9"

# 配置变量
SPEC2017_URL="${SPEC2017_URL:-$DEFAULT_SPEC2017_URL}"
SPEC2017_ISO="${SPEC2017_ISO:-$DEFAULT_SPEC2017_ISO}"
SPEC2017_UNPACK_DIR="${SPEC2017_UNPACK_DIR:-$DEFAULT_SPEC2017_UNPACK_DIR}"
SPEC2017_INSTALL_DIR="${SPEC2017_INSTALL_DIR:-$DEFAULT_SPEC2017_INSTALL_DIR}"

# 创建日志目录
LOG_DIR="$SCRIPT_DIR/spec2017/logs"
mkdir -p "$LOG_DIR" || error_exit "无法创建日志目录 '$LOG_DIR'" 1

# 验证日志目录是否创建成功
if [ ! -d "$LOG_DIR" ]; then
    error_exit "日志目录 '$LOG_DIR' 创建失败" 1
fi

# 日志文件
LOG_FILE="$LOG_DIR/setup_spec2017_$(date '+%Y%m%d_%H%M%S').log"

# 验证日志文件是否可以创建
if ! touch "$LOG_FILE" 2>/dev/null; then
    error_exit "无法创建日志文件 '$LOG_FILE'" 1
fi
rm -f "$LOG_FILE"  # 临时文件，用于验证

# 日志函数
log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "$timestamp $level $message"
    echo -e "$timestamp $level $message" >> "$LOG_FILE"
}

# 错误处理函数
error_exit() {
    log "$ERROR_LABEL" "$1"
    log "$ERROR_LABEL" "安装失败，退出代码: $2"
    exit "$2"
}

# 检查依赖
check_dependencies() {
    log "$INFO_LABEL" "检查依赖..."
    
    for cmd in wget bsdtar; do
        if ! command -v "$cmd" &> /dev/null; then
            if [ "$cmd" == "bsdtar" ]; then
                error_exit "依赖命令 '$cmd' 未找到，请安装后重试，可通过 sudo apt install libarchive-tools 命令安装" 1
            fi
            error_exit "依赖命令 '$cmd' 未找到，请安装后重试" 1
        fi
        log "$INFO_LABEL" "✓ $cmd 已安装"
    done
}

# 下载ISO文件
download_iso() {
    log "$INFO_LABEL" "准备下载SPEC CPU 2017 ISO文件..."
    
    if [ -f "$SPEC2017_ISO" ]; then
        log "$ATTENTION_LABEL" "ISO文件 '$SPEC2017_ISO' 已存在，跳过下载"
        return 0
    fi
    
    log "$INFO_LABEL" "从 $SPEC2017_URL 下载 $SPEC2017_ISO..."
    
    if ! wget -q "$SPEC2017_URL" -O "$SPEC2017_ISO" --show-progress; then
        error_exit "下载ISO文件失败" 2
    fi
    
    log "$SUCCESS_LABEL" "ISO文件下载完成"
}

# 解压ISO文件
unpack_iso() {
    log "$INFO_LABEL" "准备解压ISO文件..."
    
    if [ -d "$SPEC2017_UNPACK_DIR" ]; then
        log "$ATTENTION_LABEL" "解压目录 '$SPEC2017_UNPACK_DIR' 已存在，跳过解压"
        return 0
    fi
    
    mkdir -p "$SPEC2017_UNPACK_DIR" || error_exit "创建解压目录失败" 3
    
    log "$INFO_LABEL" "解压 $SPEC2017_ISO 到 $SPEC2017_UNPACK_DIR..."
    
    if ! bsdtar -xf "$SPEC2017_ISO" -C "$SPEC2017_UNPACK_DIR" 2>&1 | tee -a "$LOG_FILE"; then
        error_exit "解压ISO文件失败" 4
    fi
    
    log "$SUCCESS_LABEL" "ISO文件解压完成"
}

# 安装SPEC CPU 2017
install_spec2017() {
    log "$INFO_LABEL" "准备安装SPEC CPU 2017..."
    
    cd "$SPEC2017_UNPACK_DIR" || error_exit "切换到解压目录失败" 5
    
    if [ ! -f "install.sh" ]; then
        error_exit "install.sh 脚本未找到，解压可能失败" 6
    fi
    
    log "$ATTENTION_LABEL" "开始安装SPEC CPU 2017..."
    log "$INFO_LABEL" "将自动接受安装协议"
    
    mkdir -p "$SPEC2017_INSTALL_DIR" || error_exit "创建安装目录失败" 3

    if ! ./install.sh -d "$SPEC2017_INSTALL_DIR" <<< "yes" 2>&1 | tee -a "$LOG_FILE"; then
        error_exit "安装SPEC CPU 2017失败" 7
    fi
    
    log "$SUCCESS_LABEL" "SPEC CPU 2017安装完成"
}

# 验证安装
verify_installation() {
    log "$INFO_LABEL" "验证安装..."
    
    # 检查关键文件是否存在
    local key_files=("shrc" "bin/runspec")
    local all_found=true
    
    for file in "${key_files[@]}"; do
        if [ ! -f "$SPEC2017_INSTALL_DIR/$file" ]; then
            log "$ERROR_LABEL" "关键文件 '$file' 未找到"
            all_found=false
        fi
    done
    
    if $all_found; then
        log "$SUCCESS_LABEL" "安装验证通过"
    else
        log "$ATTENTION_LABEL" "安装验证不完全通过，但继续执行"
    fi
}

# 清理临时文件
cleanup() {
    log "$INFO_LABEL" "是否清理ISO文件？(Y/n) [5秒后自动选择Y]"
    
    # 临时禁用 set -e，因为 read 超时会返回非零退出码
    set +e
    read -r -t 5 cleanup_iso
    local read_status=$?  # 保存read命令的退出状态
    set -e  # 重新启用 set -e
    
    # 默认清理ISO文件（超时或输入y/Y时清理，只有输入n/N时保留）
    if [[ $read_status -ne 0 ]] || [[ ! "$cleanup_iso" =~ ^[Nn]$ ]]; then
        if [[ $read_status -eq 124 ]]; then
            log "$INFO_LABEL" "超时，自动选择清理ISO文件"
        fi
        if rm -f "$SPEC2017_ISO"; then
            log "$SUCCESS_LABEL" "ISO文件已清理"
        else
            log "$ERROR_LABEL" "清理ISO文件失败"
        fi
    else
        log "$INFO_LABEL" "保留ISO文件"
    fi
}

# 显示帮助信息
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help            显示此帮助信息"
    echo "  -u, --url URL         指定SPEC2017 ISO文件的下载URL"
    echo "  -i, --iso FILE        指定ISO文件名（默认: $DEFAULT_SPEC2017_ISO）"
    echo "  -d, --dir DIR         指定安装目录（默认: $DEFAULT_SPEC2017_INSTALL_DIR）"
    echo ""
    echo "环境变量:"
    echo "  SPEC2017_URL          与 -u 选项相同"
    echo "  SPEC2017_ISO          与 -i 选项相同"
    echo "  SPEC2017_INSTALL_DIR  与 -d 选项相同"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--url)
                SPEC2017_URL="$2"
                shift 2
                ;;
            -i|--iso)
                SPEC2017_ISO="$2"
                shift 2
                ;;
            -d|--dir)
                SPEC2017_INSTALL_DIR="$2"
                shift 2
                ;;
            *)
                error_exit "未知选项: $1" 127
                ;;
        esac
    done
}

# 主函数
main() {
    log "$INFO_LABEL" "开始安装SPEC CPU 2017环境"
    log "$INFO_LABEL" "日志文件: $LOG_FILE"
    
    parse_args "$@"
    check_dependencies
    download_iso
    unpack_iso
    install_spec2017
    verify_installation
    cleanup
    
    log "$SUCCESS_LABEL" "SPEC CPU 2017环境设置完成！"
    log "$INFO_LABEL" "使用方法: cd $SPEC2017_INSTALL_DIR && source shrc"
    
    exit 0
}

# 执行主函数
main "$@"