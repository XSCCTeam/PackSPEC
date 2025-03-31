#!/bin/bash

# 默认值设置
SPEC_PATH=/home/wll/SPECcpu2017
SPEC_CFG=llvm19.cfg
SPEC_TUNE=base
SPEC_INPUT=test
SPEC_TEST="intspeed fpspeed"
SPEC_REBUILD=true

# 显示帮助信息
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -p PATH    设置SPEC路径 (默认: /home/wll/SPECcpu2017)"
    echo "  -c CFG     设置配置文件 (默认: llvm19.cfg)"
    echo "  -t TUNE    设置优化类型 (默认: base)"
    echo "  -i INPUT   设置输入类型 (默认: test)"
    echo "  -s TEST    设置测试集合 (默认: \"intspeed fpspeed\")"
    echo "  -r         禁用重新编译 (默认: 启用)"
    echo "  -h         显示此帮助信息"
    exit 1
}

# 处理命令行参数
while getopts "p:c:t:i:s:rh" opt; do
    case $opt in
        p) SPEC_PATH="$OPTARG" ;;
        c) SPEC_CFG="$OPTARG" ;;
        t) SPEC_TUNE="$OPTARG" ;;
        i) SPEC_INPUT="$OPTARG" ;;
        s) SPEC_TEST="$OPTARG" ;;
        r) SPEC_REBUILD=false ;;
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
echo "当前配置:"
echo "SPEC路径: $SPEC_PATH"
echo "配置文件: $SPEC_CFG"
echo "优化类型: $SPEC_TUNE"
echo "输入类型: $SPEC_INPUT"
echo "测试集合: $SPEC_TEST"
echo "重新编译: $SPEC_REBUILD"
echo

# 构建SPEC命令
SPEC_COMMEND=""
if ${SPEC_REBUILD}; then
    SPEC_COMMEND="runcpu -c ${SPEC_CFG} -a setup --rebuild --thread 1 -T ${SPEC_TUNE} -n 1 -i ${SPEC_INPUT} ${SPEC_TEST}"
else
    SPEC_COMMEND="runcpu -c ${SPEC_CFG} -a setup --thread 1 -T ${SPEC_TUNE} -n 1 -i ${SPEC_INPUT} ${SPEC_TEST}"
fi

SHRC=${SPEC_PATH}/shrc

cd ${SPEC_PATH}
source ${SHRC}
echo "++ $SPEC_COMMEND"
# $SPEC_COMMEND