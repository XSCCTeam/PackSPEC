#!/bin/bash

# 项目根目录
# 使用BASH_SOURCE确保在source执行时也能正确获取脚本目录
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

# 验证目录是否正确
if [[ ! -f "${SCRIPT_DIR}/reference_files/test_setup_gcc.cfg" ]]; then
    echo "错误: 无法找到配置文件，请确保脚本在正确的目录中执行"
    return 1 2>/dev/null || exit 1
fi

SPEC_TEST_TEST_CFG_PATH="${SCRIPT_DIR}/reference_files/test_setup_gcc.cfg"
SPEC_TEST_2006_INSTALL_PATH="${SCRIPT_DIR}/spec_env/speccpu2006-v1.2"
SPEC_TEST_CFG_PATH="${SPEC_TEST_2006_INSTALL_PATH}/config/test_setup_gcc.cfg"
SPEC_TEST_SETUPLOG_TEMPLATE="${SCRIPT_DIR}/reference_files/test_spec_log.template"
SPEC_TEST_SETUPLOG_PATH="${SCRIPT_DIR}/reference_files/test_spec_log.setuplog"
SPEC_TEST_GENERATED_PATH="${SCRIPT_DIR}/generated_files"


# 确保配置目录存在
mkdir -p "${SPEC_TEST_2006_INSTALL_PATH}/config"

# 从SPEC_TEST_TEST_CFG_PATH复制SPEC_TEST_CFG_PATH
echo "尝试复制配置文件: ${SPEC_TEST_TEST_CFG_PATH} -> ${SPEC_TEST_CFG_PATH}"
if cp "${SPEC_TEST_TEST_CFG_PATH}" "${SPEC_TEST_CFG_PATH}"; then
    echo "已复制配置文件: ${SPEC_TEST_TEST_CFG_PATH} -> ${SPEC_TEST_CFG_PATH}"
else
    echo "警告: 无法复制配置文件 ${SPEC_TEST_TEST_CFG_PATH}"
    echo "这可能是由于系统权限限制导致的"
    echo "请确保您有权限写入目标目录: ${SPEC_TEST_2006_INSTALL_PATH}/config"
    # 不返回错误，继续执行
fi

# 通过SPEC_TEST_SETUPLOG_TEMPLATE生成SPEC_TEST_SETUPLOG_PATH，将{{SPEC_2006_INSTALL_PATH}}替换为SPEC_TEST_2006_INSTALL_PATH   
echo "尝试生成日志文件: ${SPEC_TEST_SETUPLOG_PATH}"
if sed "s|{{SPEC_2006_INSTALL_PATH}}|${SPEC_TEST_2006_INSTALL_PATH}|g" "${SPEC_TEST_SETUPLOG_TEMPLATE}" > "${SPEC_TEST_SETUPLOG_PATH}"; then
    echo "已生成日志文件: ${SPEC_TEST_SETUPLOG_PATH}"
else
    echo "警告: 无法生成日志文件 ${SPEC_TEST_SETUPLOG_PATH}"
    echo "这可能是由于系统权限限制导致的"
    echo "请确保您有权限写入目标目录: ${SCRIPT_DIR}/reference_files"
    # 不返回错误，继续执行
fi

# 导出环境变量
export SPEC_TEST_2006_INSTALL_PATH
export SPEC_TEST_CFG_PATH
export SPEC_TEST_SETUPLOG_PATH
export SPEC_TEST_GENERATED_PATH
export SPEC2006_PATH="${SPEC_TEST_2006_INSTALL_PATH}"
