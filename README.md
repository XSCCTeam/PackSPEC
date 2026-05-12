# PackSPEC 项目

## 项目简介

PackSPEC 是一个用于自动化打包和管理 SPEC CPU 基准测试文件的工具，支持 SPEC2006 和 SPEC2017 版本。该工具能够自动化完成 SPEC 基准测试的编译、打包和测试脚本生成工作，极大简化了 SPEC 测试环境的部署流程。

### 主要特性

- 支持 SPEC CPU 2006 (v1.2.0 和 v1.0.1) 和 SPEC CPU 2017
- 自动化打包二进制文件和运行环境
- 支持多种优化级别 (base/peak) 和输入类型 (test/train/ref)
- 支持速度模式 (speed) 和吞吐模式 (rate)
- 自动生成测试脚本和分数计算脚本
- 支持 Profile 生成模式 (PGO)
- 支持钉钉机器人消息通知
- 完善的类型注解和错误处理

## 项目结构

```
pack_spec/
├── src/pack_spec/           # 核心源代码目录
│   ├── __init__.py          # 包初始化文件，导出公共 API
│   ├── pack_spec.py         # 主模块，PackSPEC 类定义
│   ├── spec_driver.py       # SPEC 驱动基类
│   ├── spec_2006_driver.py  # SPEC2006 驱动实现
│   ├── spec_2017_driver.py  # SPEC2017 驱动实现
│   ├── pack_config.py       # 配置模块，枚举和异常定义
│   └── pack_utils.py        # 工具类模块
├── scripts/                  # 辅助脚本目录
│   ├── setup-spec06.sh      # SPEC2006 安装脚本
│   ├── setup-spec17.sh      # SPEC2017 安装脚本
│   ├── cal_score.py         # 分数计算脚本
│   ├── send_md_message.py   # 钉钉消息发送脚本
│   └── ...
├── tests/                    # 测试用例目录
├── config.py                 # 用户配置文件
├── main.py.example           # 主程序示例
├── .env.example              # 环境变量示例
├── pyproject.toml            # 项目配置文件
└── README.md                 # 项目说明文档
```

## 核心模块说明

### pack_spec.py - 主模块

PackSPEC 核心类，负责协调 SPEC 基准测试的编译、打包和测试脚本生成。支持从配置文件或配置字典初始化，提供 `setup_spec()`、`pack_binaries()`、`pack_benches()` 等主要方法。

### spec_driver.py - 驱动基类

定义了 SPEC 基准测试驱动的通用接口，包括配置解析、编译执行、路径获取等功能。SPEC2006Driver 和 SPEC2017Driver 继承自该基类。

**主要方法：**
- `analyze_spec_config()`: 分析 SPEC 配置文件，提取标签信息
- `run_setup_spec()`: 运行 SPEC setup 脚本进行编译
- `execute_specinvoke()`: 执行 specinvoke 生成运行脚本
- `get_spec_info()`: 获取 SPEC 版本信息

### spec_2006_driver.py - SPEC2006 驱动

实现 SPEC2006 基准测试的具体操作，包含 29 个基准测试（12 个整数测试 + 17 个浮点测试）的配置和管理。

**基准测试列表：**
- 整数测试 (INT): 400.perlbench, 401.bzip2, 403.gcc, 429.mcf, 445.gobmk, 456.hmmer, 458.sjeng, 462.libquantum, 464.h264ref, 471.omnetpp, 473.astar, 483.xalancbmk
- 浮点测试 (FP): 410.bwaves, 416.gamess, 433.milc, 434.zeusmp, 435.gromacs, 436.cactusADM, 437.leslie3d, 444.namd, 447.dealII, 450.soplex, 453.povray, 454.calculix, 459.GemsFDTD, 465.tonto, 470.lbm, 481.wrf, 482.sphinx3

### spec_2017_driver.py - SPEC2017 驱动

实现 SPEC2017 基准测试的具体操作，包含 20 个基准测试（10 个整数测试 + 10 个浮点测试）的配置和管理。

