# PackSPEC 接口定义文档

本文档定义了 PackSPEC 工具的所有公共接口，包括 PackSPEC 主类、SPECDriver 抽象接口、PackUtils 工具接口、模块间交互接口以及配置文件格式。

---

## 1. PackSPEC 公共 API

`PackSPEC` 是工具的核心入口类，负责协调 SPEC 基准测试的编译、打包和测试脚本生成。支持 SPEC2006 和 SPEC2017 两个版本。

### 1.1 `__init__(config)`

初始化 PackSPEC 实例。

| 项目 | 说明 |
|------|------|
| **参数** | `config: str \| dict` — 配置信息，可以是配置文件路径字符串或配置字典 |
| **返回值** | `PackSPEC` 实例 |
| **异常** | `ValueError` — 当 config 参数类型不是 str 或 dict 时抛出 |

**初始化行为：**

- 当 `config` 为 `str` 时：从配置文件路径加载配置（调用 `load_pack_spec_cfg`），使用配置中的 `date` 字段
- 当 `config` 为 `dict` 时：直接使用配置字典初始化，自动创建生成目录并保存配置文件

**使用示例：**

```python
from pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode

# 从字典初始化
config = {
    "task": {"pack_name": "my_test", "setup_spec": False, "pack_binaries": True, "pack_benches": True},
    "spec_config": {"spec_cfg_path": "/path/to/spec.cfg", "spec_name": SPECName.spec2017, ...},
}
packer = PackSPEC(config)

# 从配置文件初始化
packer = PackSPEC("/path/to/pack_spec.cfg")
```

---

### 1.2 `setup_spec()`

执行 SPEC 基准测试的编译和设置。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `None` |
| **异常** | `CommandExecutionError` — 当编译命令执行失败时抛出 |

**行为说明：**

- 将 cfg 文件复制到 `generated_files` 目录（保护源文件不被修改）
- 解析 SPEC 配置文件
- 编译基准测试二进制文件
- 准备运行目录和输入数据
- 内部调用 `spec_driver.run_setup_spec()` 执行实际编译

**使用示例：**

```python
packer = PackSPEC(config)
packer.setup_spec()
```

---

### 1.3 `pack_binaries()`

打包二进制文件。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `list` — 目标目录列表 |
| **异常** | `FileOperationError` — 当没有二进制文件可复制时抛出 |

**行为说明：**

- 根据配置的 `tune_type` 和 `input_type`，复制所有基准测试的二进制文件
- 如果 `tune_type` 或 `input_type` 为 `all`，会自动处理所有组合
- 同时复制配置文件及相关日志到目标目录

**使用示例：**

```python
packer = PackSPEC(config)
packer.pack_binaries()
```

---

### 1.4 `pack_benches(with_build=False, spec_cfg="")`

打包完整测试环境。

| 项目 | 说明 |
|------|------|
| **参数** | `with_build: bool` — 是否包含构建目录，默认 `False` |
| | `spec_cfg: str` — SPEC 配置文件名，为空则不复制配置文件，默认 `""` |
| **返回值** | `list` — 目标目录列表 |
| **异常** | `FileOperationError` — 当复制失败或没有基准测试可复制时抛出 |
| | `CommandExecutionError` — 当生成运行脚本失败时抛出 |

**行为说明：**

- 复制基准测试的运行目录，包括二进制文件、输入数据、配置文件等
- 自动生成 `run_{input_type}.sh` 测试脚本
- 自动生成 `test_{input_type}.sh` 或 `profile_gen_{input_type}.sh` 运行脚本
- 自动生成 `specdiff_{input_type}.sh` 验证脚本
- 如果 `tune_type` 或 `input_type` 为 `all`，会自动处理所有组合

**使用示例：**

```python
packer = PackSPEC(config)
# 不包含构建目录
packer.pack_benches()
# 包含构建目录，并复制配置文件
packer.pack_benches(with_build=True, spec_cfg="/path/to/spec.cfg")
```

---

