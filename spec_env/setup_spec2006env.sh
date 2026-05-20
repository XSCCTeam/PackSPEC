#!/bin/bash

# SPEC CPU 2006环境设置脚本
# 通过 OpenList API (/api/fs/get) 获取带签名下载链接，下载 ISO 和校验文件，自动校验后安装

set -euo pipefail

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

mkdir -p spec2006 || error_exit "无法创建 spec2006 目录" 1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INFO_LABEL="${BLUE}[INFO]${NC}"
ATTENTION_LABEL="${YELLOW}[ATTENTION]${NC}"
ERROR_LABEL="${RED}[ERROR]${NC}"
SUCCESS_LABEL="${GREEN}[SUCCESS]${NC}"

DEFAULT_OPENLIST_BASE_URL="http://172.38.8.157:5244"
DEFAULT_ISO_REMOTE_PATH="/cpu2006/cpu2006-1.2.iso"
DEFAULT_HASH_REMOTE_PATH="/cpu2006/cpu2006-1.2.iso.sha256"
DEFAULT_SPEC2006_ISO="$SCRIPT_DIR/spec2006/cpu2006-1.2.iso"
DEFAULT_SPEC2006_HASH="$SCRIPT_DIR/spec2006/cpu2006-1.2.iso.sha256"
DEFAULT_SPEC2006_UNPACK_DIR="$SCRIPT_DIR/spec2006/cpu2006-1.2"
DEFAULT_SPEC2006_INSTALL_DIR="$SCRIPT_DIR/spec2006/speccpu2006-v1.2"

OPENLIST_BASE_URL="${OPENLIST_BASE_URL:-$DEFAULT_OPENLIST_BASE_URL}"
ISO_REMOTE_PATH="${ISO_REMOTE_PATH:-$DEFAULT_ISO_REMOTE_PATH}"
HASH_REMOTE_PATH="${HASH_REMOTE_PATH:-$DEFAULT_HASH_REMOTE_PATH}"
SPEC2006_ISO="${SPEC2006_ISO:-$DEFAULT_SPEC2006_ISO}"
SPEC2006_HASH="${SPEC2006_HASH:-$DEFAULT_SPEC2006_HASH}"
SPEC2006_UNPACK_DIR="${SPEC2006_UNPACK_DIR:-$DEFAULT_SPEC2006_UNPACK_DIR}"
SPEC2006_INSTALL_DIR="${SPEC2006_INSTALL_DIR:-$DEFAULT_SPEC2006_INSTALL_DIR}"

LOG_DIR="$SCRIPT_DIR/spec2006/logs"
mkdir -p "$LOG_DIR" || error_exit "无法创建日志目录 '$LOG_DIR'" 1

if [ ! -d "$LOG_DIR" ]; then
    error_exit "日志目录 '$LOG_DIR' 创建失败" 1
fi

LOG_FILE="$LOG_DIR/setup_spec2006_$(date '+%Y%m%d_%H%M%S').log"

if ! touch "$LOG_FILE" 2>/dev/null; then
    error_exit "无法创建日志文件 '$LOG_FILE'" 1
fi
rm -f "$LOG_FILE"

log() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "$timestamp $level $message"
    echo -e "$timestamp $level $message" >> "$LOG_FILE"
}

error_exit() {
    log "$ERROR_LABEL" "$1"
    log "$ERROR_LABEL" "安装失败，退出代码: $2"
    exit "$2"
}

MIN_FREE_SPACE_GB=10

check_dependencies() {
    log "$INFO_LABEL" "检查依赖..."

    for cmd in wget curl bsdtar sha256sum jq; do
        if ! command -v "$cmd" &> /dev/null; then
            case "$cmd" in
                bsdtar)
                    error_exit "依赖命令 '$cmd' 未找到，请安装: sudo apt install libarchive-tools" 1
                    ;;
                jq)
                    error_exit "依赖命令 '$cmd' 未找到，请安装: sudo apt install jq" 1
                    ;;
                *)
                    error_exit "依赖命令 '$cmd' 未找到，请安装后重试" 1
                    ;;
            esac
        fi
        log "$INFO_LABEL" "✓ $cmd 已安装"
    done
}

check_write_permission() {
    log "$INFO_LABEL" "检查写入权限..."

    local target_dir="$SCRIPT_DIR/spec2006"
    if [ -d "$target_dir" ]; then
        if [ ! -w "$target_dir" ]; then
            error_exit "目录 '$target_dir' 无写入权限，请检查权限或使用其他目录" 10
        fi
    else
        if [ ! -w "$SCRIPT_DIR" ]; then
            error_exit "目录 '$SCRIPT_DIR' 无写入权限，无法创建 spec2006 目录" 10
        fi
    fi

    log "$INFO_LABEL" "✓ 写入权限正常"
}