**基准测试列表：**
- 整数测试 (INT): 600.perlbench_s, 602.gcc_s, 605.mcf_s, 620.omnetpp_s, 623.xalancbmk_s, 625.x264_s, 631.deepsjeng_s, 641.leela_s, 648.exchange2_s, 657.xz_s
- 浮点测试 (FP): 603.bwaves_s, 607.cactuBSSN_s, 619.lbm_s, 621.wrf_s, 627.cam4_s, 628.pop2_s, 638.imagick_s, 644.nab_s, 649.fotonik3d_s, 654.roms_s

### pack_config.py - 配置模块

定义全局配置常量、枚举类型和异常类：

**枚举类型：**
- `ActionType`: 操作类型 (build/run)
- `TuneType`: 优化级别 (base/peak/all)
- `InputType`: 输入类型 (test/train/ref/all)
- `SPECName`: SPEC 版本 (spec2006/spec2006v1p01/spec2017)
- `SPECMode`: 运行模式 (speed/rate)
- `PACKMode`: 打包模式 (bin/run/buildrun)

**异常类：**
- `PackSPECError`: 基础异常类
- `ConfigError`: 配置相关异常
- `FileOperationError`: 文件操作异常
- `CommandExecutionError`: 命令执行异常
- `BenchmarkError`: 基准测试异常

### pack_utils.py - 工具模块

提供文件操作、脚本生成、命令执行等辅助功能：

**主要功能：**
- JSON 配置文件读写（支持枚举类型序列化/反序列化）
- 文件复制和目录创建
- 测试脚本生成
- 分数计算脚本生成
- 钉钉消息通知脚本生成
- Profile 文件收集脚本生成

## 安装步骤

### 1. 安装依赖

```bash
pip install loguru
```

或使用 pip 安装项目：

```bash
pip install -e .
```

### 2. 配置环境变量

将 `.env.example` 复制为 `.env` 并编辑：

```bash
cp .env.example .env
# 编辑 .env 文件，填写实际路径
```

`.env` 文件支持注释（以 `#` 开头），程序启动时会自动加载。如果 `.env` 文件不存在，程序会使用系统环境变量。

**必需的环境变量：**
- `SPEC2006_PATH`: SPEC2006 安装目录路径
- `SPEC2017_PATH`: SPEC2017 安装目录路径

**可选的环境变量：**
- `DEFAULT_LLVM_PATH`: LLVM 安装路径（用于 Profile 生成）
- `BOSC_API_KEY`: 钉钉机器人 API 密钥（消息通知功能）
- `BOSC_AT_USER`: 钉钉通知 @ 的用户手机号
- `QEMU_PATH`: QEMU 安装路径（QEMU 验证模式）
- `QEMU_CMD`: QEMU 命令（QEMU 验证模式）

### 3. 配置项目

将 `main.py.example` 复制为 `main.py`：

```bash
cp main.py.example main.py
```

## 使用说明

### 基本用法

```python
from src.pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode

# 配置打包参数
config = {
    # 任务配置
    "task": {
        "pack_name": "my_test",
        "setup_spec": False,
        "pack_binaries": False,
        "pack_benches": False,
        "pack_builds": False,
    },
    # SPEC基准测试相关配置
    "spec_config": {
        "spec_cfg_path": "/path/to/spec/config.cfg",
        "spec_name": SPECName.spec2017,
        "tune_type": TuneType.base,
        "input_type": InputType.ref,
        "spec_mode": SPECMode.speed,
        "spec_benches": "all",
        "iterations": 3,
        "rebuild": False,
    },
    # PackSPEC打包相关配置
    "pack_config": {
        "test_core_num": 4,
        "test_clock_rate": 1.0,
        "profile_gen": False,
        "auto_mode": False,
    },
    # 消息发送相关配置
    "msg_config": {
        "enable_dingtalk_message": False,
        "log_language": "zh",
    },
}

# 创建打包实例
packer = PackSPEC(config)

# 根据配置自动执行相应操作
packer.run()
```

### 从配置文件加载

```python
from src.pack_spec import PackSPEC

# 从配置文件路径初始化
packer = PackSPEC("/path/to/pack_config.json")
packer.run()
```

### 配置参数说明