### 1.5 `pack_qemu_verify(output_dir=None)`

生成 QEMU 验证脚本。

| 项目 | 说明 |
|------|------|
| **参数** | `output_dir: str \| None` — 验证脚本输出目录，默认自动生成 |
| **返回值** | `Dict` — 结果字典，包含以下键： |
| | `success (bool)` — 是否成功生成 |
| | `output_dir (str)` — 输出目录路径 |
| | `scripts (List[str])` — 生成的脚本路径列表 |
| **异常** | `ConfigError` — 当未配置 `QEMU_PATH` 环境变量或未开启 `verify_mode` 时抛出 |
| | `FileOperationError` — 当复制文件失败或运行目录不存在时抛出 |

**前置条件：**

- 需要先调用 `setup_spec()` 编译二进制文件
- 需要先调用 `pack_benches()` 生成运行目录
- 需要在 `.env` 中配置 `QEMU_PATH` 环境变量
- 需要在配置中开启 `verify_mode`

**使用示例：**

```python
config = {
    "task": {"pack_name": "verify_test", ...},
    "spec_config": {"spec_cfg_path": "/path/to/spec.cfg", ...},
    "pack_config": {"verify_mode": True, ...}
}
packer = PackSPEC(config)
packer.setup_spec()
packer.pack_benches()
result = packer.pack_qemu_verify()
print(result["scripts"])
```

---

### 1.6 `run_spec(output_dir=None, generate_report=True)`

直接运行 SPEC 测试。

| 项目 | 说明 |
|------|------|
| **参数** | `output_dir: str \| None` — 结果输出目录，默认自动生成 |
| | `generate_report: bool` — 是否生成测试报告，默认 `True` |
| **返回值** | `Dict` — 结果字典，包含以下键： |
| | `success (bool)` — 是否成功完成 |
| | `output_dir (str)` — 结果输出目录 |
| | `log_file (str)` — 日志文件路径 |
| | `return_code (int)` — 命令返回码 |
| | `error_message (str)` — 错误信息（如果有） |
| | `results (Dict)` — 解析后的测试结果（如果解析成功） |
| | `report_path (str)` — 报告文件路径（如果生成） |
| **异常** | `FileOperationError` — 当 SPEC 环境检查失败时抛出 |
| | `CommandExecutionError` — 当命令执行失败或用户中断时抛出 |

**行为说明：**

- 调用 `runspec`/`runcpu` 命令直接执行 SPEC 基准测试
- 测试过程中实时输出日志
- 支持 Ctrl+C 中断测试
- 测试完成后自动解析结果并生成报告

**使用示例：**

```python
packer = PackSPEC(config)
result = packer.run_spec()
print(f"INT分数: {result['results']['int_score']}")
print(f"FP分数: {result['results']['fp_score']}")
```

---

### 1.7 `run()`

统一入口方法，根据配置自动执行相应操作。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `Dict` — 结果字典，包含以下键： |
| | `success (bool)` — 是否成功完成 |
| | `steps (List[str])` — 执行的步骤名称列表 |
| | `run_spec_result (Dict)` — `run_spec()` 的结果（仅在 direct 模式下） |
| **异常** | 同各子方法可能抛出的异常 |

**行为说明：**

- 当 `run_mode == RunMode.direct` 时：调用 `run_spec()` 直接运行 SPEC 测试
- 当 `run_mode == RunMode.pack`（默认）时，根据 task 配置执行打包操作：
  - `setup_spec == True` → 调用 `setup_spec()`
  - `pack_binaries == True` → 调用 `pack_binaries()`
  - `pack_benches == True` → 调用 `pack_benches_cfg()`
  - `verify_mode == True` → 调用 `pack_qemu_verify()`

**使用示例：**

```python
packer = PackSPEC(config)
result = packer.run()
print(f"执行步骤: {result['steps']}")
```

---

## 2. SPECDriver 抽象接口

