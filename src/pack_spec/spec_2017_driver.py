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

import sys
import os
import re

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    FileOperationError, BenchmarkError,
    SPEC2017_BENCH_PATH, SCRIPTS_PATH, logger
)
from .spec_driver import SPECDriver
from src.pack_spec.pack_utils import PackUtils, is_numeric
from typing import List, Dict, Tuple, Optional


#########################################
# SPEC 2017 Configs
#########################################

SPEC2017_INT_BENCHES = ["600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s", 
                  "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s", 
                  "648.exchange2_s", "657.xz_s"]
"""SPEC2017整数基准测试列表，共10个测试"""

SPEC2017_FP_BENCHES = ["603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s", "627.cam4_s",
                  "628.pop2_s", "638.imagick_s", "644.nab_s", "649.fotonik3d_s", "654.roms_s"]
"""SPEC2017浮点基准测试列表，共10个测试"""

SPEC2017_BENCHES = SPEC2017_INT_BENCHES + SPEC2017_FP_BENCHES
"""SPEC2017完整基准测试列表，共20个测试"""

SPEC2017_BIN_MAP = {
    # INT - 整数基准测试二进制文件名映射
    "600.perlbench_s": "perlbench_s", "602.gcc_s": "sgcc", "605.mcf_s": "mcf_s", 
    "620.omnetpp_s": "omnetpp_s", "623.xalancbmk_s": "xalancbmk_s", "625.x264_s": "x264_s", 
    "631.deepsjeng_s": "deepsjeng_s", "641.leela_s": "leela_s", "648.exchange2_s": "exchange2_s", 
    "657.xz_s": "xz_s",
    # FP - 浮点基准测试二进制文件名映射
    "603.bwaves_s": "speed_bwaves_s", "607.cactuBSSN_s": "cactuBSSN_s", "619.lbm_s": "lbm_s", 
    "621.wrf_s": "wrf_s", "627.cam4_s": "cam4_s", "628.pop2_s": "pop2_s", 
    "638.imagick_s": "imagick_s", "644.nab_s": "nab_s", "649.fotonik3d_s": "fotonik3d_s", 
    "654.roms_s": "roms_s"
}
"""SPEC2017基准测试名称到二进制文件名的映射字典"""

