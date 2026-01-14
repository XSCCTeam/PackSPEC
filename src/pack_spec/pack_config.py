import os
from datetime import datetime
from loguru import logger
import sys
from enum import Enum

# 获取当前脚本所在目录的父目录的父目录的绝对路径
P_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#########################################
# Local Configs
#########################################
CURRENT_DATE = datetime.now().strftime("%y%m%d")
CURRENT_TIME = datetime.now().strftime("%y%m%d_%H%M%S")
HOME_PATH = os.path.expanduser("~")
LOGGER_PATH = os.path.join(P_PATH, "log", f"PackSpec_{CURRENT_TIME}.log")
# 配置 loguru 日志
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    LOGGER_PATH,
    level="DEBUG",
    rotation="8 MB",
)
PACK_PATH = os.path.join(P_PATH, "packed_files")
SCRIPTS_PATH = os.path.join(P_PATH, "scripts")
GENERATED_FILES_PATH = os.path.join(P_PATH, "generated_files")


#########################################
# PackSPEC Configs
#########################################

class ActionType(Enum):
    """
    SPEC基准测试动作类型枚举类
    
    定义SPEC基准测试的不同操作阶段类型
    
    Attributes:
        build (int): 构建阶段，对应值1
        run (int): 运行阶段，对应值2
    
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
        base (int): 基础优化级别，对应值1
        peak (int): 峰值优化级别，对应值2
    
    Note:
        base级别使用标准优化，peak级别使用更激进的优化策略
    """
    base = 1
    peak = 2
    all = 3

class InputType(Enum):
    """
    SPEC基准测试输入类型枚举类
    
    定义SPEC基准测试的不同输入数据集类型
    
    Attributes:
        test (int): 测试输入数据集，对应值1
        train (int): 训练输入数据集，对应值2
        ref (int): 参考输入数据集，对应值3
    
    Note:
        test数据集最小，用于快速验证；train数据集中等大小；ref数据集最大，用于正式测试
    """
    test = 1
    train = 2
    ref = 3
    all = 4

class SPECName(Enum):
    spec2006 = 1
    spec2006v1p01 = 2
    spec2017 = 3

class SPECSubBench(Enum):
    all = 1
    int = 2
    fp = 3

class SPECMode(Enum):
    speed = 1
    rate = 2

class PACKMode(Enum):
    bin = 1
    run = 2
    buildrun = 3

# 常量定义
DEFAULT_CORE_NUM = -1  # 默认不绑定核心
DEFAULT_ITERATIONS = 3  # 默认迭代次数
DEFAULT_CLOCK_RATE = 1.0  # 默认CPU主频，单位GHz
DEFAULT_DEBUG_MODE = False  # 默认调试模式
DEFAULT_REBUILD = True  # 默认重新构建
DEFAULT_PROFILE_GEN = False  # 默认不生成profile
DEFAULT_AUTO_MODE = False  # 默认非自动模式
DEFAULT_HOST_MODE = False  # 默认非HOST模式
RANDOM_SUFFIX_LENGTH = 4  # 随机后缀长度，用于目录命名


class PackSPECError(Exception):
    """
    PackSPEC工具的基础异常类
    
    所有PackSPEC相关的异常都应该继承自这个类
    
    Args:
        message (str): 异常消息
        code (int): 异常代码，默认为1
    """
    def __init__(self, message, code=1):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ConfigError(PackSPECError):
    """
    配置相关异常
    
    用于处理配置加载、验证等过程中的错误
    """
    pass


class FileOperationError(PackSPECError):
    """
    文件操作相关异常
    
    用于处理文件复制、创建、删除等操作中的错误
    """
    pass


class CommandExecutionError(PackSPECError):
    """
    命令执行相关异常
    
    用于处理外部命令执行过程中的错误
    """
    pass


class BenchmarkError(PackSPECError):
    """
    基准测试相关异常
    
    用于处理基准测试选择、运行等过程中的错误
    """
    pass

#########################################
# LLVM Configs
#########################################
DEFAULT_LLVM_PATH = os.getenv('DEFAULT_LLVM_PATH')
if DEFAULT_LLVM_PATH != None:
    DEFAULT_LLVM_PROFDATA_PATH = os.path.join(DEFAULT_LLVM_PATH, "bin", "llvm-profdata")
else:
    DEFAULT_LLVM_PROFDATA_PATH = None


#########################################
# DingDing rebot Configs
#########################################
# 参考：https://thoughts.aliyun.com/workspaces/66597cc824f406001b6ef466/docs/675b9751a7c8ff00016d92a2
BOSC_API_KEY = os.getenv('BOSC_API_KEY')
BOSC_AT_USER = os.getenv('BOSC_AT_USER')

#########################################
# SPEC Configs
#########################################
SPEC2006_PATH = os.getenv('SPEC2006_PATH')
if SPEC2006_PATH != None:
    SPEC2006_BENCH_PATH = os.path.join(SPEC2006_PATH, "benchspec", "CPU2006")
    SPEC2006_CONFIG_PATH = os.path.join(SPEC2006_PATH, "config")
else:
    SPEC2006_BENCH_PATH = None
    SPEC2006_CONFIG_PATH = None

SPEC2017_PATH = os.getenv('SPEC2017_PATH')
if SPEC2017_PATH != None:
    SPEC2017_BENCH_PATH = os.path.join(SPEC2017_PATH, "benchspec", "CPU2017")
    SPEC2017_CONFIG_PATH = os.path.join(SPEC2017_PATH, "config")
else:
    SPEC2017_BENCH_PATH = None
    SPEC2017_CONFIG_PATH = None