`SPECDriver` 是 SPEC CPU 基准测试驱动的基类，定义了 SPEC 基准测试的通用操作接口。`SPEC2006Driver`、`SPEC2006V1P01Driver` 和 `SPEC2017Driver` 继承自该基类。

### 2.1 基类定义的方法

#### `get_spec_info()`

获取 SPEC CPU 的基本信息。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `Dict[str, str]` — 包含 `spec_name`、`spec_version`、`spec_path` 的字典 |
| **异常** | `ValueError` — 当 `spec_name` 不是已知的 SPEC 版本时抛出 |

---

#### `get_spec_log(spec_log_file)`

从 SPEC 日志文件中获取实际的日志文件路径。

| 项目 | 说明 |
|------|------|
| **参数** | `spec_log_file: str` — SPEC 日志文件路径 |
| **返回值** | `str` — 找到的日志文件绝对路径，未找到则返回空字符串 |
| **异常** | 无 |

---

#### `analyze_spec_config()`

分析 SPEC 配置文件，提取标签信息。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `str` — 从配置文件中提取的标签字符串 |
| **异常** | `ConfigError` — 当配置文件不存在时抛出 |
| | `PackSPECError` — 当用户取消 basepeak 确认时抛出 |
| | `AssertionError` — 当无法从配置文件中提取标签时抛出 |

**行为说明：**

- SPEC2006 使用 `ext` 字段提取标签
- SPEC2017 使用 `label` 字段提取标签
- 如果配置文件中设置了 `basepeak=yes`，会提示用户确认

---

#### `run_setup_spec(tune_type, input_type, rebuild=True)`

运行 SPEC setup 脚本进行编译和环境准备。

| 项目 | 说明 |
|------|------|
| **参数** | `tune_type: TuneType` — 优化级别（base/peak） |
| | `input_type: InputType` — 输入数据集类型（test/train/ref） |
| | `rebuild: bool` — 是否重新构建，默认 `True` |
| **返回值** | `str` — SPEC setup 日志文件路径 |
| **异常** | `CommandExecutionError` — 当命令执行失败时抛出 |

---

#### `execute_specinvoke(src_dir, dest_dir, input_type, binary_name_map=("", ""))`

执行 specinvoke 命令生成运行脚本。

| 项目 | 说明 |
|------|------|
| **参数** | `src_dir: str` — 源目录路径，包含 `speccmds.cmd` 文件 |
| | `dest_dir: str` — 目标目录路径 |
| | `input_type: InputType` — 输入数据集类型 |
| | `binary_name_map: tuple` — 二进制文件名映射（旧名, 新名），默认 `("", "")` |
| **返回值** | `bool` — 如果成功创建 `run_{input_type}.sh` 文件则返回 `True` |
| **异常** | `CommandExecutionError` — 当命令执行失败时抛出 |

---

#### `execute_specdiff(src_dir, dest_dir, input_type)`

执行 specinvoke 命令解析 compare.cmd 文件，生成 specdiff 验证脚本。

| 项目 | 说明 |
|------|------|
| **参数** | `src_dir: str` — 源目录路径，包含 `compare.cmd` 文件 |
| | `dest_dir: str` — 目标目录路径 |
| | `input_type: InputType` — 输入数据集类型 |
| **返回值** | `bool` — 如果成功创建 specdiff 脚本文件则返回 `True` |
| **异常** | 无 |

---

#### `_check_spec_environment()`

检查 SPEC 环境是否正确配置。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `bool` — 如果环境检查通过返回 `True` |
| **异常** | `FileOperationError` — 当 SPEC 安装目录不存在时抛出 |
| | `CommandExecutionError` — 当 SPEC 命令不可用时抛出 |

---

#### `_build_run_command()`

构建 SPEC 运行命令。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `List[str]` — SPEC 命令及参数列表 |
| **异常** | 无 |

**说明：** 此方法应由子类重写，基类返回空列表。

---

#### `run_spec_directly(output_dir=None)`

直接运行 SPEC 测试。

