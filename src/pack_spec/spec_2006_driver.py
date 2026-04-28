"""
SPEC CPU 2006基准测试驱动模块

本模块实现了SPEC CPU 2006基准测试的具体驱动功能，继承自SPECDriver基类。
支持SPEC2006 v1.2.0和v1.0.1两个版本。

主要功能：
- 管理SPEC2006的基准测试列表(整数测试和浮点测试)
- 获取基准测试的构建和运行目录路径
- 获取基准测试的参考时间
- 获取二进制文件路径映射

SPEC2006基准测试组成：
- 整数测试(INT): 12个基准测试，如400.perlbench, 401.bzip2等
- 浮点测试(FP): 17个基准测试，如410.bwaves, 416.gamess等
"""

import os

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, FileOperationError, BenchmarkError, ConfigError,
    SPEC2006_PATH, SPEC2006_BENCH_PATH, SCRIPTS_PATH, logger
)
from .spec_driver import SPECDriver
from src.pack_spec.pack_utils import PackUtils, is_numeric
from typing import List, Dict


#########################################
# SPEC 2006 Configs
#########################################

SPEC2006_INT_BENCHES = ["400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk", "456.hmmer",
                  "458.sjeng", "462.libquantum", "464.h264ref", "471.omnetpp", "473.astar", "483.xalancbmk"]
"""SPEC2006整数基准测试列表，共12个测试"""

SPEC2006_FP_BENCHES = ["410.bwaves", "416.gamess", "433.milc", "434.zeusmp", "435.gromacs", "436.cactusADM",
                  "437.leslie3d", "444.namd", "447.dealII", "450.soplex", "453.povray", "454.calculix",
                  "459.GemsFDTD", "465.tonto", "470.lbm", "481.wrf", "482.sphinx3"]
"""SPEC2006浮点基准测试列表，共17个测试"""

SPEC2006_BENCHES = SPEC2006_INT_BENCHES + SPEC2006_FP_BENCHES
"""SPEC2006完整基准测试列表，共29个测试"""

SPEC2006_BIN_MAP = {
    # INT - 整数基准测试二进制文件名映射
    "400.perlbench": "perlbench", "401.bzip2": "bzip2", "403.gcc": "gcc", "429.mcf": "mcf", 
    "445.gobmk": "gobmk", "456.hmmer": "hmmer", "458.sjeng": "sjeng", "462.libquantum": "libquantum", 
    "464.h264ref": "h264ref", "471.omnetpp": "omnetpp", "473.astar": "astar", "483.xalancbmk": "Xalan",
    # FP - 浮点基准测试二进制文件名映射
    "410.bwaves": "bwaves", "416.gamess": "gamess", "433.milc": "milc", "434.zeusmp": "zeusmp", 
    "435.gromacs": "gromacs", "436.cactusADM": "cactusADM", "437.leslie3d": "leslie3d", "444.namd": "namd", 
    "447.dealII": "dealII", "450.soplex": "soplex", "453.povray": "povray", "454.calculix": "calculix", 
    "459.GemsFDTD": "GemsFDTD", "465.tonto": "tonto", "470.lbm": "lbm", "481.wrf": "wrf", "482.sphinx3": "sphinx_livepretend"
}
"""SPEC2006基准测试名称到二进制文件名的映射字典"""

