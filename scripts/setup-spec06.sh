#!/bin/bash

set -e

# 默认值设置
SPEC_PATH=/SPECcpu2006
SPEC_CFG=llvm19.cfg
SPEC_ACTION=setup
SPEC_TUNE=base
SPEC_INPUT=test
SPEC_TEST="all"
SPEC_RUN_NUM=3
SPEC_REBUILD=false

# 显示帮助信息
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -p PATH    设置SPEC路径 (默认: /SPECcpu2006)"
    echo "  -c CFG     设置配置文件 (默认: llvm19.cfg)"
    echo "  -a ACTION  设置动作 (默认: setup)"
    echo "  -t TUNE    设置优化类型 (默认: base)"
    echo "  -i INPUT   设置输入类型 (默认: test)"
    echo "  -s TEST    设置测试集合 (默认: \"all\")"
    echo "  -n RUN_NUM 设置测试次数 (默认: 3)"
    echo "  -r         禁用重新编译 (默认: 启用)"
    echo "  -h         显示此帮助信息"
    exit 1
}

# 处理命令行参数
while getopts "p:c:a:t:i:s:n:rh" opt; do
    case $opt in
        p) SPEC_PATH="$OPTARG" ;;
        c) SPEC_CFG="$OPTARG" ;;
        a) SPEC_ACTION="$OPTARG" ;;
        t) SPEC_TUNE="$OPTARG" ;;
        i) SPEC_INPUT="$OPTARG" ;;
        s) SPEC_TEST=$OPTARG ;;
        n) SPEC_RUN_NUM="$OPTARG" ;;
        r) SPEC_REBUILD=true ;;
        h) show_help ;;
        ?) show_help ;;
    esac
done

# 验证必要的参数
if [ ! -d "$SPEC_PATH" ]; then
    echo "错误: SPEC路径 '$SPEC_PATH' 不存在"
    exit 1
fi

# 输出当前配置
echo "++ 当前配置:"
echo "++ SPEC路径: $SPEC_PATH"
echo "++ 配置文件: $SPEC_CFG"
echo "++ 执行动作: $SPEC_ACTION"
echo "++ 优化类型: $SPEC_TUNE"
echo "++ 输入类型: $SPEC_INPUT"
echo "++ 测试集合: $SPEC_TEST"
echo "++ 测试次数: $SPEC_RUN_NUM"
echo "++ 重新编译: $SPEC_REBUILD"
echo

# 构建SPEC命令
SPEC_COMMEND=""
if ${SPEC_REBUILD}; then
    SPEC_COMMEND="runspec -c ${SPEC_CFG} -a ${SPEC_ACTION} --rebuild -T ${SPEC_TUNE} -n ${SPEC_RUN_NUM} -i ${SPEC_INPUT} ${SPEC_TEST}"
else
    SPEC_COMMEND="runspec -c ${SPEC_CFG} -a ${SPEC_ACTION} -T ${SPEC_TUNE} -n ${SPEC_RUN_NUM} -i ${SPEC_INPUT} ${SPEC_TEST}"
fi

SHRC=${SPEC_PATH}/shrc

cd ${SPEC_PATH}
source ${SHRC}
echo "++ $SPEC_COMMEND"
$SPEC_COMMEND