| 项目 | 说明 |
|------|------|
| **参数** | `output_dir: str \| None` — 结果输出目录，默认自动生成 |
| **返回值** | `Dict` — 包含 `success`、`output_dir`、`log_file`、`return_code`、`error_message` 的字典 |
| **异常** | `FileOperationError` — 当 SPEC 环境检查失败时抛出 |
| | `CommandExecutionError` — 当命令执行失败或用户中断时抛出 |

---

### 2.2 子类必须实现的方法

以下方法在基类中没有默认实现，子类（`SPEC2006Driver`、`SPEC2017Driver`）必须提供具体实现。

#### `get_bench_list()`

根据 `spec_benches` 字符串获取基准测试列表。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `List[str]` — 排序后的基准测试名称列表 |
| **异常** | `BenchmarkError` — 当没有选择到任何基准测试时抛出 |

**spec_benches 支持的格式：**

| 格式 | SPEC2006 | SPEC2017 |
|------|----------|----------|
| `"all"` | 所有基准测试 | 所有基准测试 |
| `"int"` | 整数基准测试 | 整数 speed 基准测试 |
| `"intspeed"` | — | 整数 speed 基准测试 |
| `"fp"` | 浮点基准测试 | 浮点 speed 基准测试 |
| `"fpspeed"` | — | 浮点 speed 基准测试 |
| `"400 401"` | 指定编号的基准测试 | 指定编号的基准测试 |

---

#### `get_ref_time(bench_name, input_type)`

获取基准测试的参考时间。

| 项目 | 说明 |
|------|------|
| **参数** | `bench_name: str` — 基准测试名称 |
| | `input_type: InputType` — 输入数据集类型 |
| **返回值** | `str` — 参考时间字符串（数字） |
| **异常** | `FileOperationError` — 当无法读取参考时间文件或参考时间不是有效数字时抛出 |

**说明：**

- SPEC2006：从 `{spec_bench_path}/{bench_name}/data/{input_type}/reftime` 读取
- SPEC2017：通过 `SPEC2017_REFTIME_MAP` 映射查找 reftime 文件路径

---

#### `get_bench_path(action_type, tune_type, input_type, spec_mode)`

获取基准测试的构建或运行目录路径列表。

| 项目 | 说明 |
|------|------|
| **参数** | `action_type: ActionType` — 动作类型（`ActionType.build` / `ActionType.run`） |
| | `tune_type: TuneType` — 优化级别 |
| | `input_type: InputType` — 输入数据集类型 |
| | `spec_mode: SPECMode` — 运行模式 |
| **返回值** | `List[str]` — 匹配的基准测试目录绝对路径列表 |
| **异常** | 无 |

**目录命名格式：**

| 版本 | 构建目录 | 运行目录 |
|------|----------|----------|
| SPEC2006 | `build_{tune_type}_{label}.XXXX` | `run_{tune_type}_{input_type}_{label}.XXXX` |
| SPEC2017 | `build_{tune_type}_{label}.XXXX` | `run_{tune_type}_{input_type}_{label}.XXXX`（非 ref） |
| SPEC2017 | — | `run_{tune_type}_{input_type}{spec_mode}_{label}.XXXX`（ref） |

---

#### `get_binary_path_map(tune_type, input_type, spec_mode)`

获取二进制文件路径映射。

| 项目 | 说明 |
|------|------|
| **参数** | `tune_type: TuneType` — 优化级别 |
| | `input_type: InputType` — 输入数据集类型 |
| | `spec_mode: SPECMode` — 运行模式 |
| **返回值** | `Dict[str, str]` — 基准测试名称到二进制文件路径的映射字典 |
| **异常** | 无 |

**说明：**

- SPEC2006：从 `exe` 目录获取，二进制文件名格式为 `{binary_name}_{tune_type}.{label}`
- SPEC2017：从 `build` 目录获取，二进制文件名格式为 `{binary_name}`

---

## 3. PackUtils 工具接口

`PackUtils` 提供文件操作、脚本生成、命令执行等辅助功能。

### 3.1 目录操作

#### `create_generated_dir(auto_mode=False)`

