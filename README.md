

# PackSPEC 项目

## 项目简介
PackSPEC 是一个用于自动化打包和管理SPEC CPU基准测试文件的工具，支持SPEC2006和SPEC2017版本。

## 主要功能
- 自动化打包SPEC基准测试二进制文件和运行环境
- 管理SPEC文件配置和构建参数
- 提供便捷的测试脚本生成功能
- 支持多种输入类型(test/train/ref)
- 支持多种优化级别(base/peak)
- 支持配置绑核测试
- 自动生成测试报告和日志文件

## 安装步骤
1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置项目:
将 `config.py.example` 复制为 `config.py` 并编辑配置文件:
```bash
cp config.py.example config.py
# 然后编辑 config.py 文件配置您的 SPEC 路径等信息
```

## 使用说明

### 基本用法
1. 配置config.py中的SPEC路径和其他参数
2. 运行主程序:
```bash
python pack_spec.py
```

### 高级功能
- 支持自定义测试迭代次数
- 支持指定测试核心数
- 支持生成完整的测试报告

## 示例
```python
from pack_spec import *

# 创建SPEC2006整数基准测试打包实例
packer = PackSPEC(
    spec_bench=SPECBench.spec2006int,
    action_type=ActionType.run,
    tune_type=TuneType.base,
    input_type=InputType.ref,
    iterations=3,
    test_core_num=4
)
# SPEC config 中的 ext
label = "llvm19-m64"

# 打包二进制文件
packer.pack_binarys("llvm19-m64")

# 打包完整测试环境
packer.pack_benches("llvm19-m64")
```
