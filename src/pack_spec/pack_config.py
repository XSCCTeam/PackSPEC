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


P_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""项目根目录的绝对路径"""


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


DEFAULT_RUN_MODE = RunMode.pack
"""默认运行模式，默认为打包模式以保持向后兼容"""

DEFAULT_REPORT_FORMAT = "json"
"""默认报告格式，支持json和markdown"""

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

DEFAULT_HOST_MODE = False
"""默认是否HOST模式"""

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
