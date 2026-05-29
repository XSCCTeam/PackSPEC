"""
SPEC CPU 2017基准测试驱动模块

本模块实现了SPEC CPU 2017基准测试的具体驱动功能，继承自SPECDriver基类。
支持SPEC2017的speed和rate两种运行模式。

主要功能：
- 管理SPEC2017的基准测试列表(整数测试和浮点测试)
- 获取基准测试的构建和运行目录路径
- 获取基准测试的参考时间(SPEC2017参考时间映射较复杂)
- 获取二进制文件路径映射

SPEC2017基准测试组成：
- 整数测试(INT): 10个基准测试，如600.perlbench_s, 602.gcc_s等
- 浮点测试(FP): 10个基准测试，如603.bwaves_s, 607.cactuBSSN_s等

Note:
    SPEC2017的参考时间存储位置与SPEC2006不同，需要通过SPEC2017_REFTIME_MAP映射查找
"""

import os

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    ConfigError, FileOperationError, BenchmarkError,
    SPEC2017_PATH, SPEC2017_BENCH_PATH, SCRIPTS_PATH, logger
)
from .spec_driver import SPECDriver
from src.pack_spec.pack_utils import PackUtils, is_numeric
from typing import List, Dict


#########################################
# SPEC 2017 Configs
#########################################

SPEC2017_INT_SPEED_BENCHES = ["600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s", 
                  "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s", 
                  "648.exchange2_s", "657.xz_s"]
SPEC2017_FP_SPEED_BENCHES = ["603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s", "627.cam4_s",
                  "628.pop2_s", "638.imagick_s", "644.nab_s", "649.fotonik3d_s", "654.roms_s"]
SPEC2017_SPEED_BENCHES = SPEC2017_INT_SPEED_BENCHES + SPEC2017_FP_SPEED_BENCHES

SPEC2017_INT_RATE_BENCHES = ["500.perlbench_r", "502.gcc_r", "505.mcf_r", "520.omnetpp_r", 
                  "523.xalancbmk_r", "525.x264_r", "531.deepsjeng_r", "541.leela_r", 
                  "548.exchange2_r", "557.xz_r"]
SPEC2017_FP_RATE_BENCHES = ["503.bwaves_r", "507.cactuBSSN_r", "508.namd_r", "510.parest_r", 
                  "511.povray_r", "519.lbm_r", "521.wrf_r", "526.blender_r", "527.cam4_r",
                  "538.imagick_r", "544.nab_r", "549.fotonik3d_r", "554.roms_r"]
SPEC2017_RATE_BENCHES = SPEC2017_INT_RATE_BENCHES + SPEC2017_FP_RATE_BENCHES

SPEC2017_INT_BENCHES = SPEC2017_INT_SPEED_BENCHES
SPEC2017_FP_BENCHES = SPEC2017_FP_SPEED_BENCHES
SPEC2017_BENCHES = SPEC2017_SPEED_BENCHES

SPEC2017_BENCHES_BY_MODE = {
    SPECMode.speed: {
        "int": SPEC2017_INT_SPEED_BENCHES,
        "fp": SPEC2017_FP_SPEED_BENCHES,
        "all": SPEC2017_SPEED_BENCHES,
    },
    SPECMode.rate: {
        "int": SPEC2017_INT_RATE_BENCHES,
        "fp": SPEC2017_FP_RATE_BENCHES,
        "all": SPEC2017_RATE_BENCHES,
    },
}

SPEC2017_SPEED_BIN_MAP = {
    "600.perlbench_s": "perlbench_s", "602.gcc_s": "sgcc", "605.mcf_s": "mcf_s", 
    "620.omnetpp_s": "omnetpp_s", "623.xalancbmk_s": "xalancbmk_s", "625.x264_s": "x264_s", 
    "631.deepsjeng_s": "deepsjeng_s", "641.leela_s": "leela_s", "648.exchange2_s": "exchange2_s", 
    "657.xz_s": "xz_s",
    "603.bwaves_s": "speed_bwaves", "607.cactuBSSN_s": "cactuBSSN_s", "619.lbm_s": "lbm_s", 
    "621.wrf_s": "wrf_s", "627.cam4_s": "cam4_s", "628.pop2_s": "speed_pop2", 
    "638.imagick_s": "imagick_s", "644.nab_s": "nab_s", "649.fotonik3d_s": "fotonik3d_s", 
    "654.roms_s": "sroms"
}