SPEC2017_REFTIME_MAP = {
    # INT SPEED - 整数speed测试参考时间映射
    # 格式: {bench_name: {input_type: [对应的rate测试名, "data", 目录名]}}
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
    # FP SPEED - 浮点speed测试参考时间映射
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
"""SPEC2017基准测试参考时间路径映射字典，用于定位reftime文件"""


class SPEC2017Driver(SPECDriver):
    """
    SPEC CPU 2017基准测试驱动类
    
    实现SPEC2017基准测试的具体操作，包括获取基准测试列表、
    获取参考时间、获取构建和运行目录路径等功能。
    
    继承自SPECDriver基类，实现了以下抽象方法：
    - get_bench_list(): 根据spec_benches字符串获取基准测试列表
    - get_ref_time(): 获取基准测试的参考时间
    - get_bench_path(): 获取基准测试的构建或运行目录
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
    def __init__(self, 
                 spec_cfg_path: str,
                 tune_type: TuneType, 
                 input_type: InputType, 
                 spec_mode: SPECMode,
                 spec_benches: str,
                 utils: PackUtils,
                 iterations: int = 3,
                 rebuild: bool = False,
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
        """
        super().__init__(spec_cfg_path, SPECName.spec2017, 
                        tune_type, input_type, spec_mode, 
                        spec_benches, utils, iterations, rebuild)
        self.spec_bench_path = SPEC2017_BENCH_PATH
        self.spec_bench_map = SPEC2017_BIN_MAP
        self.spec_build_dir = 'build'
        self.spec_run_dir = 'run'
        self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec17.sh")
        self.spec_bench_list = self.get_bench_list()

    def get_bench_list(self) -> List[str]:
        """
        根据spec_benches字符串获取基准测试列表
        
        解析spec_benches字符串，支持以下格式：
        - "all": 选择所有基准测试
        - "int" 或 "intspeed": 选择所有整数speed基准测试
        - "fp" 或 "fpspeed": 选择所有浮点speed基准测试
        - "600 602": 选择指定编号的基准测试
        
        Returns:
            list: 排序后的基准测试名称列表，整数测试在前，浮点测试在后
            
        Raises:
            BenchmarkError: 当没有选择到任何基准测试时抛出
        """
        spec_bench_set = set()
        spec_bench_list = []

        for bench in self.spec_benches.split():
            if bench == "all":
                spec_bench_set.update(SPEC2017_BENCHES) 
            elif bench in ["int", "intspeed"]:
                spec_bench_set.update(SPEC2017_INT_BENCHES)
            elif bench in ["fp", "fpspeed"]:
                spec_bench_set.update(SPEC2017_FP_BENCHES)
            else:
                for spec_bench in SPEC2017_BENCHES:
                    if bench == spec_bench.split('.')[0]:
                        spec_bench_set.add(spec_bench)
        spec_bench_list = sorted(spec_bench_set, 
            key=lambda x: (0 if x in SPEC2017_INT_BENCHES else 1, 
                x.split('.')[0]))

        if spec_bench_list == []:
            logger.error(f"No bench selected from {self.spec_benches} in {self.spec_name.name}.")
            raise BenchmarkError(f"No bench selected from {self.spec_benches} in {self.spec_name.name}.")
        else:
            logger.info(f"Selected {len(spec_bench_list)} benches from {self.spec_benches} in {self.spec_name.name}.")
            for spec_bench in spec_bench_list:
                logger.debug(f"Selected {spec_bench}.")
        return spec_bench_list
    
    def get_ref_time(self, bench_name: str, input_type: InputType) -> str:
        """
        获取基准测试的参考时间
        
        从SPEC2017的reftime文件中读取指定基准测试和输入类型的参考时间。
        SPEC2017的参考时间存储位置与SPEC2006不同，需要通过SPEC2017_REFTIME_MAP映射查找。
        
        Args:
            bench_name (str): 基准测试名称，如"600.perlbench_s"
            input_type (InputType): 输入数据集类型(test/train/ref)
            
        Returns:
            str: 参考时间字符串(数字)
            
        Raises:
            FileOperationError: 当无法读取参考时间文件时抛出
            AssertionError: 当参考时间不是有效数字时抛出
            
        Note:
            - SPEC2017的speed测试参考时间可能存储在对应的rate测试目录中
            - reftime文件中包含多行，需要根据input_type和spec_mode匹配正确的行
        """
        reftime_result = ""
        reftime_path = os.path.join(
            self.spec_bench_path, 
            os.path.sep.join(SPEC2017_REFTIME_MAP[bench_name][input_type.name]),
            "reftime")

        try:
            logger.debug(f"Get reftime {bench_name}.{input_type.name} from {reftime_path}.")
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
                logger.error(f"Failed to get reftime from '{reftime_path}'")
                raise FileOperationError(f"Failed to get reftime from '{reftime_path}'")
        except Exception as e:
            logger.error(f"Failed to get reftime from '{reftime_path}': {str(e)}")
            raise FileOperationError(f"Failed to get reftime from '{reftime_path}': {str(e)}")
            
        if not is_numeric(reftime_result):
            raise FileOperationError(
                f"Failed to get reftime from '{reftime_path}': "
                f"Expect a numeric but get '{reftime_result}'"
            )
        return reftime_result

    def get_bench_path(self, action_type: ActionType, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> List[str]:
        """
        获取基准测试的构建或运行目录路径列表
        
        根据动作类型、优化级别、输入类型等参数，查找并返回匹配的基准测试目录。
        目录命名格式遵循SPEC2017规范。
        
        Args:
            action_type (ActionType): 动作类型
                - ActionType.build: 获取构建目录
                - ActionType.run: 获取运行目录
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            
        Returns:
            list: 匹配的基准测试目录绝对路径列表
            
        Note:
            - 构建目录格式: build_{tune_type}_{label}.XXXX
            - 运行目录格式(ref): run_{tune_type}_{input_type}{spec_mode}_{label}.XXXX
            - 运行目录格式(非ref): run_{tune_type}_{input_type}_{label}.XXXX
            - 如果找到多个匹配目录，选择编号最大的(最新的)
        """
        if self.debug_mode:
            logger.debug(f"Get bench dir with:")
            logger.debug(f"  action_type: {action_type.name}")
            logger.debug(f"  tune_type: {tune_type.name}")
            logger.debug(f"  input_type: {input_type.name}")
            logger.debug(f"  spec_mode: {spec_mode.name}")

        if action_type == ActionType.build:
            bench_parent_dir = self.spec_build_dir
            # 构建目录格式：build_优化类型_标签
            bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{self.label}"
        elif action_type == ActionType.run:
            bench_parent_dir = self.spec_run_dir
            if self.spec_name == SPECName.spec2006:
                # 运行目录格式：run_优化类型_输入类型_标签
                bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}_{self.label}"
            elif self.spec_name == SPECName.spec2017:
                if input_type == InputType.ref:
                    # 运行目录格式：run_优化类型_输入类型+模式_标签
                    bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}{spec_mode.name}_{self.label}"
                else:
                    # 运行目录格式：run_优化类型_输入类型_标签
                    bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}_{self.label}"

        selected_bench_dir = []
        
        # 遍历SPEC2017基准测试目录
        for bench_dir in os.listdir(self.spec_bench_path):
            # 检查是否为指定的基准测试集合
            if bench_dir in self.spec_bench_list:
                # 根据动作类型构建完整路径（build或run目录）
                bench_run_dir = os.path.join(self.spec_bench_path, bench_dir, bench_parent_dir)
                if self.debug_mode:
                    logger.debug(f"Bench {bench_dir} run dir: {bench_run_dir}")
                    
                run_dir_path_list = []

                pattern = re.compile(rf"^{re.escape(bench_dir_perfix)}\.\d{{4}}$")
                
                # 判断 bench_run_dir 目录是否存在
                if not os.path.isdir(bench_run_dir):
                    logger.warning(f"Directory {bench_run_dir} not exist.")
                    continue

                # 查找符合前缀的目录
                for run_dir in os.listdir(bench_run_dir):
                    if pattern.match(run_dir):
                        run_dir_path_list.append(os.path.join(bench_run_dir, run_dir))
                        
                # 处理查找结果
                if len(run_dir_path_list) == 0:
                    # 未找到符合条件的目录
                    logger.warning(f"Bench {os.path.basename(bench_dir)} not found in {bench_dir_perfix}.")
                elif len(run_dir_path_list) > 1:
                    # 找到多个符合条件的目录，选择编号最大的那个（最新的）
                    logger.warning(f"Bench {os.path.basename(bench_dir)} found in more than one {bench_dir_perfix}.")
                    for run_dir_path in run_dir_path_list:
                        logger.debug(f"Found {run_dir_path}")
                    max = 0
                    selected = run_dir_path_list[0]
                    for run_dir_perfix in run_dir_path_list:
                        # 检查目录名末尾是否为数字，如果是则比较大小
                        if run_dir_perfix.split(".")[-1].isnumeric():
                            if int(run_dir_perfix.split(".")[-1]) > max:
                                max = int(run_dir_perfix.split(".")[-1])
                                selected = run_dir_perfix
                    selected_bench_dir.append(selected)
                    logger.warning(f"Bench {os.path.basename(bench_dir)} using {selected}")
                else:
                    # 只找到一个符合条件的目录
                    selected_bench_dir.append(run_dir_path_list[0])
                    logger.debug(f"Bench {os.path.basename(bench_dir)} using {run_dir_path_list[0]}")

        return selected_bench_dir

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
            # Path format: .../benchspec/CPU2017/{benchmark_name}/build/{build_dir}
            bench_name = os.path.basename(os.path.dirname(bench_dir))
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
        
        logger.debug(f"构建runcpu命令: {' '.join(cmd)}")
        return cmd