#### task 配置项

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `pack_name` | str | 打包任务名称 | 必填 |
| `setup_spec` | bool | 是否执行 SPEC 编译 | False |
| `pack_binaries` | bool | 是否打包二进制文件 | False |
| `pack_benches` | bool | 是否打包完整测试环境 | False |
| `pack_builds` | bool | 是否打包 build 和 run 目录到一个 build 目录 | False |
| `run_mode` | RunMode | 运行模式（pack/direct） | pack |

#### spec_config 配置项

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `spec_cfg_path` | str | SPEC 配置文件路径 | 必填 |
| `spec_name` | SPECName | SPEC 版本 | 必填 |
| `tune_type` | TuneType | 优化级别 | 必填 |
| `input_type` | InputType | 输入数据集类型 | 必填 |
| `spec_mode` | SPECMode | 运行模式 | 必填 |
| `spec_benches` | str | 基准测试选择 | 必填 |
| `iterations` | int | 测试迭代次数 | 3 |
| `rebuild` | bool | 是否重新构建 | False |

**注意：** 为保护源配置文件不被修改，setup 操作前会自动将 cfg 文件复制到 `generated_files/{pack_name}/cfg/` 目录，然后使用复制后的文件进行 setup 操作。

#### pack_config 配置项

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `test_core_num` | int | 绑定的 CPU 核心编号 | -1 (不绑定) |
| `test_clock_rate` | float | CPU 主频 (GHz)，用于算分 | 1.0 |
| `profile_gen` | bool | Profile 生成模式 | False |
| `auto_mode` | bool | 自动模式，自动覆盖已存在目录，并生成不带日期前缀的目录名（非自动模式下会询问用户是否覆盖，目录名带日期前缀） | False |
| `verify_mode` | bool | QEMU 验证模式 | False |
| `qemu_verify_parallel_jobs` | int | QEMU 验证并行任务数，0 表示使用 CPU 核心数-2 | 0 |
| `minimal_mode` | bool | 极简模式 | False |
| `allow_basepeak` | bool | 允许 basepeak 配置 | False |
| `report_format` | str | 报告格式（json/markdown） | json |

#### msg_config 配置项

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enable_dingtalk_message` | bool | 是否开启钉钉消息发送 | False |
| `log_language` | str | 日志输出语言（zh/en） | zh |

### 日志语言设置

PackSPEC 支持中英文日志输出，通过 `msg_config.log_language` 参数配置。

**可选值：**

| 值 | 说明 |
|----|------|
| `"zh"` 或 `"chinese"` 或 `"cn"` | 中文输出 |
| `"en"` 或 `"english"` | 英文输出 |

**使用示例：**

```python
config = {
    "task": {...},
    "spec_config": {...},
    "msg_config": {
        "enable_dingtalk_message": False,
        "log_language": "zh",  # 中文输出
    },
}
```

**注意事项：**
- 默认使用中文输出
- 所有日志消息（info、warning、error、debug）都会根据语言设置输出对应语言
- 错误消息和异常信息也会使用配置的语言

### spec_benches 参数格式

`spec_benches` 参数支持以下格式：

| 格式 | 说明 | 示例 |
|------|------|------|
| `"all"` | 选择所有基准测试 | `"all"` |
| `"int"` 或 `"intspeed"` | 选择所有整数基准测试 | `"int"` |
| `"fp"` 或 `"fpspeed"` | 选择所有浮点基准测试 | `"fp"` |
| `"600 602 603"` | 选择指定编号的基准测试（空格分隔） | `"600 602"` |
| 组合使用 | 可以组合多个选择条件 | `"int 603 607"` |

### run() 方法

PackSPEC 采用配置驱动的设计模式，用户只需要配置 config 并调用 `run()` 方法，`run()` 会根据配置自动调用相应的内部方法。

**使用示例：**

```python
from src.pack_spec import PackSPEC

config = {
    "task": {
        "pack_name": "my_test",
        "setup_spec": False,
        "pack_binaries": False,
        "pack_benches": False,
        "pack_builds": False,
    },
    "spec_config": {...},
    "pack_config": {...},
}

