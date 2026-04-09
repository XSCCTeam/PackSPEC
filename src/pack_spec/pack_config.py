"""
PackSPEC配置模块

本模块定义了PackSPEC工具的全局配置、枚举类型和异常类。

主要内容包括：
1. 枚举类型定义：
   - ActionType: SPEC基准测试动作类型(build/run)
   - TuneType: 优化级别(base/peak/all)
   - InputType: 输入数据集类型(test/train/ref/all)
   - SPECName: SPEC版本(spec2006/spec2006v1p01/spec2017)
   - SPECSubBench: 基准测试子集(all/int/fp)
   - SPECMode: 运行模式(speed/rate)
   - PACKMode: 打包模式(bin/run/buildrun)

2. 异常类定义：
   - PackSPECError: 基础异常类
   - ConfigError: 配置相关异常
   - FileOperationError: 文件操作异常
   - CommandExecutionError: 命令执行异常
   - BenchmarkError: 基准测试异常

3. 全局配置常量：
   - 路径配置
   - 默认值配置
   - LLVM配置
   - 钉钉机器人配置
   - SPEC安装路径配置
"""

import os
from datetime import datetime
from loguru import logger
import sys
from enum import Enum
from dotenv import load_dotenv


P_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""项目根目录的绝对路径"""

# 自动加载 .env 文件
_env_file = os.path.join(P_PATH, ".env")
if os.path.exists(_env_file):
    load_dotenv(_env_file)


#########################################
# Local Configs - 本地配置
#########################################

CURRENT_DATE = datetime.now().strftime("%y%m%d")
"""当前日期，格式：YYMMDD"""

CURRENT_TIME = datetime.now().strftime("%y%m%d_%H%M%S")
"""当前时间，格式：YYMMDD_HHMMSS"""

HOME_PATH = os.path.expanduser("~")
"""用户主目录路径"""

LOGGER_PATH = os.path.join(P_PATH, "log", f"PackSpec_{CURRENT_TIME}.log")
"""日志文件路径"""

logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    LOGGER_PATH,
    level="DEBUG",
    rotation="8 MB",
)
"""配置loguru日志记录器"""

PACK_PATH = os.path.join(P_PATH, "packed_files")
"""打包输出目录路径"""

SCRIPTS_PATH = os.path.join(P_PATH, "scripts")
"""脚本文件目录路径"""

GENERATED_FILES_PATH = os.path.join(P_PATH, "generated_files")
"""生成的配置文件目录路径"""


#########################################
# PackSPEC Configs - PackSPEC配置
#########################################


class ActionType(Enum):
    """
    SPEC基准测试动作类型枚举类
    
    定义SPEC基准测试的不同操作阶段类型
    
    Attributes:
        build (int): 构建阶段，对应值1，用于编译基准测试程序
        run (int): 运行阶段，对应值2，用于运行基准测试程序
    
    Note:
        用于指定SPEC基准测试的执行阶段，build阶段编译测试程序，run阶段运行测试程序
    """
    build = 1
    run = 2


class TuneType(Enum):
    """
    SPEC基准测试优化类型枚举类
    
    定义SPEC基准测试的不同优化级别
    
    Attributes:
        base (int): 基础优化级别，对应值1，使用标准编译优化选项
        peak (int): 峰值优化级别，对应值2，使用更激进的优化策略
        all (int): 所有优化级别，对应值3，同时处理base和peak
    
    Note:
        base级别使用标准优化选项，所有基准测试使用相同的编译选项；
        peak级别允许针对每个基准测试使用特定的优化选项
    """
    base = 1
    peak = 2
    all = 3


class InputType(Enum):
    """
    SPEC基准测试输入类型枚举类
    
    定义SPEC基准测试的不同输入数据集类型
    
    Attributes:
        test (int): 测试输入数据集，对应值1，最小数据集，用于快速验证
        train (int): 训练输入数据集，对应值2，中等大小数据集
        ref (int): 参考输入数据集，对应值3，最大数据集，用于正式测试和报告
        all (int): 所有输入类型，对应值4，同时处理test/train/ref
    
    Note:
        test数据集最小，运行时间最短，适合快速验证程序正确性；
        train数据集中等大小，用于调试和性能调优；
        ref数据集最大，是正式测试和提交报告必须使用的数据集
    """
    test = 1
    train = 2
    ref = 3
    all = 4


class SPECName(Enum):
    """
    SPEC基准测试版本枚举类
    
    定义支持的SPEC CPU基准测试版本
    
    Attributes:
        spec2006 (int): SPEC CPU 2006 v1.2.0版本
        spec2006v1p01 (int): SPEC CPU 2006 v1.0.1版本(即将废弃)
        spec2017 (int): SPEC CPU 2017版本
    """
    spec2006 = 1
    spec2006v1p01 = 2
    spec2017 = 3


class SPECSubBench(Enum):
    """
    SPEC基准测试子集枚举类
    
    定义SPEC基准测试的子集分类
    
    Attributes:
        all (int): 完整基准测试套件
        int (int): 整数基准测试子集
        fp (int): 浮点基准测试子集
    """
    all = 1
    int = 2
    fp = 3


class SPECMode(Enum):
    """
    SPEC基准测试运行模式枚举类
    
    定义SPEC基准测试的运行模式
    
    Attributes:
        speed (int): 速度模式，测量单任务执行时间
        rate (int): 吞吐模式，测量多任务并发吞吐量
    
    Note:
        speed模式适合测量单核性能；
        rate模式适合测量多核并发性能
    """
    speed = 1
    rate = 2


class PACKMode(Enum):
    """
    PackSPEC打包模式枚举类
    
    定义打包输出的内容类型
    
    Attributes:
        bin (int): 仅打包二进制文件
        run (int): 打包运行环境(不含构建目录)
        buildrun (int): 打包完整环境(含构建目录)
    """
    bin = 1
    run = 2
    buildrun = 3


class RunMode(Enum):
    """
    PackSPEC运行模式枚举类
    
    定义PackSPEC的运行模式，区分打包模式和直接运行模式
    
    Attributes:
        pack (int): 打包模式，将SPEC测试打包为可独立运行的文件集
        direct (int): 直接运行模式，直接调用runspec/runcpu命令执行测试
    
    Note:
        打包模式适用于需要在其他机器上运行测试的场景；
        直接运行模式适用于本地直接执行测试的场景，无需打包文件
    """
    pack = 1
    direct = 2


class LogLanguage(Enum):
    """
    日志语言枚举类
    
    定义日志输出的语言选择
    
    Attributes:
        zh (int): 中文
        en (int): 英文
    """
    zh = 1
    en = 2


DEFAULT_RUN_MODE = RunMode.pack
"""默认运行模式，默认为打包模式以保持向后兼容"""

DEFAULT_REPORT_FORMAT = "json"
"""默认报告格式，支持json和markdown"""

DEFAULT_LOG_LANGUAGE = LogLanguage.zh
"""默认日志语言，默认使用中文"""

RESULTS_OUTPUT_PATH = os.path.join(P_PATH, "spec_results")
"""SPEC测试结果输出目录路径"""

DEFAULT_CORE_NUM = -1
"""默认绑定的CPU核心编号，-1表示不绑定核心"""

DEFAULT_ITERATIONS = 3
"""默认测试迭代次数"""

DEFAULT_CLOCK_RATE = 1.0
"""默认CPU主频，单位GHz，用于计算SPEC分数"""

DEFAULT_DEBUG_MODE = False
"""默认调试模式开关"""

DEFAULT_REBUILD = True
"""默认是否重新构建"""

DEFAULT_PROFILE_GEN = False
"""默认是否生成Profile"""

DEFAULT_AUTO_MODE = False
"""默认是否自动模式，自动模式下无需用户确认"""

RANDOM_SUFFIX_LENGTH = 4
"""随机后缀长度，用于目录命名避免冲突"""


class PackSPECError(Exception):
    """
    PackSPEC工具的基础异常类
    
    所有PackSPEC相关的异常都应该继承自这个类，便于统一异常处理。
    
    Args:
        message (str): 异常消息，描述错误详情
        code (int): 异常代码，默认为1，可用于程序退出码
        
    Attributes:
        message (str): 异常消息
        code (int): 异常代码
        
    Example:
        >>> raise PackSPECError("配置文件不存在", code=2)
    """
    def __init__(self, message, code=1):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConfigError(PackSPECError):
    """
    配置相关异常
    
    用于处理配置加载、验证、解析等过程中的错误。
    
    Example:
        >>> raise ConfigError("无法解析配置文件: 格式错误")
    """
    pass


class FileOperationError(PackSPECError):
    """
    文件操作相关异常
    
    用于处理文件复制、创建、删除、读取等操作中的错误。
    
    Example:
        >>> raise FileOperationError("无法复制文件: 权限不足")
    """
    pass


class CommandExecutionError(PackSPECError):
    """
    命令执行相关异常
    
    用于处理外部命令执行过程中的错误，如subprocess调用失败。
    
    Example:
        >>> raise CommandExecutionError("setup脚本执行失败: 返回码非零")
    """
    pass


class BenchmarkError(PackSPECError):
    """
    基准测试相关异常
    
    用于处理基准测试选择、运行、验证等过程中的错误。
    
    Example:
        >>> raise BenchmarkError("未找到匹配的基准测试")
    """
    pass

#########################################
# LLVM Configs - LLVM工具链配置
#########################################

DEFAULT_LLVM_PATH = os.getenv('DEFAULT_LLVM_PATH')
"""默认LLVM安装路径，从环境变量获取"""

if DEFAULT_LLVM_PATH != None:
    DEFAULT_LLVM_PROFDATA_PATH = os.path.join(DEFAULT_LLVM_PATH, "bin", "llvm-profdata")
    """llvm-profdata工具路径，用于合并profile文件"""
else:
    DEFAULT_LLVM_PROFDATA_PATH = None


#########################################
# DingDing robot Configs - 钉钉机器人配置
#########################################

BOSC_API_KEY = os.getenv('BOSC_API_KEY')
"""钉钉机器人API密钥，从环境变量获取"""

BOSC_AT_USER = os.getenv('BOSC_AT_USER')
"""钉钉通知@的用户手机号，从环境变量获取"""


#########################################
# SPEC Configs - SPEC安装路径配置
#########################################

SPEC2006_PATH = os.getenv('SPEC2006_PATH')
"""SPEC2006安装目录路径，从环境变量获取"""

if SPEC2006_PATH != None:
    SPEC2006_BENCH_PATH = os.path.join(SPEC2006_PATH, "benchspec", "CPU2006")
    """SPEC2006基准测试目录路径"""
    SPEC2006_CONFIG_PATH = os.path.join(SPEC2006_PATH, "config")
    """SPEC2006配置文件目录路径"""
else:
    SPEC2006_BENCH_PATH = None
    SPEC2006_CONFIG_PATH = None

SPEC2017_PATH = os.getenv('SPEC2017_PATH')
"""SPEC2017安装目录路径，从环境变量获取"""

if SPEC2017_PATH != None:
    SPEC2017_BENCH_PATH = os.path.join(SPEC2017_PATH, "benchspec", "CPU2017")
    """SPEC2017基准测试目录路径"""
    SPEC2017_CONFIG_PATH = os.path.join(SPEC2017_PATH, "config")
    """SPEC2017配置文件目录路径"""
else:
    SPEC2017_BENCH_PATH = None
    SPEC2017_CONFIG_PATH = None


#########################################
# QEMU Configs - QEMU模拟器配置
#########################################

QEMU_PATH = os.getenv('QEMU_PATH')
"""QEMU安装目录路径，从环境变量获取，用于QEMU验证模式"""

QEMU_CMD = os.getenv('QEMU_CMD', 'qemu-aarch64')
"""QEMU模拟器命令，从环境变量获取，默认为qemu-aarch64"""

DEFAULT_VERIFY_MODE = False
"""默认验证模式开关，开启后生成QEMU验证脚本用于验证编译出的binary是否正确"""

DEFAULT_MINIMAL_MODE = False
"""默认极简模式开关，开启后生成的脚本使用POSIX兼容语法，降低对运行环境的要求"""


class LogMessages:
    """
    日志消息管理类
    
    提供中英文日志消息的统一管理，根据语言配置返回对应的消息文本
    
    Attributes:
        language (LogLanguage): 当前语言配置
    """
    
    MESSAGES = {
        "config_saved": {
            "zh": "PackSPEC 配置文件已保存到: {path}",
            "en": "PackSPEC config file saved to: {path}"
        },
        "bench_dir_not_found": {
            "zh": "未找到基准测试目录: {bench_name}",
            "en": "Failed to find bench dir for {bench_name}."
        },
        "spec_log_found": {
            "zh": "从 '{file}' 找到 SPEC 日志",
            "en": "Find spec log from '{file}'"
        },
        "spec_log_marked_line_not_found": {
            "zh": "从 '{file}' 查找 SPEC 日志失败: 未找到标记行",
            "en": "Failed find spec log from '{file}': marked line not found."
        },
        "spec_log_parse_error": {
            "zh": "从 '{file}' 查找 SPEC 日志失败: {error}",
            "en": "Failed find spec log from '{file}': {error}"
        },
        "generated_dir_created": {
            "zh": "已创建生成文件目录: {path}",
            "en": "Created generated files dir: {path}"
        },
        "pack_dir_exists": {
            "zh": "打包生成目录 {path} 已存在",
            "en": "Pack generated files dir {path} already exists."
        },
        "continue_prompt": {
            "zh": "是否继续? (y/n): ",
            "en": "Do you want to continue? (y/n): "
        },
        "pack_dir_created": {
            "zh": "已创建打包生成目录: {path}",
            "en": "Created pack generated files dir: {path}"
        },
        "operation_canceled": {
            "zh": "用户取消了操作",
            "en": "User canceled the operation. "
        },
        "dest_dir_exists": {
            "zh": "目标目录 {path} 已存在",
            "en": "Directory {path} already exists."
        },
        "overwrite_prompt": {
            "zh": "是否覆盖? (y/n): ",
            "en": "Do you want to overwrite it? (y/n): "
        },
        "overwriting_dir": {
            "zh": "正在覆盖目录 {path}",
            "en": "Overwriting directory {path} "
        },
        "operation_canceled_not_overwritten": {
            "zh": "用户取消了操作，目录未被覆盖",
            "en": "User canceled the operation. Directory not overwritten."
        },
        "creating_dir": {
            "zh": "正在创建目录 {path}",
            "en": "Creating directory {path} "
        },
        "env_file_created": {
            "zh": "已创建 {name}.env 记录编译环境",
            "en": "Create {name}.env to record compile environment."
        },
        "env_file_failed": {
            "zh": "创建 compile.env 失败: {error}",
            "en": "Failed to create compile.env: {error}"
        },
        "executing_command": {
            "zh": "正在执行命令: {command}",
            "en": "Executing command: {command}"
        },
        "command_failed": {
            "zh": "命令执行失败: {error}",
            "en": "Command failed with error: {error}"
        },
        "command_execute_failed": {
            "zh": "执行命令失败: {error}",
            "en": "Failed to execute command: {error}"
        },
        "file_copied": {
            "zh": "已复制 {info} 文件 '{src}' 到 '{dest}'",
            "en": "Copie {info} file '{src}' to '{dest}'."
        },
        "copying_file": {
            "zh": "正在复制 {src}\n\t从 {from_path} 到 {to_path}",
            "en": "Copying {src}\n\tFrom {from_path} -to-> {to_path}"
        },
        "copy_failed": {
            "zh": "复制 {info} 文件 '{src}' 到 '{dest}' 失败: {error}",
            "en": "Failed to copy {info} file '{src}' to '{dest}': {error}"
        },
        "script_created": {
            "zh": "从模板 {template} 创建脚本 {name} 到 {dir}",
            "en": "Create script {name} from template {template} to {dir}."
        },
        "script_create_failed": {
            "zh": "从模板 {template} 创建脚本 {name} 到 {dir} 失败: {error}",
            "en": "Failed to create script {name} from template {template} to {dir}: {error}"
        },
        "add_cal_score_commands": {
            "zh": "添加计算分数命令",
            "en": "Add cal score commands."
        },
        "add_send_message_commands": {
            "zh": "添加发送消息命令",
            "en": "Add send message commands."
        },
        "add_send_md_message_commands": {
            "zh": "添加发送 Markdown 消息命令",
            "en": "Add send md message commands."
        },
        "add_collect_profiles_commands": {
            "zh": "添加收集 Profile 命令",
            "en": "Add collect profiles commands."
        },
        "result_dir_not_found": {
            "zh": "结果目录不存在: {path}",
            "en": "Result directory not found: {path}"
        },
        "sum_file_not_found": {
            "zh": "未找到 .sum 文件: {path}",
            "en": "No .sum file found: {path}"
        },
        "sum_parse_failed": {
            "zh": "解析 {path} 失败: {error}",
            "en": "Failed to parse {path}: {error}"
        },
        "qemu_cmd_invalid": {
            "zh": "QEMU命令 '{cmd}' 可能不是有效的QEMU模拟器",
            "en": "QEMU command '{cmd}' may not be a valid QEMU emulator"
        },
        "spec_setup_log_warning": {
            "zh": "如果您没有使用此工具进行 setup，spec_setup 日志将不会生成。请忽略此警告。",
            "en": "If you didn't use this tool for setup, spec_setup log will not be generated. Please ignore this warning."
        },
        "start_packing": {
            "zh": "开始打包 {name}",
            "en": "Start Packing {name}"
        },
        "current_time": {
            "zh": "当前时间: {time}",
            "en": "Current Time: {time}"
        },
        "spec_version": {
            "zh": "{name} 版本: {version}",
            "en": "{name} Version: {version}"
        },
        "spec_path": {
            "zh": "路径: {path}",
            "en": "Path: {path}"
        },
        "no_binary_to_copy": {
            "zh": "没有二进制文件可复制",
            "en": "No binary to copy."
        },
        "cannot_match_bench": {
            "zh": "无法从 '{dir}' 匹配 '{bench}'",
            "en": "Cannot match '{bench}' from '{dir}'"
        },
        "copying_bench": {
            "zh": "正在复制 {bench}...",
            "en": "Copying {bench}..."
        },
        "copy_from_to": {
            "zh": "\t从 {from_path} 到 {to_path}",
            "en": "\tFrom {from_path} -to-> {to_path}"
        },
        "copy_bench_done": {
            "zh": "{bench} 复制完成",
            "en": "Copie {bench} done."
        },
        "copy_bench_failed": {
            "zh": "复制 {bench} 失败: {error}",
            "en": "Failed to copy {bench}: {error}"
        },
        "run_test_script_failed": {
            "zh": "在 {dir} 生成 run_test.sh 失败",
            "en": "Failed to generate run_test.sh in {dir}"
        },
        "no_benches_to_copy": {
            "zh": "没有基准测试可复制",
            "en": "No benches to copy."
        },
        "run_script_created": {
            "zh": "已在 {path} 创建运行脚本 {name}",
            "en": "Created {name} script at {path}"
        },
        "no_benchmark_dirs_to_run": {
            "zh": "没有可运行的基准测试目录",
            "en": "No benchmark directories to run"
        },
        "start_direct_run": {
            "zh": "开始直接运行SPEC测试",
            "en": "Starting direct SPEC test run"
        },
        "spec_env_check_failed": {
            "zh": "SPEC环境检查失败: {error}",
            "en": "SPEC environment check failed: {error}"
        },
        "spec_test_failed": {
            "zh": "SPEC测试执行失败: {error}",
            "en": "SPEC test execution failed: {error}"
        },
        "spec_test_unknown_error": {
            "zh": "运行SPEC测试时发生未知错误: {error}",
            "en": "Unknown error occurred while running SPEC test: {error}"
        },
        "spec_test_execution_failed": {
            "zh": "SPEC测试执行失败: {error}",
            "en": "SPEC test execution failed: {error}"
        },
        "parsing_results": {
            "zh": "解析测试结果...",
            "en": "Parsing test results..."
        },
        "test_result_summary": {
            "zh": "测试结果摘要",
            "en": "Test Result Summary"
        },
        "int_score": {
            "zh": "整数测试(INT)分数: {score:.2f}",
            "en": "Integer test (INT) score: {score:.2f}"
        },
        "int_score_failed": {
            "zh": "整数测试(INT)分数: 解析失败或无有效数据",
            "en": "Integer test (INT) score: Parse failed or no valid data"
        },
        "fp_score": {
            "zh": "浮点测试(FP)分数: {score:.2f}",
            "en": "Floating point test (FP) score: {score:.2f}"
        },
        "fp_score_failed": {
            "zh": "浮点测试(FP)分数: 解析失败或无有效数据",
            "en": "Floating point test (FP) score: Parse failed or no valid data"
        },
        "generating_qemu_verify_script": {
            "zh": "生成QEMU验证脚本",
            "en": "Generating QEMU verification scripts"
        },
        "qemu_dir": {
            "zh": "QEMU目录: {path}",
            "en": "QEMU directory: {path}"
        },
        "spec_version_info": {
            "zh": "SPEC版本: {version}",
            "en": "SPEC version: {version}"
        },
        "tune_type_info": {
            "zh": "优化级别: {type}",
            "en": "Tune type: {type}"
        },
        "input_type_info": {
            "zh": "输入类型: {type}",
            "en": "Input type: {type}"
        },
        "dir_exists_auto_overwrite": {
            "zh": "目录 {path} 已存在，自动模式下将覆盖",
            "en": "Directory {path} already exists, will overwrite in auto mode"
        },
        "dir_exists": {
            "zh": "目录 {path} 已存在",
            "en": "Directory {path} already exists"
        },
        "bench_dir_not_found_qemu": {
            "zh": "无法找到基准测试目录: {bench}",
            "en": "Cannot find benchmark directory: {bench}"
        },
        "copying_bench_qemu": {
            "zh": "复制 {bench}...",
            "en": "Copying {bench}..."
        },
        "copy_bench_qemu_failed": {
            "zh": "复制 {bench} 失败: {error}",
            "en": "Failed to copy {bench}: {error}"
        },
        "qemu_verify_script_done": {
            "zh": "QEMU验证脚本生成完成",
            "en": "QEMU verification script generation completed"
        },
        "output_dir": {
            "zh": "输出目录: {path}",
            "en": "Output directory: {path}"
        },
        "scripts_generated": {
            "zh": "生成脚本数量: {count}",
            "en": "Number of scripts generated: {count}"
        },
        "run_mode_direct": {
            "zh": "运行模式: 直接运行 (RunMode.direct)",
            "en": "Run mode: Direct run (RunMode.direct)"
        },
        "executing_run_spec": {
            "zh": "执行 run_spec()...",
            "en": "Executing run_spec()..."
        },
        "run_mode_pack": {
            "zh": "运行模式: 打包模式 (RunMode.pack)",
            "en": "Run mode: Pack mode (RunMode.pack)"
        },
        "executing_setup_spec": {
            "zh": "执行 setup_spec()...",
            "en": "Executing setup_spec()..."
        },
        "executing_pack_binaries": {
            "zh": "执行 pack_binaries()...",
            "en": "Executing pack_binaries()..."
        },
        "executing_pack_benches_cfg": {
            "zh": "执行 pack_benches_cfg()...",
            "en": "Executing pack_benches_cfg()..."
        },
        "executing_pack_qemu_verify": {
            "zh": "执行 pack_qemu_verify()...",
            "en": "Executing pack_qemu_verify()..."
        },
        "all_tasks_completed": {
            "zh": "所有任务执行完成",
            "en": "All tasks completed"
        },
        "executed_steps": {
            "zh": "执行步骤: {steps}",
            "en": "Executed steps: {steps}"
        },
        "successfully_copied_files": {
            "zh": "成功复制 {count} 个文件",
            "en": "Successfully copied {count} files."
        },
        "successfully_copied_benches": {
            "zh": "成功复制 {count} 个基准测试",
            "en": "Successfully copied {count} benches."
        },
        "created_script_at": {
            "zh": "已在 {path} 创建脚本 {name}",
            "en": "Created {name} script at {path}"
        },
        "report_generated": {
            "zh": "测试报告已生成: {path}",
            "en": "Test report generated: {path}"
        },
        "verify_script_generated": {
            "zh": "生成验证脚本: {path}",
            "en": "Generated verify script: {path}"
        },
        "batch_verify_script_generated": {
            "zh": "生成批量验证脚本: {path}",
            "en": "Generated batch verify script: {path}"
        },
        "no_bench_selected": {
            "zh": "从 {benches} 中未选择任何基准测试 ({spec_name})",
            "en": "No bench selected from {benches} in {spec_name}."
        },
        "selected_benches": {
            "zh": "从 {benches} 中选择了 {count} 个基准测试 ({spec_name})",
            "en": "Selected {count} benches from {benches} in {spec_name}."
        },
        "selected_bench": {
            "zh": "已选择: {bench}",
            "en": "Selected {bench}."
        },
        "get_reftime_from": {
            "zh": "从 {path} 获取参考时间 {bench}.{input_type}",
            "en": "Get reftime {bench}.{input_type} from {path}."
        },
        "get_reftime_failed": {
            "zh": "从 '{path}' 获取参考时间失败",
            "en": "Failed to get reftime from '{path}'"
        },
        "get_reftime_error": {
            "zh": "从 '{path}' 获取参考时间失败: {error}",
            "en": "Failed to get reftime from '{path}': {error}"
        },
        "get_bench_dir_with": {
            "zh": "获取基准测试目录参数:",
            "en": "Get bench dir with:"
        },
        "action_type_info": {
            "zh": "  action_type: {value}",
            "en": "  action_type: {value}"
        },
        "tune_type_info_debug": {
            "zh": "  tune_type: {value}",
            "en": "  tune_type: {value}"
        },
        "input_type_info_debug": {
            "zh": "  input_type: {value}",
            "en": "  input_type: {value}"
        },
        "spec_mode_info_debug": {
            "zh": "  spec_mode: {value}",
            "en": "  spec_mode: {value}"
        },
        "bench_run_dir": {
            "zh": "基准测试 {bench} 运行目录: {path}",
            "en": "Bench {bench} run dir: {path}"
        },
        "directory_not_exist": {
            "zh": "目录 {path} 不存在",
            "en": "Directory {path} not exist."
        },
        "bench_not_found_in": {
            "zh": "在 {prefix} 中未找到基准测试 {bench}",
            "en": "Bench {bench} not found in {prefix}."
        },
        "bench_found_multiple": {
            "zh": "基准测试 {bench} 在 {prefix} 中找到多个匹配",
            "en": "Bench {bench} found in more than one {prefix}."
        },
        "found_path": {
            "zh": "找到: {path}",
            "en": "Found {path}"
        },
        "bench_using": {
            "zh": "基准测试 {bench} 使用 {selected}",
            "en": "Bench {bench} using {selected}"
        },
        "build_runspec_cmd": {
            "zh": "构建runspec命令: {cmd}",
            "en": "Build runspec command: {cmd}"
        },
        "build_runcpu_cmd": {
            "zh": "构建runcpu命令: {cmd}",
            "en": "Build runcpu command: {cmd}"
        },
        "spec_path_not_set": {
            "zh": "SPEC_PATH 未设置",
            "en": "SPEC_PATH is not set"
        },
        "binary_not_found": {
            "zh": "在 {dir} 中未找到二进制文件 {binary}",
            "en": "Binary {binary} not found in {dir}"
        },
        "basepeak_set_to_yes": {
            "zh": "'basepeak' 在 {path} 中设置为 yes",
            "en": "'basepeak' is set to yes in {path}."
        },
        "basepeak_meaning": {
            "zh": "设置 'basepeak' 为 yes 意味着:",
            "en": "Set 'basepeak' to yes means:"
        },
        "continue_with_basepeak": {
            "zh": "继续使用 'basepeak' 设置",
            "en": "Process continue with 'basepeak' setting."
        },
        "aborted_by_user": {
            "zh": "用户中止",
            "en": "Aborted by user."
        },
        "config_file_not_found": {
            "zh": "配置文件 {path} 未找到",
            "en": "File {path} not found."
        },
        "setting_up_spec": {
            "zh": "从配置文件设置 SPEC: {path}",
            "en": "Setting up spec from config: {path}"
        },
        "executing_command_debug": {
            "zh": "执行命令: {cmd}",
            "en": "Executing command: {cmd}"
        },
        "command_failed_return_code": {
            "zh": "命令执行失败，返回码: {code}",
            "en": "Command failed with return code: {code}"
        },
        "successfully_setup_spec": {
            "zh": "成功从配置文件 {path} 设置 SPEC ({tune_type}_{input_type})",
            "en": "Successfully setup spec with {tune_type}_{input_type} from config: {path}"
        },
        "no_starting_run_found": {
            "zh": "命令输出中未找到 '# Starting run'",
            "en": "No '# Starting run' found in command output"
        },
        "successfully_created_file": {
            "zh": "成功创建文件: {path}",
            "en": "Successfully created {path}"
        },
        "spec_env_check_passed": {
            "zh": "SPEC环境检查通过: {path}",
            "en": "SPEC environment check passed: {path}"
        },
        "build_run_command_should_override": {
            "zh": "_build_run_command() 应由子类重写",
            "en": "_build_run_command() should be overridden by subclass"
        },
        "start_running_spec": {
            "zh": "开始运行SPEC测试: {cmd}",
            "en": "Starting SPEC test run: {cmd}"
        },
        "result_output_dir": {
            "zh": "结果输出目录: {path}",
            "en": "Result output directory: {path}"
        },
        "spec_test_completed": {
            "zh": "SPEC测试完成: {path}",
            "en": "SPEC test completed: {path}"
        },
        "user_interrupted_test": {
            "zh": "用户中断测试",
            "en": "User interrupted test"
        },
        "spec_command_failed": {
            "zh": "执行SPEC命令失败: {error}",
            "en": "Failed to execute SPEC command: {error}"
        },
    }
    
    def __init__(self, language: LogLanguage = DEFAULT_LOG_LANGUAGE):
        """
        初始化日志消息管理器
        
        Args:
            language (LogLanguage): 语言配置，默认为中文
        """
        self.language = language
    
    def get(self, key: str, **kwargs) -> str:
        """
        获取日志消息
        
        Args:
            key (str): 消息键名
            **kwargs: 消息格式化参数
            
        Returns:
            str: 格式化后的消息文本
        """
        if key not in self.MESSAGES:
            return key
        
        lang_key = "zh" if self.language == LogLanguage.zh else "en"
        message = self.MESSAGES[key].get(lang_key, self.MESSAGES[key].get("zh", key))
        
        if kwargs:
            try:
                return message.format(**kwargs)
            except KeyError:
                return message
        return message


def get_log_messages(language: LogLanguage = DEFAULT_LOG_LANGUAGE) -> LogMessages:
    """
    获取日志消息管理器实例
    
    Args:
        language (LogLanguage): 语言配置
        
    Returns:
        LogMessages: 日志消息管理器实例
    """
    return LogMessages(language)