SPEC2017_RATE_BIN_MAP = {
    "500.perlbench_r": "perlbench_r", "502.gcc_r": "cpugcc_r", "505.mcf_r": "mcf_r", 
    "520.omnetpp_r": "omnetpp_r", "523.xalancbmk_r": "cpuxalan_r", "525.x264_r": "x264_r", 
    "531.deepsjeng_r": "deepsjeng_r", "541.leela_r": "leela_r", "548.exchange2_r": "exchange2_r", 
    "557.xz_r": "xz_r",
    "503.bwaves_r": "bwaves_r", "507.cactuBSSN_r": "cactusBSSN_r", "508.namd_r": "namd_r", 
    "510.parest_r": "parest_r", "511.povray_r": "povray_r", "519.lbm_r": "lbm_r", 
    "521.wrf_r": "wrf_r", "526.blender_r": "blender_r", "527.cam4_r": "cam4_r",
    "538.imagick_r": "imagick_r", "544.nab_r": "nab_r", "549.fotonik3d_r": "fotonik3d_r", 
    "554.roms_r": "roms_r"
}

SPEC2017_BIN_MAP = SPEC2017_SPEED_BIN_MAP

SPEC2017_BIN_MAP_BY_MODE = {
    SPECMode.speed: SPEC2017_SPEED_BIN_MAP,
    SPECMode.rate: SPEC2017_RATE_BIN_MAP,
}