packer = PackSPEC(config)
packer.run()  # 根据配置自动执行相应操作
```

**配置项与内部方法的对应关系：**

| 配置项 | 配置路径 | 调用的内部方法 | 说明 |
|--------|----------|----------------|------|
| `setup_spec` | task | `setup_spec()` | 执行 SPEC 编译和环境准备 |
| `pack_binaries` | task | `pack_binaries()` | 打包二进制文件 |
| `pack_benches` | task | `pack_benches_cfg()` | 打包完整测试环境 |
| `pack_builds` | task | `pack_benches_cfg(with_build=True)` | 打包 build 和 run 目录到一个 build 目录 |
| `run_mode` | task | `run_spec()` | 当设置为 `RunMode.direct` 时直接运行 SPEC 测试 |
| `verify_mode` | pack_config | `pack_qemu_verify()` | 生成 QEMU 验证脚本 |

**run_mode 配置说明：**

| run_mode 值 | 行为 |
|-------------|------|
| `RunMode.pack`（默认） | 根据 task 配置执行打包操作（setup_spec、pack_binaries、pack_benches、pack_builds） |
| `RunMode.direct` | 直接运行 SPEC 测试，调用 `run_spec()` 方法，跳过打包操作 |

**内部方法列表：**

以下方法由 `run()` 根据配置自动调用，通常不需要用户直接调用：

| 方法 | 说明 |
|------|------|
| `setup_spec()` | 执行 SPEC 编译和环境准备 |
| `pack_binaries()` | 打包二进制文件 |
| `pack_binaries_cfg()` | 打包二进制文件（使用配置文件路径） |
| `pack_benches(with_build=False)` | 打包完整测试环境 |
| `pack_benches_cfg(with_build=False)` | 打包完整测试环境（使用配置文件路径） |
| `run_spec(output_dir=None, generate_report=True)` | 直接运行 SPEC 测试（无需打包） |
| `pack_qemu_verify(output_dir=None)` | 生成 QEMU 验证脚本 |

## 输出目录结构

打包完成后，输出目录结构如下：

**普通模式（auto_mode=False）：**

生成目录、配置文件和打包子目录都带日期前缀，避免不同日期的结果互相覆盖：

```
generated_files/
└── {date}_{pack_name}/
    ├── {date}_{pack_name}.json          # 配置文件
    ├── log/
    │   └── PackSpec_{time}.log          # 日志文件
    ├── cfg/
    │   └── {config}.cfg                 # 复制的配置文件
    ├── bin/
    │   └── {date}_spec2017_bin_{pack_name}.{tune_type}_{input_type}_{spec_mode}/
    │       ├── 600.perlbench_s/
    │       │   └── perlbench_s
    │       └── ...
    ├── run/
    │   └── {date}_spec2017_run_{pack_name}.{tune_type}_{input_type}_{spec_mode}/
    │       ├── 600.perlbench_s/
    │       │   ├── perlbench_s_base.{label}
    │       │   ├── run_ref.sh
    │       │   ├── test_ref.sh
    │       │   ├── specdiff_ref.sh
    │       │   └── ...
    │       ├── test_ref_all.sh
    │       ├── specdiff_ref_all.sh
    │       └── ...
    └── build/
        └── {date}_spec2017_build_{pack_name}.{tune_type}_{input_type}_{spec_mode}/
            ├── 600.perlbench_s/
            │   ├── perlbench_s_base.{label}
            │   ├── run_ref.sh
            │   ├── test_ref.sh
            │   ├── specdiff_ref.sh
            │   └── ...
            ├── test_ref_all.sh
            ├── specdiff_ref_all.sh
            └── ...
```

**自动模式（auto_mode=True）：**

目录名和配置文件名都不包含日期前缀，便于自动化脚本预测路径：

```
generated_files/
└── {pack_name}/
    ├── {pack_name}.json                 # 配置文件
    ├── log/
    │   └── PackSpec_{time}.log          # 日志文件
    ├── cfg/
    │   └── {config}.cfg                 # 复制的配置文件
    ├── bin/
    │   └── ...
    ├── run/
    │   └── ...
    └── build/
        └── ...
```

## 高级功能

### 直接运行模式

PackSPEC 支持直接运行模式，无需打包即可直接驱动 SPEC 测试。该模式适用于本地测试场景，可以简化测试流程。

**使用方法：**

```python
from src.pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode, RunMode