class SPEC2006Driver(SPECDriver):
    """
    SPEC CPU 2006基准测试驱动类
    
    实现SPEC2006基准测试的具体操作，包括获取基准测试列表、
    获取参考时间、获取构建和运行目录路径等功能。
    
    继承自SPECDriver基类，实现了以下抽象方法：
    - get_bench_list(): 根据spec_benches字符串获取基准测试列表
    - get_ref_time(): 获取基准测试的参考时间
    - get_binary_path_map(): 获取二进制文件路径映射
    
    Attributes:
        spec_dir (str): SPEC2006安装目录路径
        spec_bench_path (str): SPEC2006基准测试目录路径
        spec_bench_map (dict): 基准测试名称到二进制文件名的映射
        spec_build_dir (str): 构建目录名称，默认为'build'
        spec_run_dir (str): 运行目录名称，默认为'run'
        setup_script_path (str): setup脚本路径
        spec_bench_list (list): 选中的基准测试列表
    """

    _spec_name_key = "spec2006"
    """注册到驱动注册表的键，对应 SPECName.spec2006"""
    def __init__(self, 
                 spec_cfg_path: str,
                 tune_type: TuneType, 
                 input_type: InputType, 
                 spec_mode: SPECMode,
                 spec_benches: str,
                 utils: PackUtils,
                 iterations: int = 3,
                 rebuild: bool = False,
                 debug_mode: bool = False,
                 allow_basepeak: bool = False,
                 ):
        """
        初始化SPEC2006Driver实例
        
        Args:
            spec_cfg_path (str): SPEC配置文件的绝对路径
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            spec_benches (str): 基准测试选择字符串，支持"all"/"int"/"fp"或具体编号
            utils (PackUtils): 工具类实例
            iterations (int, optional): 测试迭代次数，默认3
            rebuild (bool, optional): 是否重新构建，默认False
            debug_mode (bool, optional): 是否调试模式，默认False
            allow_basepeak (bool, optional): 是否允许basepeak配置，默认False
        """
        super().__init__(spec_cfg_path, SPECName.spec2006, 
                        tune_type, input_type, spec_mode, 
                        spec_benches, utils, iterations, rebuild, debug_mode, allow_basepeak)
        if SPEC2006_PATH is None:
            logger.error(self.msg.get("spec_path_not_set"))
            raise ConfigError(self.msg.get("spec_path_not_set"))
        self.spec_dir = SPEC2006_PATH
        self.spec_bench_path = SPEC2006_BENCH_PATH
        self.spec_bench_map = SPEC2006_BIN_MAP
        self.spec_build_dir = 'build'
        self.spec_run_dir = 'run'
        self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec06.sh")
        self.spec_bench_list = self.get_bench_list()
    
    def get_bench_list(self) -> List[str]:
        """
        根据spec_benches字符串获取基准测试列表
        
        解析spec_benches字符串，支持以下格式：
        - "all": 选择所有基准测试
        - "int": 选择所有整数基准测试
        - "fp": 选择所有浮点基准测试
        - "400 401": 选择指定编号的基准测试
        
        Returns:
            list: 排序后的基准测试名称列表，整数测试在前，浮点测试在后
            
        Raises:
            BenchmarkError: 当没有选择到任何基准测试时抛出
            
        Example:
            >>> driver.get_bench_list()  # spec_benches="int"
            ['400.perlbench', '401.bzip2', ...]
        """
        spec_bench_set = set()
        spec_bench_list = []
        for bench in self.spec_benches.split():
            if bench == "all":
                spec_bench_set.update(SPEC2006_BENCHES) 
            elif bench == "int":
                spec_bench_set.update(SPEC2006_INT_BENCHES)
            elif bench == "fp":
                spec_bench_set.update(SPEC2006_FP_BENCHES)
            else:
                for spec_bench in SPEC2006_BENCHES:
                    if bench == spec_bench.split('.')[0]:
                        spec_bench_set.add(spec_bench)
        spec_bench_list = sorted(spec_bench_set, 
            key=lambda x: (0 if x in SPEC2006_INT_BENCHES else 1, 
                x.split('.')[0]))

        if spec_bench_list == []:
            logger.error(self.msg.get("no_bench_selected", benches=self.spec_benches, spec_name=self.spec_name.name))
            raise BenchmarkError(self.msg.get("no_bench_selected", benches=self.spec_benches, spec_name=self.spec_name.name))
        else:
            logger.info(self.msg.get("selected_benches", count=len(spec_bench_list), benches=self.spec_benches, spec_name=self.spec_name.name))
            for spec_bench in spec_bench_list:
                logger.debug(self.msg.get("selected_bench", bench=spec_bench))
        return spec_bench_list

    def get_ref_time(self, bench_name: str, input_type: InputType) -> str:
        """
        获取基准测试的参考时间
        
        从SPEC2006的reftime文件中读取指定基准测试和输入类型的参考时间。
        参考时间用于计算SPEC分数。
        
        Args:
            bench_name (str): 基准测试名称，如"400.perlbench"
            input_type (InputType): 输入数据集类型(test/train/ref)
            
        Returns:
            str: 参考时间字符串(数字)
            
        Raises:
            FileOperationError: 当无法读取参考时间文件时抛出
            FileOperationError: 当参考时间不是有效数字时抛出
            
        Note:
            reftime文件路径格式: {spec_bench_path}/{bench_name}/data/{input_type}/reftime
        """
        reftime_result = ""
        reftime_path = os.path.join(self.spec_bench_path, bench_name, "data", 
                                    input_type.name, "reftime")
        try:
            logger.debug(self.msg.get("get_reftime_from", path=reftime_path, bench=bench_name, input_type=input_type.name))
            with open(reftime_path, 'r') as f:
                reftime = f.readlines()
            reftime_result = reftime[1].strip()
        except Exception as e:
            logger.error(self.msg.get("get_reftime_error", path=reftime_path, error=str(e)))
            raise FileOperationError(self.msg.get("get_reftime_error", path=reftime_path, error=str(e)))

        if not is_numeric(reftime_result):
            raise FileOperationError(
                f"Failed to get reftime from '{reftime_path}': "
                f"Expect a numeric but get '{reftime_result}'"
            )
        return reftime_result

    def get_binary_path_map(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> Dict[str, str]:
        """
        获取基准测试二进制文件的路径映射
        
        从exe目录获取各基准测试的二进制文件路径。
        SPEC2006的二进制文件存放在exe目录，格式为: {binary_name}_{tune_type}.{label}
        
        Args:
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            
        Returns:
            dict: 基准测试名称到二进制文件路径的映射字典
                  格式: {bench_name: binary_path}
                  
        Example:
            >>> driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            {'400.perlbench': '/path/to/400.perlbench/exe/perlbench_base.x86_llvm19_novec_wll', ...}
        """
        binary_path_map = {}
        for bench_name in self.spec_bench_list:
            if bench_name not in self.spec_bench_map:
                continue
            binary_name = self.spec_bench_map[bench_name]
            exe_dir = os.path.join(self.spec_bench_path, bench_name, 'exe')
            if not os.path.isdir(exe_dir):
                logger.warning(self.msg.get("directory_not_exist", path=exe_dir))
                continue
            target_binary = f"{binary_name}_{tune_type.name}.{self.label}"
            binary_path = os.path.join(exe_dir, target_binary)
            if os.path.isfile(binary_path):
                binary_path_map[bench_name] = binary_path
            else:
                logger.warning(self.msg.get("binary_not_found", binary=target_binary, dir=exe_dir))
        return binary_path_map

    def _build_run_command(self) -> List[str]:
        """
        构建SPEC2006 runspec命令
        
        根据配置构建runspec命令及参数。
        runspec是SPEC2006的测试运行命令。
        
        Returns:
            List[str]: runspec命令及参数列表
            
        Note:
            命令格式: runspec --config <cfg> --tune <tune> --size <size> 
                      --iterations <n> --noreportable <benches>
        """
        runspec = os.path.join(self.spec_dir, "bin", "runspec")
        
        cmd = [runspec]
        
        cmd.extend(["--config", self.spec_cfg_path])
        
        if self.tune_type == TuneType.all:
            cmd.extend(["--tune", "base,peak"])
        else:
            cmd.extend(["--tune", self.tune_type.name])
        
        if self.input_type == InputType.all:
            cmd.extend(["--size", "test,train,ref"])
        else:
            cmd.extend(["--size", self.input_type.name])
        
        cmd.extend(["--iterations", str(self.iterations)])
        
        cmd.append("--noreportable")
        
        if self.spec_mode == SPECMode.rate:
            cmd.extend(["--rate", str(self.iterations)])
        
        cmd.extend(self.spec_bench_list)
        
        logger.debug(self.msg.get("build_runspec_cmd", cmd=' '.join(cmd)))
        return cmd


class SPEC2006V1P01Driver(SPEC2006Driver):
    """
    SPEC CPU 2006 v1.0.1版本驱动类
    
    继承自SPEC2006Driver，针对SPEC2006 v1.0.1版本的特殊处理。
    主要区别在于构建目录名称不同(v1.0.1使用'run'作为构建目录)。
    
    Note:
        该版本即将被废弃，建议使用v1.2.0版本的SPEC2006
    """

    _spec_name_key = "spec2006v1p01"
    """注册到驱动注册表的键，对应 SPECName.spec2006v1p01"""
    def __init__(self, 
                 spec_cfg_path: str,
                 tune_type: TuneType, 
                 input_type: InputType, 
                 spec_mode: SPECMode,
                 spec_benches: str,
                 utils: 'PackUtils',
                 iterations: int = 3,
                 rebuild: bool = False,
                 allow_basepeak: bool = False,
                 ):
        """
        初始化SPEC2006V1P01Driver实例
        
        Args:
            spec_cfg_path (str): SPEC配置文件的绝对路径
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            spec_benches (str): 基准测试选择字符串，支持"all"/"int"/"fp"或具体编号
            utils (PackUtils): 工具类实例
            iterations (int, optional): 测试迭代次数，默认3
            rebuild (bool, optional): 是否重新构建，默认False
            allow_basepeak (bool, optional): 是否允许basepeak配置，默认False
        """
        super().__init__(spec_cfg_path, tune_type, input_type, spec_mode, 
                         spec_benches, utils, iterations, rebuild, allow_basepeak=allow_basepeak)
        # TODO: 目前v1.0.1版本的SPEC2006打包即将被废弃
        self.spec_build_dir = 'run'