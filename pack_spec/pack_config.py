import os
import datetime
from loguru import logger
import sys
from enum import Enum

# 获取当前脚本所在目录的父目录的绝对路径
P_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#########################################
# Local Configs
#########################################
CURRENT_DATE = datetime.datetime.now().strftime("%y%m%d")
HOME_PATH = os.path.expanduser("~")
LOGGER_PATH = os.path.join(P_PATH, "log", f"PackSpec_{CURRENT_DATE}.log")
# 配置 loguru 日志
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add(
    LOGGER_PATH,
    level="DEBUG",
    rotation="8 MB",
)
PACK_PATH = os.path.join(P_PATH, "packed_files")
SPEC_LOG_PATH = os.path.join(P_PATH, "spec_setup_logs")
SCRIPTS_PATH = os.path.join(P_PATH, "scripts")

#########################################
# SPEC Configs
#########################################
SPEC2006_INT_BENCHES = ["400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk", "456.hmmer",
                  "458.sjeng", "462.libquantum", "464.h264ref", "471.omnetpp", "473.astar", "483.xalancbmk"]
SPEC2006_FP_BENCHES = ["410.bwaves", "416.gamess", "433.milc", "434.zeusmp", "435.gromacs", "436.cactusADM",
                  "437.leslie3d", "444.namd", "447.dealII", "450.soplex", "453.povray", "454.calculix",
                  "459.GemsFDTD", "465.tonto", "470.lbm", "481.wrf", "482.sphinx3"]
SPEC2006_BENCHES = SPEC2006_INT_BENCHES + SPEC2006_FP_BENCHES
SPEC2006_BIN_MAP = {
    # INT
    "400.perlbench": "perlbench", "401.bzip2": "bzip2", "403.gcc": "gcc", "429.mcf": "mcf", 
    "445.gobmk": "gobmk", "456.hmmer": "hmmer", "458.sjeng": "sjeng", "462.libquantum": "libquantum", 
    "464.h264ref": "h264ref", "471.omnetpp": "omnetpp", "473.astar": "astar", "483.xalancbmk": "Xalan",
    # FP
    "410.bwaves": "bwaves", "416.gamess": "gamess", "433.milc": "milc", "434.zeusmp": "zeusmp", 
    "435.gromacs": "gromacs", "436.cactusADM": "cactusADM", "437.leslie3d": "leslie3d", "444.namd": "namd", 
    "447.dealII": "dealII", "450.soplex": "soplex", "453.povray": "povray", "454.calculix": "calculix", 
    "459.GemsFDTD": "GemsFDTD", "465.tonto": "tonto", "470.lbm": "lbm", "481.wrf": "wrf", "482.sphinx3": "sphinx_livepretend"
}

SPEC2017_INT_BENCHES = ["600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s", 
                  "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s", 
                  "648.exchange2_s", "657.xz_s"]
SPEC2017_FP_BENCHES = ["603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s", "627.cam4_s",
                  "628.pop2_s", "638.imagick_s", "644.nab_s", "649.fotonik3d_s", "654.roms_s"]