config = {
    # 任务配置
    "task": {
        "pack_name": "my_test",
        "setup_spec": False,
        "pack_binaries": False,
        "pack_benches": False,
        "pack_builds": False,
    },
    # SPEC基准测试相关配置
    "spec_config": {
        "spec_cfg_path": "/path/to/spec/config.cfg",
        "spec_name": SPECName.spec2017,
        "tune_type": TuneType.base,
        "input_type": InputType.ref,
        "spec_mode": SPECMode.speed,
        "spec_benches": "all",
        "iterations": 3,
    },
    # PackSPEC打包相关配置
    "pack_config": {
        "run_mode": RunMode.direct,  # 设置为直接运行模式
        "report_format": "json",     # 报告格式：json 或 markdown
    },
}

packer = PackSPEC(config)

# 直接运行 SPEC 测试
result = packer.run_spec()

# 查看测试结果
print(f"INT 分数: {result['results']['int_score']}")
print(f"FP 分数: {result['results']['fp_score']}")
print(f"报告路径: {result['report_path']}")
```

**返回结果说明：**

`run_spec()` 方法返回一个字典，包含以下键：

| 键 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否成功完成 |
| `output_dir` | str | 结果输出目录 |
| `log_file` | str | 日志文件路径 |
| `results` | Dict | 解析后的测试结果 |
| `report_path` | str | 报告文件路径 |

**测试报告格式：**

测试报告包含以下信息：
- 测试配置信息（SPEC 版本、优化级别、输入类型等）
- 各基准测试的运行时间和分数
- 整数测试 (INT) 综合分数
- 浮点测试 (FP) 综合分数
- 测试时间戳

**注意事项：**
- 直接运行模式需要 SPEC 已正确安装并配置环境变量
- 测试过程中会实时输出日志
- 支持 Ctrl+C 中断测试
- 测试结果保存在 `spec_results/` 目录下

### QEMU 验证模式

PackSPEC 支持 QEMU 验证模式，用于验证编译出的 SPEC CPU 2006/2017 二进制文件是否正确。该模式通过 QEMU 模拟器运行测试，不统计运行时间，只保留程序输出。

**配置环境变量：**

在 `.env` 文件中配置 QEMU 路径：

```bash
# QEMU Configs
QEMU_PATH=/path/to/qemu
QEMU_CMD=qemu-aarch64
```

**使用方法：**

```python
from src.pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode

config = {
    # 任务配置
    "task": {
        "pack_name": "verify_test",
        "setup_spec": False,
        "pack_binaries": False,
        "pack_benches": False,
        "pack_builds": False,
    },
    # SPEC基准测试相关配置
    "spec_config": {
        "spec_cfg_path": "/path/to/spec/config.cfg",
        "spec_name": SPECName.spec2017,
        "tune_type": TuneType.base,
        "input_type": InputType.test,    # 建议使用 test 输入进行快速验证
        "spec_mode": SPECMode.speed,
        "spec_benches": "all",
    },
    # PackSPEC打包相关配置
    "pack_config": {
        "verify_mode": True,             # 开启验证模式
    },
}

packer = PackSPEC(config)

# 先编译二进制文件
packer.setup_spec()

# 生成 QEMU 验证脚本
result = packer.pack_qemu_verify()

print(f"输出目录: {result['output_dir']}")
print(f"生成脚本数量: {len(result['scripts'])}")
```

**配置参数说明：**

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `verify_mode` | bool | 是否开启验证模式 | False |

**环境变量：**

| 变量名 | 说明 |
|--------|------|
| `QEMU_PATH` | QEMU 安装目录路径（在 .env 中配置） |
| `QEMU_CMD` | QEMU 命令（在 .env 中配置） |

**QEMU 目录结构要求：**

```
$QEMU_PATH/
├── bin/
│   ├── qemu-aarch64      # ARM64 模拟器
│   ├── qemu-riscv64      # RISC-V 64 模拟器
│   └── ...
└── sysroot/              # 目标架构的系统库
    ├── lib/
    └── ...