check_disk_space() {
    log "$INFO_LABEL" "检查磁盘空间..."

    local target_dir="$SCRIPT_DIR"
    local available_kb
    available_kb=$(df "$target_dir" | awk 'NR==2 {print $4}')
    local available_gb=$((available_kb / 1024 / 1024))

    if [ "$available_gb" -lt "$MIN_FREE_SPACE_GB" ]; then
        error_exit "磁盘空间不足: 可用 ${available_gb}GB，至少需要 ${MIN_FREE_SPACE_GB}GB (ISO ~2.7GB + 解压空间)" 11
    fi

    log "$INFO_LABEL" "✓ 磁盘空间充足: 可用 ${available_gb}GB"
}

get_download_url() {
    local remote_path="$1"

    local api_url="${OPENLIST_BASE_URL}/api/fs/get"
    local response
    response=$(curl -s --noproxy '*' -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -d "{\"path\":\"${remote_path}\"}" 2>&1) || true

    if [ -z "$response" ]; then
        error_exit "OpenList API 请求失败：无响应" 9
    fi

    local code
    code=$(echo "$response" | jq -r '.code' 2>/dev/null) || true

    if [ "$code" != "200" ]; then
        local message
        message=$(echo "$response" | jq -r '.message' 2>/dev/null) || echo "未知错误"
        error_exit "OpenList API 返回错误 (code=$code): $message" 9
    fi

    local download_url
    download_url=$(echo "$response" | jq -r '.data.raw_url' 2>/dev/null) || true

    if [ -z "$download_url" ] || [ "$download_url" = "null" ]; then
        download_url=$(echo "$response" | jq -r '.data.provider' 2>/dev/null) || true
    fi

    if [ -z "$download_url" ] || [ "$download_url" = "null" ]; then
        error_exit "无法获取文件 '$remote_path' 的下载链接" 9
    fi

    download_url=$(echo "$download_url" | sed 's/\\u0026/\&/g')

    echo "$download_url"
}

download_file() {
    local remote_path="$1"
    local local_dest="$2"
    local description="$3"

    if [ -f "$local_dest" ]; then
        log "$ATTENTION_LABEL" "$description 已存在: '$local_dest'，跳过下载"
        return 0
    fi

    log "$INFO_LABEL" "获取 $description 的下载链接..."
    local download_url
    download_url=$(get_download_url "$remote_path")

    log "$INFO_LABEL" "下载 $description..."
    log "$INFO_LABEL" "下载链接: $download_url"

    if ! wget --no-proxy -q "$download_url" -O "$local_dest" --show-progress; then
        rm -f "$local_dest"
        error_exit "下载 $description 失败" 2
    fi

    log "$SUCCESS_LABEL" "$description 下载完成"
}

download_iso() {
    log "$INFO_LABEL" "准备下载SPEC CPU 2006 ISO文件和校验文件..."

    download_file "$ISO_REMOTE_PATH" "$SPEC2006_ISO" "ISO文件"
    download_file "$HASH_REMOTE_PATH" "$SPEC2006_HASH" "SHA256校验文件"
}

verify_iso() {
    log "$INFO_LABEL" "校验ISO文件完整性..."

    if [ ! -f "$SPEC2006_HASH" ]; then
        log "$ATTENTION_LABEL" "校验文件不存在，跳过校验"
        return 0
    fi

    local expected_hash
    expected_hash=$(awk '{print $1}' "$SPEC2006_HASH")

    if [ -z "$expected_hash" ]; then
        log "$ATTENTION_LABEL" "校验文件内容为空，跳过校验"
        return 0
    fi

    log "$INFO_LABEL" "计算本地文件的 SHA256（大文件可能需要较长时间）..."
    local actual_hash
    actual_hash=$(sha256sum "$SPEC2006_ISO" | awk '{print $1}')

    if [ "$actual_hash" = "$expected_hash" ]; then
        log "$SUCCESS_LABEL" "SHA256 校验通过: $actual_hash"
    else
        log "$ERROR_LABEL" "SHA256 校验失败!"
        log "$ERROR_LABEL" "期望: $expected_hash"
        log "$ERROR_LABEL" "实际: $actual_hash"
        log "$ATTENTION_LABEL" "删除已下载的文件，请重新运行脚本"
        rm -f "$SPEC2006_ISO" "$SPEC2006_HASH"
        error_exit "SHA256 校验失败，ISO文件可能损坏或被篡改" 8
    fi
}

unpack_iso() {
    log "$INFO_LABEL" "准备解压ISO文件..."
    
    if [ -d "$SPEC2006_UNPACK_DIR" ]; then
        log "$ATTENTION_LABEL" "解压目录 '$SPEC2006_UNPACK_DIR' 已存在，跳过解压"
        fix_unpack_permissions
        return 0
    fi

    mkdir -p "$SPEC2006_UNPACK_DIR" || error_exit "创建解压目录失败" 3

    log "$INFO_LABEL" "解压 $SPEC2006_ISO 到 $SPEC2006_UNPACK_DIR..."

    if ! bsdtar -xf "$SPEC2006_ISO" -C "$SPEC2006_UNPACK_DIR" 2>&1 | tee -a "$LOG_FILE"; then
        error_exit "解压ISO文件失败" 4
    fi

    fix_unpack_permissions

    log "$SUCCESS_LABEL" "ISO文件解压完成"
}

