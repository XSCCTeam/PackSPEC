

# PackSPEC 项目

## 项目简介
PackSPEC 是一个用于自动化打包和管理SPEC CPU基准测试文件的工具，支持SPEC2006和SPEC2017版本。

## 主要功能
- 自动化打包SPEC基准测试二进制文件和运行环境
- 管理SPEC文件配置和构建参数
- 提供便捷的测试脚本生成功能
- 支持多种输入类型(test/train/ref/all)
- 支持多种优化级别(base/peak/all)
- 支持配置绑核测试
- 自动生成测试报告和日志文件
- 支持自定义测试迭代次数
- 支持生成完整的测试报告
- 提供详细的日志记录功能

## 枚举类说明
- `SPECName`: 指定SPEC版本(spec2006/spec2017)
- `TuneType`: 优化级别(base/peak/all)
- `InputType`: 输入类型(test/train/ref/all)
- `SPECSubBench`: 基准测试子集(all/int/fp)
- `ActionType`: 操作类型(build/run)

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
- 指定测试核心编号: 通过`test_core_num`参数设置
- 生成完整测试报告: 自动记录测试日志和结果
- 支持多种优化级别: base(基础优化)和peak(峰值优化)
- 支持多种输入数据集: test(测试)、train(训练)和ref(参考)

## 示例

### PackSPEC类初始化参数
```python
PackSPEC(
    spec_name: SPECName,   # SPEC版本(spec2006/spec2017)
    spec_benches: str,     # 基准测试子集("all"/"int"/"fp")
    tune_type: TuneType,   # 优化级别(base/peak/all)
    input_type: InputType,  # 输入类型(test/train/ref/all)
    iterations: int = 3,    # 测试迭代次数(默认3)
    test_core_num: int = 4, # 测试核心数(默认4)
    rebuild: bool = True    # 是否重新构建(默认True)
)
```

参数说明:
- `spec_name`: 指定SPEC版本(spec2006或spec2017)
- `spec_benches`: 基准测试子集，可以是"all"(全部)、"int"(整数)或"fp"(浮点)，也可以是具体基准测试名称
- `tune_type`: 优化级别，base(基础优化)、peak(峰值优化)或all(两者)
- `input_type`: 输入数据集类型，test(测试)、train(训练)、ref(参考)或all(全部)
- `iterations`: 测试运行迭代次数，默认为3
- `test_core_num`: 测试绑定的CPU核心编号，默认为4
- `rebuild`: 是否重新构建测试环境，默认为True

### 主要方法
- `analyze_spec_config(spec_cfg: str) -> str`: 分析SPEC配置文件获取构建标签
- `run_setup_spec(spec_cfg: str, tune_type: TuneType, input_type: InputType, rebuild: bool = True) -> str`: 设置并编译SPEC环境
- `get_bench_path(label: str, action_type: ActionType, tune_type: TuneType, input_type: InputType) -> list`: 获取基准测试路径
- `copy_binarys(label: str, tune_type: TuneType, input_type: InputType, dest_binary_dir: str = "") -> str`: 复制二进制文件
- `copy_benches(label: str, tune_type: TuneType, input_type: InputType, with_build: bool = False, dest_bench_dir: str = "") -> list`: 复制完整测试环境
- `pack_binarys_cfg(spec_cfg: str)`: 打包二进制文件及相关配置文件
  - 功能: 根据SPEC配置文件自动分析标签并打包二进制文件，同时复制配置文件和相关日志
  - 参数: 
    - `spec_cfg`: SPEC配置文件名
  - 示例: `packer.pack_binarys_cfg("my_config.cfg")`

- `pack_benches_cfg(spec_cfg: str, with_build=False)`: 打包完整测试环境及相关配置文件
  - 功能: 根据SPEC配置文件自动分析标签并打包完整测试环境，同时复制配置文件和相关日志
  - 参数: 
    - `spec_cfg`: SPEC配置文件名
    - `with_build`: 是否包含构建目录(默认False)
  - 示例: `packer.pack_benches_cfg("my_config.cfg", with_build=True)`

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
    test_core_num=4,
    rebuild=True
)

# 分析SPEC配置文件获取标签
label = packer.analyze_spec_config("my_config.cfg")

# 设置并编译SPEC环境
packer.run_setup_spec("my_config.cfg", TuneType.base, InputType.ref)

# 打包二进制文件
binary_dir = packer.copy_binarys(label, TuneType.base, InputType.ref)

# 打包完整测试环境
bench_dirs = packer.copy_benches(label, TuneType.base, InputType.ref, with_build=True)
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