```

**生成的脚本：**

- `verify_{input_type}.sh`: 单个基准测试的验证脚本
- `verify_{input_type}_all.sh`: 批量验证所有基准测试的脚本

**输出目录结构：**

```
output_dir/
├── 600.perlbench_s/
│   ├── perlbench_s_base.{label}
│   ├── verify_test.sh
│   └── ...
├── 602.gcc_s/
│   └── ...
├── logs/
│   ├── 600.perlbench_s_verify.log
│   └── verify_all.log
├── verify_test_all.sh
└── {config}.cfg
```

**运行验证：**

```bash
# 验证单个基准测试
cd output_dir/600.perlbench_s
./verify_test.sh

# 批量验证所有基准测试
cd output_dir
./verify_test_all.sh
```

**注意事项：**
- 需要先调用 `setup_spec()` 编译二进制文件
- QEMU 路径通过环境变量 `QEMU_PATH` 配置
- QEMU 目录必须包含对应架构的模拟器和 sysroot
- 验证模式不统计运行时间，仅验证程序能否正确执行
- 建议使用 `test` 输入类型进行快速验证

### Profile 生成模式

设置 `profile_gen: True` 可启用 Profile 生成模式，该模式下：

- 迭代次数自动设为 1
- 生成 `profile_gen_{input_type}.sh` 脚本
- 自动生成 `merge_profile.sh` 用于合并 Profile 文件
- 需要配置 `DEFAULT_LLVM_PATH` 环境变量

```python
config = {
    "task": {...},
    "spec_config": {...},
    "pack_config": {
        "profile_gen": True,
    },
}
```

### 钉钉消息通知

配置 `BOSC_API_KEY` 和 `BOSC_AT_USER` 环境变量后，测试完成后会自动发送钉钉消息通知，包含：

- 测试完成通知
- 测试结果和分数信息
- Markdown 格式的详细报告

**安全说明：** API 密钥通过环境变量传递，不会硬编码在生成的脚本中。

### 绑核测试

通过 `test_core_num` 参数指定测试运行的 CPU 核心：

```python
config = {
    "task": {...},
    "spec_config": {...},
    "pack_config": {
        "test_core_num": 4,  # 绑定到 CPU 核心 4
    },
}
```

设置为 `-1` 表示不绑定核心。

## 枚举类说明

| 枚举类 | 说明 | 可选值 |
|--------|------|--------|
| `SPECName` | SPEC 版本 | `spec2006`, `spec2006v1p01`, `spec2017` |
| `TuneType` | 优化级别 | `base` (基础优化), `peak` (峰值优化), `all` |
| `InputType` | 输入类型 | `test` (最小), `train` (中等), `ref` (最大), `all` |
| `SPECMode` | 运行模式 | `speed` (速度测试), `rate` (吞吐测试) |
| `ActionType` | 操作类型 | `build` (构建), `run` (运行) |
| `PACKMode` | 打包模式 | `bin` (仅二进制), `run` (运行环境), `buildrun` (完整环境) |
| `RunMode` | 运行模式 | `pack` (打包模式), `direct` (直接运行模式) |

## 开发指南

### 代码风格

- 使用 Python 3.8+ 语法
- 代码注释使用中文
- 遵循 PEP 8 编码规范
- 使用显式导入，避免 `import *`
- 添加完整的类型注解

### 运行单元测试

项目使用 pytest 框架进行单元测试，测试覆盖率要求不低于 80%。

**安装测试依赖：**

```bash
pip install pytest pytest-cov
```

**运行所有测试：**

```bash
pytest
```

**运行测试并生成覆盖率报告：**

```bash
# 终端输出覆盖率报告
pytest --cov=src/pack_spec --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src/pack_spec --cov-report=html
```

**运行指定测试文件：**

```bash
# 测试配置模块
pytest tests/test_pack_config.py

# 测试工具模块
pytest tests/test_pack_utils.py

# 测试主模块
pytest tests/test_pack_spec.py