创建生成的文件目录。

| 项目 | 说明 |
|------|------|
| **参数** | `auto_mode: bool` — 是否自动模式，默认 `False` |
| **返回值** | `str` — 创建的打包生成目录的完整路径 |
| **异常** | `PackSPECError` — 当非自动模式下用户选择不覆盖已存在的目录时抛出 |

---

#### `create_dest_dir(profile_gen, auto_mode, pack_mode, spec_name, tune_type, input_type, spec_mode)`

创建基准测试打包的目标目录。

| 项目 | 说明 |
|------|------|
| **参数** | `profile_gen: bool` — 是否生成 profile |
| | `auto_mode: bool` — 是否自动模式 |
| | `pack_mode: PACKMode` — 打包模式（bin/run/buildrun） |
| | `spec_name: SPECName` — SPEC 版本 |
| | `tune_type: TuneType` — 优化级别 |
| | `input_type: InputType` — 输入数据集类型 |
| | `spec_mode: SPECMode` — 运行模式 |
| **返回值** | `str` — 创建的目标目录路径 |
| **异常** | `PackSPECError` — 当用户取消目录覆盖操作时抛出 |

---

#### `get_pack_generated_dir_path()`

获取打包生成的目录路径。

| 项目 | 说明 |
|------|------|
| **参数** | 无 |
| **返回值** | `str` — 目录的完整路径 |

**目录名称格式：**

- `auto_mode=True`：`{GENERATED_FILES_PATH}/{pack_name}`
- `auto_mode=False`：`{GENERATED_FILES_PATH}/{date}_{pack_name}`

---

#### `get_dest_dir(profile_gen, auto_mode, pack_mode, spec_name, tune_type, input_type, spec_mode)`

获取基准测试打包的目标目录路径（不创建目录）。

| 项目 | 说明 |
|------|------|
| **参数** | 同 `create_dest_dir` |
| **返回值** | `str` — 目标目录路径 |

---

### 3.2 文件操作

#### `copy_file_to_target_dir(src_path, dest_path, file_info="", error_info="")`

复制文件到目标目录。

| 项目 | 说明 |
|------|------|
| **参数** | `src_path: str` — 源文件路径 |
| | `dest_path: str` — 目标文件路径 |
| | `file_info: str` — 文件描述信息，默认 `""` |
| | `error_info: str` — 错误信息，默认 `""` |
| **返回值** | `bool` — 复制成功返回 `True`，失败返回 `False` |

---

#### `copy_script_file_to_target_dir(script_name, script_target_path)`

复制脚本文件到目标目录。

| 项目 | 说明 |
|------|------|
| **参数** | `script_name: str` — 脚本名称 |
| | `script_target_path: str` — 目标目录路径 |
| **返回值** | `bool` — 复制成功返回 `True`，失败返回 `False` |
| **异常** | `FileOperationError` — 当脚本文件不存在时抛出 |

---

#### `copy_spec_cfg_and_logs_to_target_dir(spec_dir, spec_cfg, dest_dir, tune_type, input_type)`

复制 SPEC 配置文件和日志到目标目录。

| 项目 | 说明 |
|------|------|
| **参数** | `spec_dir: str` — SPEC 目录路径 |
| | `spec_cfg: str` — SPEC 配置文件名 |
| | `dest_dir: str` — 目标目录路径 |
| | `tune_type: TuneType` — 优化级别 |
| | `input_type: InputType` — 输入数据集类型 |
| **返回值** | `None` |

**复制的文件包括：**

- SPEC 配置文件（cfg）
- setup 日志文件
- SPEC 运行日志文件
- 编译环境变量文件（compile.env）
- 打包配置文件

---

#### `use_template_to_create_script(template_name, script_target_dir, replace_dict)`

使用模板创建脚本文件。

