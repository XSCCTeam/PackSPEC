

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
- 支持自定义测试迭代次数
- 支持生成完整的测试报告
- 提供详细的日志记录功能

## 安装步骤
1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置项目:
将 `config.py.example` 复制为 `config.py` 并编辑配置文件, 将 `main.py.example` 复制为 `main.py`:
```bash
cp config.py.example config.py
cp main.py.example main.py
```

编辑config.py文件配置以下信息:
- `SPEC2006_PATH`: SPEC2006安装目录路径
- `SPEC2017_PATH`: SPEC2017安装目录路径
- `BOSC_API_KEY`: (可选)钉钉机器人API密钥
- `BOSC_AT_USER`: (可选)钉钉通知手机号

## 使用说明

### 基本用法
1. 配置config.py中的SPEC路径和其他参数
2. 运行主程序:
```bash
python main.py
```

### 高级功能
- 自定义测试迭代次数: 通过`iterations`参数设置
- 指定测试核心数: 通过`test_core_num`参数设置
- 生成完整测试报告: 自动记录测试日志和结果
- 支持多种优化级别: base(基础优化)和peak(峰值优化)
- 支持多种输入数据集: test(测试)、train(训练)和ref(参考)

## 示例

### 基本示例
```python
from pack_spec import *

# 创建SPEC2006整数基准测试打包实例
packer = PackSPEC(
    spec_name=SPECName.spec2006,
    spec_benches="int",
    tune_type=TuneType.base,
    input_type=InputType.ref,
    iterations=3,
    test_core_num=4
)

# 分析SPEC配置文件获取标签
label = packer.analyze_spec_config("my_config.cfg")

# 打包二进制文件
packer.pack_binarys(label)

# 打包完整测试环境
packer.pack_benches(label)
```

### 高级示例
```python
# 创建SPEC2017完整基准测试打包实例
packer = PackSPEC(
    spec_name=SPECName.spec2017,
    spec_benches="all",
    tune_type=TuneType.all,
    input_type=InputType.all,
    iterations=5,
    test_core_num=8
)

# 设置并编译SPEC环境
packer.setup_spec("advanced_config.cfg")

# 打包所有内容
label = packer.analyze_spec_config("advanced_config.cfg")
packer.pack_binarys(label)
packer.pack_benches(label)
```