# 测试驱动模块
pytest tests/test_spec_driver.py
```

**测试目录结构：**

```
tests/
├── conftest.py           # 测试配置和共享 fixtures
├── test_pack_config.py   # 配置模块测试（枚举、异常、默认值等）
├── test_pack_utils.py    # 工具模块测试（文件操作、脚本生成等）
├── test_pack_spec.py     # 主模块测试（PackSPEC 类初始化和运行）
└── test_spec_driver.py   # 驱动模块测试（SPEC 驱动基类）
```

**覆盖率配置：**

项目在 `pyproject.toml` 中配置了覆盖率要求：

```toml
[tool.coverage.report]
fail_under = 80  # 覆盖率不低于 80%
```

**注意事项：**

- 测试用例独立运行，不依赖 SPEC 安装环境
- 使用 mock 模拟外部依赖（文件系统、命令执行等）
- 测试覆盖率排除了需要 SPEC 环境的模块（spec_driver.py、spec_2006_driver.py、spec_2017_driver.py、pack_spec.py 中的 SPEC 交互方法）

### 运行 SPEC 集成测试

```bash
cd tests/spec2006
bash run_test.sh
```

### 模块导入

推荐使用以下方式导入：

```python
# 导入主要类和枚举
from src.pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode, RunMode

# 导入异常类
from src.pack_spec import PackSPECError, ConfigError, FileOperationError

# 导入工具函数
from src.pack_spec import load_pack_spec_cfg, save_pack_spec_cfg, parse_spec_results, generate_json_report, generate_markdown_report
```

## 注意事项

1. **环境变量配置**：确保 SPEC 安装路径正确配置
2. **首次使用**：建议使用 `test` 输入类型进行快速验证
3. **重新构建**：`rebuild: True` 会重新编译所有基准测试，耗时较长
4. **Profile 生成**：需要配置 LLVM 工具链路径
5. **安全性**：敏感信息（API 密钥）通过环境变量传递，不要硬编码

## 更新日志

### v0.3.0

**新功能：**
- 新增 QEMU 验证模式，支持通过 QEMU 模拟器验证编译出的二进制文件
- 新增 `pack_qemu_verify()` 方法，生成 QEMU 验证脚本
- 新增 `generate_qemu_verify_script()` 函数，生成单个基准测试验证脚本
- 新增 `generate_qemu_verify_all_script()` 函数，生成批量验证脚本
- 支持自动检测 QEMU 模拟器类型（aarch64, riscv64, arm, mips 等）
- 验证模式不统计运行时间，仅验证程序正确性并保留输出
- 新增极简模式，生成 POSIX 兼容脚本，适用于功能简单的嵌入式系统

**配置参数：**
- 新增 `QEMU_PATH` 环境变量，在 .env 中配置 QEMU 安装目录
- 新增 `QEMU_CMD` 环境变量，在 .env 中配置 QEMU 模拟器命令（如 qemu-aarch64, qemu-riscv64 等）
- 新增 `verify_mode` 配置项，开启验证模式
- 新增 `minimal_mode` 配置项，开启极简模式

### v0.2.0

**新功能：**
- 新增直接运行模式 (`RunMode.direct`)，可直接驱动 SPEC 测试无需打包
- 新增 `run_spec()` 方法，支持直接调用 runspec/runcpu 命令
- 新增测试结果解析功能 (`parse_spec_results()`)
- 新增测试报告生成功能 (`generate_json_report()`, `generate_markdown_report()`)
- 支持生成 JSON 和 Markdown 格式的测试报告

**改进：**
- 完善了 SPECDriver 基类的环境检查功能
- 优化了命令执行和日志输出

### v0.1.0

**新功能：**
- 支持 SPEC2006 和 SPEC2017 基准测试打包
- 支持多种优化级别和输入类型
- 支持自动生成测试脚本
- 支持 Profile 生成模式
- 支持钉钉消息通知

**优化改进：**
- 改进模块导入方式，使用显式导入避免命名空间污染
- 添加完整的类型注解支持
- 统一错误处理，使用自定义异常替代 assert
- 优化安全性，API 密钥通过环境变量传递
- 提取公共函数 `is_numeric()` 减少代码重复
- 完善 `__init__.py` 导出公共 API
- 更新所有模块的文档字符串

## 许可证

本项目仅供内部使用。

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 联系方式

如有问题或建议，请联系项目维护者。
