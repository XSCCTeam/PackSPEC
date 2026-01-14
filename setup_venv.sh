#!/bin/bash

# 使用uv创建虚拟环境并安装依赖的脚本

set -e

echo "开始设置Python虚拟环境..."

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装。请先安装uv: pip install uv"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
uv venv venv

echo "安装依赖..."

# 激活虚拟环境并使用uv安装依赖和开发依赖（自动识别pyproject.toml）
source venv/bin/activate && uv pip install -e .[dev]

echo ""
echo "环境设置完成！"
echo "使用以下命令激活虚拟环境:"
echo "source venv/bin/activate"
echo ""