SPEC2017_BENCHES = SPEC2017_INT_BENCHES + SPEC2017_FP_BENCHES
SPEC2017_BIN_MAP = {
    # INT
    "600.perlbench_s": "perlbench_s", "602.gcc_s": "sgcc", "605.mcf_s": "mcf_s", 
    "620.omnetpp_s": "omnetpp_s", "623.xalancbmk_s": "xalancbmk_s", "625.x264_s": "x264_s", 
    "631.deepsjeng_s": "deepsjeng_s", "641.leela_s": "leela_s", "648.exchange2_s": "exchange2_s", 
    "657.xz_s": "xz_s",
    # FP
    "603.bwaves_s": "speed_bwaves_s", "607.cactuBSSN_s": "cactuBSSN_s", "619.lbm_s": "lbm_s", 
    "621.wrf_s": "wrf_s", "627.cam4_s": "cam4_s", "628.pop2_s": "pop2_s", 
    "638.imagick_s": "imagick_s", "644.nab_s": "nab_s", "649.fotonik3d_s": "fotonik3d_s", 
    "654.roms_s": "roms_s"
}
SPEC2017_REFTIME_MAP = {
    # INT SPEED
    "600.perlbench_s": {"test": ["500.perlbench_r", "data", "test"], "train": ["500.perlbench_r", "data", "train"], "ref": ["500.perlbench_r", "data", "refrate"]},
    "602.gcc_s": {"test": ["502.gcc_r", "data", "test"], "train": ["502.gcc_r", "data", "train"], "ref": ["502.gcc_r", "data", "refspeed"]}, 
    "605.mcf_s": {"test": ["505.mcf_r", "data", "test"], "train": ["505.mcf_r", "data", "train"], "ref": ["505.mcf_r", "data", "refspeed"]}, 
    "620.omnetpp_s": {"test": ["520.omnetpp_r", "data", "test"], "train": ["520.omnetpp_r", "data", "train"], "ref": ["520.omnetpp_r", "data", "refrate"]}, 
    "623.xalancbmk_s": {"test": ["523.xalancbmk_r", "data", "test"], "train": ["523.xalancbmk_r", "data", "train"], "ref": ["523.xalancbmk_r", "data", "refrate"]}, 
    "625.x264_s": {"test": ["525.x264_r", "data", "test"], "train": ["525.x264_r", "data", "train"], "ref": ["525.x264_r", "data", "refrate"]}, 
    "631.deepsjeng_s": {"test": ["631.deepsjeng_s", "data", "test"], "train": ["631.deepsjeng_s", "data", "train"], "ref": ["631.deepsjeng_s", "data", "refspeed"]}, 
    "641.leela_s": {"test": ["541.leela_r", "data", "test"], "train": ["541.leela_r", "data", "train"], "ref": ["541.leela_r", "data", "refrate"]}, 
    "648.exchange2_s": {"test": ["548.exchange2_r", "data", "test"], "train": ["548.exchange2_r", "data", "train"], "ref": ["548.exchange2_r", "data", "refrate"]}, 
    "657.xz_s": {"test": ["557.xz_r", "data", "test"], "train": ["557.xz_r", "data", "train"], "ref": ["557.xz_r", "data", "refspeed"]},
    # FP SPEED
    "603.bwaves_s": {"test": ["503.bwaves_r", "data", "test"], "train": ["503.bwaves_r", "data", "train"], "ref": ["503.bwaves_r", "data", "refspeed"]}, 
    "607.cactuBSSN_s": {"test": ["507.cactuBSSN_r", "data", "test"], "train": ["507.cactuBSSN_r", "data", "train"], "ref": ["507.cactuBSSN_r", "data", "refspeed"]}, 
    "619.lbm_s": {"test": ["619.lbm_s", "data", "test"], "train": ["619.lbm_s", "data", "train"], "ref": ["619.lbm_s", "data", "refspeed"]}, 
    "621.wrf_s": {"test": ["521.wrf_r", "data", "test"], "train": ["521.wrf_r", "data", "train"], "ref": ["521.wrf_r", "data", "refspeed"]}, 
    "627.cam4_s": {"test": ["527.cam4_r", "data", "test"], "train": ["527.cam4_r", "data", "train"], "ref": ["527.cam4_r", "data", "refspeed"]}, 
    "628.pop2_s": {"test": ["628.pop2_s", "data", "test"], "train": ["628.pop2_s", "data", "train"], "ref": ["628.pop2_s", "data", "refspeed"]}, 
    "638.imagick_s": {"test": ["538.imagick_r", "data", "test"], "train": ["538.imagick_r", "data", "train"], "ref": ["538.imagick_r", "data", "refspeed"]}, 
    "644.nab_s": {"test": ["544.nab_r", "data", "test"], "train": ["544.nab_r", "data", "train"], "ref": ["544.nab_r", "data", "refspeed"]}, 
    "649.fotonik3d_s": {"test": ["549.fotonik3d_r", "data", "test"], "train": ["549.fotonik3d_r", "data", "train"], "ref": ["549.fotonik3d_r", "data", "refspeed"]}, 
    "654.roms_s": {"test": ["554.roms_r", "data", "test"], "train": ["554.roms_r", "data", "train"], "ref": ["554.roms_r", "data", "refspeed"]}
}

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
    spec2006_v1_2 = 2
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
