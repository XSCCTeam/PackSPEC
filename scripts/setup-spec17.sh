#!/bin/bash

# set -x
set -e

# 默认值设置
SPEC_DIR=/SPECcpu2017
SPEC_CFG=llvm19.cfg
SPEC_ACTION=setup
SPEC_TUNE=base
SPEC_INPUT=test
SPEC_BENCHES="intspeed fpspeed"
SPEC_ITERATIONS=3
SPEC_REBUILD=true

# 显示帮助信息
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --spec-dir PATH         设置SPEC路径 (默认: /SPECcpu2017)"
    echo "  --config CFG            设置配置文件 (默认: llvm19.cfg)"
    echo "  --action ACTION         设置动作 (默认: setup)"
    echo "  --tune TUNE             设置优化类型 (默认: base)"
    echo "  --input INPUT           设置输入类型 (默认: test)"
    echo "  --benches BENCHES       设置测试集合 (默认: \"all\")"
    echo "  --iterations ITERATIONS 设置测试次数 (默认: 3)"
    echo "  --rebuild               启用重新编译 (默认: 禁用)"
    echo "  --help                  显示此帮助信息"
    exit 1
}


# 处理命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        --spec-dir) SPEC_DIR="$2"; shift ;;
        --config) SPEC_CFG="$2"; shift ;;
        --action) SPEC_ACTION="$2"; shift ;;
        --tune) SPEC_TUNE="$2"; shift ;;
        --input) SPEC_INPUT="$2"; shift ;;
        --benches) SPEC_BENCHES="$2"; shift ;;
        --iterations) SPEC_ITERATIONS="$2"; shift ;;
        --rebuild) SPEC_REBUILD=true ;;
        --help) show_help ;;
        *) echo "Unknown option: $1"; show_help ;;
    esac
    shift
done

# 验证必要的参数
if [ ! -d "$SPEC_DIR" ]; then
    echo "错误: SPEC路径 '$SPEC_DIR' 不存在"
    exit 1
fi

# 输出当前配置
echo "++ 当前配置:"
echo "++ SPEC路径: $SPEC_DIR"
echo "++ 配置文件: $SPEC_CFG"
echo "++ 执行动作: $SPEC_ACTION"
echo "++ 优化类型: $SPEC_TUNE"
echo "++ 输入类型: $SPEC_INPUT"
echo "++ 测试集合: $SPEC_BENCHES"
echo "++ 测试次数: $SPEC_ITERATIONS"
echo "++ 重新编译: $SPEC_REBUILD"
echo

# 构建SPEC命令
SPEC_COMMEND=""
if ${SPEC_REBUILD}; then
    SPEC_COMMEND="runcpu -c ${SPEC_CFG} -a ${SPEC_ACTION} --rebuild -T ${SPEC_TUNE} -n ${SPEC_ITERATIONS} -i ${SPEC_INPUT} ${SPEC_BENCHES}"
else
    SPEC_COMMEND="runcpu -c ${SPEC_CFG} -a ${SPEC_ACTION} -T ${SPEC_TUNE} -n ${SPEC_ITERATIONS} -i ${SPEC_INPUT} ${SPEC_BENCHES}"
fi

SHRC=${SPEC_DIR}/shrc

cd ${SPEC_DIR}
source ${SHRC}
echo "++ $SPEC_COMMEND"
$SPEC_COMMEND