| 项目 | 说明 |
|------|------|
| **参数** | `template_name: str` — 模板文件名（带 `.template` 后缀） |
| | `script_target_dir: str` — 目标目录路径 |
| | `replace_dict: Dict[str, str]` — 替换字典，key 为模板中的占位符，value 为替换值 |
| **返回值** | `None` |
| **异常** | `CommandExecutionError` — 当创建脚本失败时抛出 |

---

### 3.3 脚本生成

#### `commands_to_prepare_run(log_name, core_num, iterations, minimal_mode=False)`

生成准备运行的命令列表。

| 项目 | 说明 |
|------|------|
| **参数** | `log_name: str` — 日志文件名 |
| | `core_num: int` — 绑定的核心编号，`-1` 表示不绑定 |
| | `iterations: int` — 测试迭代次数 |
| | `minimal_mode: bool` — 是否启用极简模式，默认 `False` |
| **返回值** | `List[str]` — 准备运行的命令列表 |

---

#### `commands_to_run_bench(bench_name, profile_gen, spec_bench_map, core_num, ref_time, tune_type, label, input_type, minimal_mode=False)`

生成运行基准测试的命令列表。

| 项目 | 说明 |
|------|------|
| **参数** | `bench_name: str` — 基准测试名称 |
| | `profile_gen: bool` — 是否生成 profile |
| | `spec_bench_map: dict` — 基准测试二进制文件映射字典 |
| | `core_num: int` — 绑定的核心编号，`-1` 表示不绑定 |
| | `ref_time: float` — 参考时间 |
| | `tune_type: TuneType` — 优化级别 |
| | `label: str` — 基准测试标签 |
| | `input_type: InputType` — 输入数据集类型 |
| | `minimal_mode: bool` — 是否启用极简模式，默认 `False` |
| **返回值** | `List[str]` — 运行基准测试的命令列表 |

---

#### `commands_to_cal_score(script_target_dir, test_clock_rate, score_file="", minimal_mode=False)`

生成计算分数的命令列表。

| 项目 | 说明 |
|------|------|
| **参数** | `script_target_dir: str` — 脚本目标目录 |
| | `test_clock_rate: float` — 测试 CPU 主频，用于算分，单位 GHz |
| | `score_file: str` — 分数输出文件，默认 `""` |
| | `minimal_mode: bool` — 是否启用极简模式，默认 `False` |
| **返回值** | `List[str]` — 计算分数的命令列表 |
| **异常** | `FileOperationError` — 当复制算分脚本失败时抛出 |

---

#### `commands_to_send_message(message)`

生成发送消息的命令列表。

| 项目 | 说明 |
|------|------|
| **参数** | `message: str` — 要发送的消息内容 |
| **返回值** | `List[str]` — 发送消息的命令列表 |

---

### 3.4 命令执行

#### `execute_commands(command, work_dir)`

执行命令并捕获输出。

| 项目 | 说明 |
|------|------|
| **参数** | `command: str` — 要执行的命令字符串 |
| | `work_dir: str` — 命令执行的工作目录 |
| **返回值** | `List[str]` — 命令输出的行列表 |
| **异常** | `CommandExecutionError` — 当命令执行失败时抛出 |

---

## 4. 模块间交互接口

### 4.1 PackSPEC → SPECDriver

PackSPEC 通过 `spec_driver` 属性调用驱动方法。

```
PackSPEC
  └── spec_driver (SPECDriver 实例)
        ├── get_spec_info()          → 获取 SPEC 基本信息
        ├── get_binary_path_map()    → 获取二进制文件路径映射
        ├── get_bench_path()         → 获取基准测试目录路径
        ├── get_ref_time()           → 获取参考时间
        ├── run_setup_spec()         → 执行 SPEC 编译
        ├── execute_specinvoke()     → 生成运行脚本
        ├── execute_specdiff()       → 生成验证脚本
        └── run_spec_directly()      → 直接运行 SPEC 测试
```

**驱动实例化规则：**

| `spec_name` 值 | 创建的驱动实例 |
|-----------------|---------------|
| `SPECName.spec2006` | `SPEC2006Driver` |
| `SPECName.spec2006v1p01` | `SPEC2006V1P01Driver` |
| `SPECName.spec2017` | `SPEC2017Driver` |