fix_unpack_permissions() {
    log "$INFO_LABEL" "修复ISO解压文件的只读权限..."

    if [ ! -d "$SPEC2006_UNPACK_DIR" ]; then
        return 0
    fi

    local readonly_count
    readonly_count=$(find "$SPEC2006_UNPACK_DIR" ! -writable -type f 2>/dev/null | wc -l)

    if [ "$readonly_count" -gt 0 ]; then
        log "$INFO_LABEL" "发现 $readonly_count 个只读文件，修复权限..."
        chmod -R u+w "$SPEC2006_UNPACK_DIR"
        log "$SUCCESS_LABEL" "权限修复完成"
    else
        log "$INFO_LABEL" "✓ 无只读文件需要修复"
    fi
}

install_spec2006() {
    log "$INFO_LABEL" "准备安装SPEC CPU 2006..."

    cd "$SPEC2006_UNPACK_DIR" || error_exit "切换到解压目录失败" 5

    if [ ! -f "install.sh" ]; then
        error_exit "install.sh 脚本未找到，解压可能失败" 6
    fi

    log "$ATTENTION_LABEL" "开始安装SPEC CPU 2006..."
    log "$INFO_LABEL" "将自动接受安装协议"

    mkdir -p "$SPEC2006_INSTALL_DIR" || error_exit "创建安装目录失败" 3

    if ! ./install.sh -d "$SPEC2006_INSTALL_DIR" <<< "yes" 2>&1 | tee -a "$LOG_FILE"; then
        error_exit "安装SPEC CPU 2006失败" 7
    fi

    log "$SUCCESS_LABEL" "SPEC CPU 2006安装完成"
}

verify_installation() {
    log "$INFO_LABEL" "验证安装..."

    local key_files=("shrc" "bin/runspec")
    local all_found=true

    for file in "${key_files[@]}"; do
        if [ ! -f "$file" ]; then
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

cleanup() {
    log "$INFO_LABEL" "是否清理ISO和校验文件？(Y/n) [5秒后自动选择Y]"

    set +e
    read -r -t 5 cleanup_iso
    local read_status=$?
    set -e

    if [[ $read_status -ne 0 ]] || [[ ! "$cleanup_iso" =~ ^[Nn]$ ]]; then
        if [[ $read_status -eq 124 ]]; then
            log "$INFO_LABEL" "超时，自动选择清理文件"
        fi
        rm -f "$SPEC2006_ISO" "$SPEC2006_HASH"
        if [ ! -f "$SPEC2006_ISO" ]; then
            log "$SUCCESS_LABEL" "ISO和校验文件已清理"
        else
            log "$ERROR_LABEL" "清理文件失败"
        fi
    else
        log "$INFO_LABEL" "保留ISO和校验文件"
    fi
}

show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -o, --openlist URL      指定OpenList服务地址（默认: $DEFAULT_OPENLIST_BASE_URL）"
    echo "  -i, --iso FILE          指定本地ISO文件路径（默认: $DEFAULT_SPEC2006_ISO）"
    echo "  -d, --dir DIR           指定安装目录（默认: $DEFAULT_SPEC2006_INSTALL_DIR）"
    echo ""
    echo "环境变量:"
    echo "  OPENLIST_BASE_URL       与 -o 选项相同"
    echo "  ISO_REMOTE_PATH         OpenList上ISO文件的远程路径"
    echo "  HASH_REMOTE_PATH        OpenList上校验文件的远程路径"
    echo "  SPEC2006_ISO            与 -i 选项相同"
    echo "  SPEC2006_INSTALL_DIR    与 -d 选项相同"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -o|--openlist)
                OPENLIST_BASE_URL="$2"
                shift 2
                ;;
            -i|--iso)
                SPEC2006_ISO="$2"
                shift 2
                ;;
            -d|--dir)
                SPEC2006_INSTALL_DIR="$2"
                shift 2
                ;;
            *)
                error_exit "未知选项: $1" 127
                ;;
        esac
    done
}

main() {
    log "$INFO_LABEL" "开始安装SPEC CPU 2006环境"
    log "$INFO_LABEL" "日志文件: $LOG_FILE"

    parse_args "$@"
    check_dependencies
    check_write_permission
    check_disk_space
    download_iso
    verify_iso
    unpack_iso
    install_spec2006
    verify_installation
    cleanup

    log "$SUCCESS_LABEL" "SPEC CPU 2006环境设置完成！"
    log "$INFO_LABEL" "使用方法: cd $SPEC2006_INSTALL_DIR && source shrc"

    exit 0
}

main "$@"