SPEC2017_SPEED_REFTIME_MAP = {
    # 映射格式: {bench_name: {input_type: [path_component1, path_component2, ...]}}
    # reftime文件路径 = SPEC2017_BENCH_PATH / path_component1 / path_component2 / ... / reftime
    # 例如 600.perlbench_s 的 ref reftime: SPEC2017_BENCH_PATH/500.perlbench_r/data/refrate/reftime
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

SPEC2017_RATE_REFTIME_MAP = {
    "500.perlbench_r": {"test": ["500.perlbench_r", "data", "test"], "train": ["500.perlbench_r", "data", "train"], "ref": ["500.perlbench_r", "data", "refrate"]},
    "502.gcc_r": {"test": ["502.gcc_r", "data", "test"], "train": ["502.gcc_r", "data", "train"], "ref": ["502.gcc_r", "data", "refrate"]},
    "505.mcf_r": {"test": ["505.mcf_r", "data", "test"], "train": ["505.mcf_r", "data", "train"], "ref": ["505.mcf_r", "data", "refrate"]},
    "520.omnetpp_r": {"test": ["520.omnetpp_r", "data", "test"], "train": ["520.omnetpp_r", "data", "train"], "ref": ["520.omnetpp_r", "data", "refrate"]},
    "523.xalancbmk_r": {"test": ["523.xalancbmk_r", "data", "test"], "train": ["523.xalancbmk_r", "data", "train"], "ref": ["523.xalancbmk_r", "data", "refrate"]},
    "525.x264_r": {"test": ["525.x264_r", "data", "test"], "train": ["525.x264_r", "data", "train"], "ref": ["525.x264_r", "data", "refrate"]},
    "531.deepsjeng_r": {"test": ["531.deepsjeng_r", "data", "test"], "train": ["531.deepsjeng_r", "data", "train"], "ref": ["531.deepsjeng_r", "data", "refrate"]},
    "541.leela_r": {"test": ["541.leela_r", "data", "test"], "train": ["541.leela_r", "data", "train"], "ref": ["541.leela_r", "data", "refrate"]},
    "548.exchange2_r": {"test": ["548.exchange2_r", "data", "test"], "train": ["548.exchange2_r", "data", "train"], "ref": ["548.exchange2_r", "data", "refrate"]},
    "557.xz_r": {"test": ["557.xz_r", "data", "test"], "train": ["557.xz_r", "data", "train"], "ref": ["557.xz_r", "data", "refrate"]},
    "503.bwaves_r": {"test": ["503.bwaves_r", "data", "test"], "train": ["503.bwaves_r", "data", "train"], "ref": ["503.bwaves_r", "data", "refrate"]},
    "507.cactuBSSN_r": {"test": ["507.cactuBSSN_r", "data", "test"], "train": ["507.cactuBSSN_r", "data", "train"], "ref": ["507.cactuBSSN_r", "data", "refrate"]},
    "508.namd_r": {"test": ["508.namd_r", "data", "test"], "train": ["508.namd_r", "data", "train"], "ref": ["508.namd_r", "data", "refrate"]},
    "510.parest_r": {"test": ["510.parest_r", "data", "test"], "train": ["510.parest_r", "data", "train"], "ref": ["510.parest_r", "data", "refrate"]},
    "511.povray_r": {"test": ["511.povray_r", "data", "test"], "train": ["511.povray_r", "data", "train"], "ref": ["511.povray_r", "data", "refrate"]},
    "519.lbm_r": {"test": ["519.lbm_r", "data", "test"], "train": ["519.lbm_r", "data", "train"], "ref": ["519.lbm_r", "data", "refrate"]},
    "521.wrf_r": {"test": ["521.wrf_r", "data", "test"], "train": ["521.wrf_r", "data", "train"], "ref": ["521.wrf_r", "data", "refrate"]},
    "526.blender_r": {"test": ["526.blender_r", "data", "test"], "train": ["526.blender_r", "data", "train"], "ref": ["526.blender_r", "data", "refrate"]},
    "527.cam4_r": {"test": ["527.cam4_r", "data", "test"], "train": ["527.cam4_r", "data", "train"], "ref": ["527.cam4_r", "data", "refrate"]},
    "538.imagick_r": {"test": ["538.imagick_r", "data", "test"], "train": ["538.imagick_r", "data", "train"], "ref": ["538.imagick_r", "data", "refrate"]},
    "544.nab_r": {"test": ["544.nab_r", "data", "test"], "train": ["544.nab_r", "data", "train"], "ref": ["544.nab_r", "data", "refrate"]},
    "549.fotonik3d_r": {"test": ["549.fotonik3d_r", "data", "test"], "train": ["549.fotonik3d_r", "data", "train"], "ref": ["549.fotonik3d_r", "data", "refrate"]},
    "554.roms_r": {"test": ["554.roms_r", "data", "test"], "train": ["554.roms_r", "data", "train"], "ref": ["554.roms_r", "data", "refrate"]},
}

SPEC2017_REFTIME_MAP = SPEC2017_SPEED_REFTIME_MAP

SPEC2017_REFTIME_MAP_BY_MODE = {
    SPECMode.speed: SPEC2017_SPEED_REFTIME_MAP,
    SPECMode.rate: SPEC2017_RATE_REFTIME_MAP,
}


class SPEC2017Driver(SPECDriver):
    """
    SPEC CPU 2017基准测试驱动类
    
    实现SPEC2017基准测试的具体操作，包括获取基准测试列表、
    获取参考时间、获取构建和运行目录路径等功能。
    
    继承自SPECDriver基类，实现了以下抽象方法：
    - get_bench_list(): 根据spec_benches字符串获取基准测试列表
    - get_ref_time(): 获取基准测试的参考时间
    - _get_bench_dir_prefix(): 获取基准测试目录前缀（SPEC2017特定格式）
    - get_binary_path_map(): 获取二进制文件路径映射
    
    Attributes:
        spec_bench_path (str): SPEC2017基准测试目录路径
        spec_bench_map (dict): 基准测试名称到二进制文件名的映射
        spec_build_dir (str): 构建目录名称，默认为'build'
        spec_run_dir (str): 运行目录名称，默认为'run'
        setup_script_path (str): setup脚本路径
        spec_bench_list (list): 选中的基准测试列表
        
    Note:
        SPEC2017与SPEC2006的主要区别：
        - 基准测试数量不同(20个 vs 29个)
        - 参考时间存储位置不同
        - 运行目录命名格式不同(ref模式下包含speed/rate)
    """

    _spec_name_key = "spec2017"
    """注册到驱动注册表的键，对应 SPECName.spec2017"""
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
        初始化SPEC2017Driver实例
        
        Args:
            spec_cfg_path (str): SPEC配置文件的绝对路径
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            spec_benches (str): 基准测试选择字符串，支持"all"/"int"/"intspeed"/"fp"/"fpspeed"或具体编号
            utils (PackUtils): 工具类实例
            iterations (int, optional): 测试迭代次数，默认3
            rebuild (bool, optional): 是否重新构建，默认False
            debug_mode (bool, optional): 是否调试模式，默认False
            allow_basepeak (bool, optional): 是否允许basepeak配置，默认False
        """
        super().__init__(spec_cfg_path, SPECName.spec2017, 
                        tune_type, input_type, spec_mode, 
                        spec_benches, utils, iterations, rebuild, debug_mode, allow_basepeak)
        if SPEC2017_PATH is None:
            logger.error(self.msg.get("spec_path_not_set"))
            raise ConfigError(self.msg.get("spec_path_not_set"))
        self.spec_dir = SPEC2017_PATH
        self.spec_bench_path = SPEC2017_BENCH_PATH
        self.spec_bench_map = SPEC2017_BIN_MAP_BY_MODE[self.spec_mode]
        self.spec_build_dir = 'build'
        self.spec_run_dir = 'run'
        self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec17.sh")
        self.spec_bench_list = self.get_bench_list()

    def get_bench_list(self) -> List[str]:
        """
        根据spec_benches字符串获取基准测试列表

        解析spec_benches字符串，根据当前spec_mode(speed/rate)选择对应的基准测试集合。
        支持以下格式：
        - "all": 选择所有基准测试
        - "int"/"intspeed"/"intrate": 选择所有整数基准测试
        - "fp"/"fpspeed"/"fprate": 选择所有浮点基准测试
        - "600 602": 选择指定编号的基准测试（空格分隔）

        Returns:
            list: 排序后的基准测试名称列表，整数测试在前，浮点测试在后

        Raises:
            BenchmarkError: 当没有选择到任何基准测试时抛出

        Note:
            - speed模式下，int/fp分别对应intspeed/fpspeed benchset
            - rate模式下，int/fp分别对应intrate/fprate benchset
            - 具体编号匹配时会遍历当前模式下的所有基准测试
        """
        spec_bench_set = set()
        spec_bench_list = []

        benches_by_mode = SPEC2017_BENCHES_BY_MODE[self.spec_mode]
        int_benches = benches_by_mode["int"]
        fp_benches = benches_by_mode["fp"]
        all_benches = benches_by_mode["all"]

        mode_aliases = {
            SPECMode.speed: {"int": ["int", "intspeed"], "fp": ["fp", "fpspeed"]},
            SPECMode.rate: {"int": ["int", "intrate"], "fp": ["fp", "fprate"]},
        }
        int_aliases = mode_aliases[self.spec_mode]["int"]
        fp_aliases = mode_aliases[self.spec_mode]["fp"]

        for bench in self.spec_benches.split():
            if bench == "all":
                spec_bench_set.update(all_benches) 
            elif bench in int_aliases:
                spec_bench_set.update(int_benches)
            elif bench in fp_aliases:
                spec_bench_set.update(fp_benches)
            else:
                for spec_bench in all_benches:
                    if bench == spec_bench.split('.')[0]:
                        spec_bench_set.add(spec_bench)
        spec_bench_list = sorted(spec_bench_set, 
            key=lambda x: (0 if x in int_benches else 1, 
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

        根据当前spec_mode从SPEC2017_REFTIME_MAP_BY_MODE中查找参考时间文件路径，
        读取并返回指定基准测试和输入类型的参考时间（以数字字符串形式返回）。

        SPEC2017的参考时间存储位置与SPEC2006不同，需要通过映射表
        SPEC2017_REFTIME_MAP_BY_MODE查找对应的data目录路径。

        Args:
            bench_name (str): 基准测试名称，如"600.perlbench_s"
            input_type (InputType): 输入数据集类型(test/train/ref)

        Returns:
            str: 参考时间字符串（数字），如"1234"

        Raises:
            FileOperationError: 当reftime文件不存在或内容格式无效时抛出
            FileOperationError: 当解析的参考时间不是有效数字时抛出

        Note:
            - ref模式下，reftime文件中的行格式为: ref{speed|rate} {n} {time}
            - test/train模式下，reftime文件中的行格式为: {test|train} {n} {time}
        """
        reftime_result = ""
        reftime_map = SPEC2017_REFTIME_MAP_BY_MODE[self.spec_mode]
        reftime_path = os.path.join(
            self.spec_bench_path, 
            os.path.sep.join(reftime_map[bench_name][input_type.name]),
            "reftime")

        try:
            logger.debug(self.msg.get("get_reftime_from", path=reftime_path, bench=bench_name, input_type=input_type.name))
            with open(reftime_path, 'r') as f:
                reftime = f.readlines()
                for reftime_line in reftime:
                    if input_type == InputType.ref:
                        if reftime_line.startswith(f"{input_type.name}{self.spec_mode.name}"):
                            reftime_result = reftime_line.split(" ")[2].strip()
                            break
                    else:
                        if reftime_line.startswith(f"{input_type.name}"):
                            reftime_result = reftime_line.split(" ")[2].strip()
                            break
            if reftime_result == "":
                logger.error(self.msg.get("get_reftime_failed", path=reftime_path))
                raise FileOperationError(self.msg.get("get_reftime_failed", path=reftime_path))
        except Exception as e:
            logger.error(self.msg.get("get_reftime_error", path=reftime_path, error=str(e)))
            raise FileOperationError(self.msg.get("get_reftime_error", path=reftime_path, error=str(e)))
            
        if not is_numeric(reftime_result):
            raise FileOperationError(
                f"Failed to get reftime from '{reftime_path}': "
                f"Expect a numeric but get '{reftime_result}'"
            )
        return reftime_result

    def _get_bench_dir_prefix(self, action_type: ActionType, tune_type: TuneType,
                              input_type: InputType, spec_mode: SPECMode) -> str:
        """
        获取基准测试目录前缀

        重写基类方法以提供SPEC2017特定的目录前缀格式。
        SPEC2017在ref输入类型时，运行目录前缀包含运行模式(speed/rate)。

        Args:
            action_type (ActionType): 动作类型(build/run)
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)

        Returns:
            str: 目录前缀字符串

        Note:
            - 构建目录前缀: build_{tune_type}_{label}
            - 运行目录前缀(ref): run_{tune_type}_{input_type}{spec_mode}_{label}
            - 运行目录前缀(非ref): run_{tune_type}_{input_type}_{label}
        """
        if action_type == ActionType.build:
            return f"{action_type.name}_{tune_type.name}_{self.label}"
        else:
            if input_type == InputType.ref:
                return f"{action_type.name}_{tune_type.name}_{input_type.name}{spec_mode.name}_{self.label}"
            else:
                return f"{action_type.name}_{tune_type.name}_{input_type.name}_{self.label}"

    def get_binary_path_map(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> Dict[str, str]:
        """
        获取基准测试二进制文件的路径映射
        
        根据构建目录获取各基准测试的二进制文件路径。
        
        Args:
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            
        Returns:
            dict: 基准测试名称到二进制文件路径的映射字典
                  格式: {bench_name: binary_path}
                  
        Example:
            >>> driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            {'600.perlbench_s': '/path/to/600.perlbench_s/build_base_label.0001/perlbench_s', ...}
        """
        bench_dirs = self.get_bench_path(ActionType.build, tune_type, input_type, spec_mode)
        binary_path_map = {}
        for bench_dir in bench_dirs:
            # Extract the benchmark name from the directory path
            # Path format: .../benchspec/CPU/{benchmark_name}/build/{build_dir}
            bench_name = os.path.basename(os.path.dirname(os.path.dirname(bench_dir)))
            # Only process actual benchmark directories that exist in our map
            if bench_name in self.spec_bench_map:
                binary_path_map[bench_name] = os.path.join(bench_dir, self.spec_bench_map[bench_name])
        return binary_path_map

    def _build_run_command(self) -> List[str]:
        """
        构建SPEC2017 runcpu命令
        
        根据配置构建runcpu命令及参数。
        runcpu是SPEC2017的测试运行命令。
        
        Returns:
            List[str]: runcpu命令及参数列表
            
        Note:
            命令格式: runcpu --config <cfg> --tune <tune> --size <size> 
                      --iterations <n> --noreportable <benches>
        """
        runcpu = os.path.join(self.spec_dir, "bin", "runcpu")
        
        cmd = [runcpu]
        
        cmd.extend(["--config", os.path.basename(self.spec_cfg_path)])
        
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
        
        logger.debug(self.msg.get("build_runcpu_cmd", cmd=' '.join(cmd)))
        return cmd