---

### 4.2 PackSPEC → PackUtils

PackSPEC 通过 `utils` 属性调用工具方法。

```
PackSPEC
  └── utils (PackUtils 实例)
        ├── create_generated_dir()           → 创建生成目录
        ├── create_dest_dir()                → 创建目标目录
        ├── get_pack_generated_dir_path()    → 获取生成目录路径
        ├── get_dest_dir()                   → 获取目标目录路径
        ├── copy_file_to_target_dir()        → 复制文件
        ├── copy_spec_cfg_and_logs_to_target_dir() → 复制配置和日志
        ├── use_template_to_create_script()  → 使用模板创建脚本
        ├── commands_to_prepare_run()        → 生成准备运行命令
        ├── commands_to_run_bench()          → 生成运行基准测试命令
        ├── commands_to_cal_score()          → 生成计算分数命令
        ├── commands_to_send_message()       → 生成发送消息命令
        └── save_pack_spec_cfg()             → 保存配置文件
```

---

### 4.3 SPECDriver → PackUtils

SPECDriver 通过构造函数接收 `utils` 参数，通过 `self.utils` 调用工具方法。

```
SPECDriver.__init__(spec_cfg_path, spec_name, tune_type, input_type,
                    spec_mode, spec_benches, utils, iterations, rebuild, debug_mode)
  └── utils (PackUtils 实例，由 PackSPEC 创建并传入)
        ├── execute_commands()               → 执行命令
        ├── create_spec_setup_log_path()     → 创建 setup 日志路径
        └── get_spec_setup_log_path()        → 获取 setup 日志路径
```

---

### 4.4 配置传递

配置以字典格式在模块间传递，包含以下四个子配置块：

```python
config = {
    "task": {
        "pack_name": str,           # 打包任务名称
        "setup_spec": bool,         # 是否执行 SPEC 编译，默认 False
        "pack_binaries": bool,      # 是否打包二进制文件，默认 True
        "pack_benches": bool,       # 是否打包完整测试环境，默认 True
        "run_mode": RunMode,        # 运行模式，默认 RunMode.pack
    },
    "spec_config": {
        "spec_cfg_path": str,       # SPEC 配置文件绝对路径
        "spec_name": SPECName,      # SPEC 版本枚举
        "tune_type": TuneType,      # 优化级别枚举
        "input_type": InputType,    # 输入数据集类型枚举
        "spec_mode": SPECMode,      # 运行模式枚举
        "spec_benches": str,        # 基准测试选择字符串
        "iterations": int,          # 测试迭代次数，默认 3
        "rebuild": bool,            # 是否重新构建，默认 True
    },
    "pack_config": {
        "test_core_num": int,       # 绑定核心编号，默认 -1
        "test_clock_rate": float,   # CPU 主频(GHz)，默认 1.0
        "profile_gen": bool,        # 是否生成 Profile，默认 False
        "auto_mode": bool,          # 是否自动模式，默认 False
        "report_format": str,       # 报告格式，默认 "json"
        "verify_mode": bool,        # 是否开启 QEMU 验证，默认 False
        "minimal_mode": bool,       # 是否开启极简模式，默认 False
        "qemu_verify_parallel_jobs": int,  # QEMU 验证并行任务数，默认 0
    },
    "msg_config": {
        "enable_dingtalk_message": bool,  # 是否开启钉钉消息，默认 False
        "log_language": str,              # 日志语言，默认 "zh"
    },
}
```

---

## 5. 配置文件格式

### 5.1 pack_spec.cfg JSON 格式说明

PackSPEC 使用 JSON 格式保存和加载配置文件，文件名为 `pack_spec.cfg`。

**保存路径：**

- `auto_mode=True`：`{GENERATED_FILES_PATH}/{pack_name}/pack_spec.cfg`
- `auto_mode=False`：`{GENERATED_FILES_PATH}/{date}_{pack_name}/pack_spec.cfg`

**JSON 结构示例：**

```json
{
    "task": {
        "pack_name": "riscv_llvm22_base",
        "setup_spec": false,
        "pack_binaries": true,
        "pack_benches": true,
        "run_mode": "pack"
    },
    "spec_config": {
        "spec_cfg_path": "/path/to/spec.cfg",
        "spec_name": "spec2017",
        "tune_type": "base",
        "input_type": "ref",
        "spec_mode": "speed",
        "spec_benches": "all",
        "iterations": 3,
        "rebuild": true
    },
    "pack_config": {
        "test_core_num": 4,
        "test_clock_rate": 1.0,
        "profile_gen": false,
        "auto_mode": false,
        "report_format": "json",
        "verify_mode": false,
        "minimal_mode": false,
        "qemu_verify_parallel_jobs": 0
    },
    "msg_config": {
        "enable_dingtalk_message": false,
        "log_language": "zh"
    },
    "date": "260410"
}
```

---

### 5.2 枚举类型序列化/反序列化规则

PackSPEC 使用自定义的 `EnumEncoder` 和 `EnumDecoder` 处理枚举类型与 JSON 字符串之间的转换。

#### 序列化规则（EnumEncoder）

枚举类型在序列化时转换为其 `name` 属性字符串：

| 枚举类型 | 枚举值 | 序列化结果 |
|----------|--------|-----------|
| `SPECName` | `SPECName.spec2006` | `"spec2006"` |
| `SPECName` | `SPECName.spec2006v1p01` | `"spec2006v1p01"` |
| `SPECName` | `SPECName.spec2017` | `"spec2017"` |
| `TuneType` | `TuneType.base` | `"base"` |
| `TuneType` | `TuneType.peak` | `"peak"` |
| `TuneType` | `TuneType.all` | `"all"` |
| `InputType` | `InputType.test` | `"test"` |
| `InputType` | `InputType.train` | `"train"` |
| `InputType` | `InputType.ref` | `"ref"` |
| `InputType` | `InputType.all` | `"all"` |
| `SPECMode` | `SPECMode.speed` | `"speed"` |
| `SPECMode` | `SPECMode.rate` | `"rate"` |
| `RunMode` | `RunMode.pack` | `"pack"` |
| `RunMode` | `RunMode.direct` | `"direct"` |

#### 反序列化规则（EnumDecoder）

反序列化时根据字段名自动匹配枚举类进行转换：

| 字段名 | 目标枚举类 |
|--------|-----------|
| `spec_name` | `SPECName` |
| `tune_type` | `TuneType` |
| `input_type` | `InputType` |
| `spec_mode` | `SPECMode` |

**反序列化流程：**

1. `EnumDecoder` 在 JSON 解码时通过 `object_hook` 回调拦截每个字典对象
2. 对字典中的每个字段，检查字段名是否在 `FIELD_TO_ENUM` 映射中
3. 如果匹配，将字符串值通过 `enum_class[string_value]` 转换为枚举实例
4. 如果转换失败（KeyError），保留原始字符串值

**示例：**

```python
import json
from pack_spec.pack_utils import EnumEncoder, EnumDecoder
from pack_spec.pack_config import SPECName, TuneType

# 序列化
data = {"spec_name": SPECName.spec2017, "tune_type": TuneType.base}
json_str = json.dumps(data, cls=EnumEncoder)
# 结果: '{"spec_name": "spec2017", "tune_type": "base"}'

# 反序列化
loaded = json.loads(json_str, cls=EnumDecoder)
# 结果: {"spec_name": SPECName.spec2017, "tune_type": TuneType.base}
```

---

## 附录：异常类层次结构

```
PackSPECError (基础异常类)
├── ConfigError           — 配置相关异常
├── FileOperationError    — 文件操作异常
├── CommandExecutionError — 命令执行异常
└── BenchmarkError        — 基准测试异常
```

所有异常均包含 `message`（异常消息）和 `code`（异常代码，默认为 1）属性。
