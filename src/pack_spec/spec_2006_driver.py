import sys
import os
import re

from src.pack_spec.pack_config import *
from .spec_driver import SPECDriver
from src.pack_spec.pack_utils import PackUtils


#########################################
# SPEC 2006 Configs
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

if SPEC2006_PATH == None:
    logger.error("SPEC2006_PATH is not set")
    exit(1)


class SPEC2006Driver(SPECDriver):
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
                 ):
        super().__init__(spec_cfg_path, SPECName.spec2006, 
                        tune_type, input_type, spec_mode, 
                        spec_benches, utils, iterations, rebuild, debug_mode)
        self.spec_dir = SPEC2006_PATH
        self.spec_bench_path = SPEC2006_BENCH_PATH
        self.spec_bench_map = SPEC2006_BIN_MAP
        self.spec_build_dir = 'build'
        self.spec_run_dir = 'run'
        self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec06.sh")
        self.spec_bench_list = self.get_bench_list()
    
    def get_bench_list(self):
        """
        根据spec_benches字符串获取基准测试列表
            
        Returns:
            list: 基准测试列表
            
        Raises:
            BenchmarkError: 当没有选择到任何基准测试时抛出
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
        
        Args:
            bench_name (str): 基准测试名称
            input_type (InputType): 输入数据集类型
            
        Returns:
            str: 参考时间字符串
            
        Raises:
            FileOperationError: 当无法读取参考时间文件时抛出
            AssertionError: 当参考时间不是数字时抛出
        """
        reftime_result = ""
        reftime_path = os.path.join(self.spec_bench_path, bench_name, "data", 
                                    input_type.name, "reftime")
        try:
            logger.debug(f"Get reftime {bench_name}.{input_type.name} from {reftime_path}.")
            with open(reftime_path, 'r') as f:
                reftime = f.readlines()
            reftime_result = reftime[1].strip()
        except Exception as e:
            logger.error(f"Failed to get reftime from '{reftime_path}': {str(e)}")
            raise FileOperationError(f"Failed to get reftime from '{reftime_path}': {str(e)}")

        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        assert is_number(reftime_result), f"Failed to get reftime from '{reftime_path}': Expect a numeric but get '{reftime_result}'"
        return reftime_result

    def get_bench_path(self, action_type: ActionType, tune_type: TuneType, 
                       input_type: InputType, spec_mode: SPECMode) -> list:
        """
        获取基准测试的构建或运行目录
        
        Args:
            action_type (ActionType): 动作类型（build或run）
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            spec_mode (SPECMode): 运行模式
            
        Returns:
            list: 基准测试目录列表
        """
        
        if self.debug_mode:
            logger.debug(f"Get bench dir with:")
            logger.debug(f"  action_type: {action_type.name}")
            logger.debug(f"  tune_type: {tune_type.name}")
            logger.debug(f"  input_type: {input_type.name}")
            logger.debug(f"  spec_mode: {spec_mode.name}")

        # 确保变量在所有情况下都有值
        if action_type == ActionType.build:
            bench_parent_dir = self.spec_build_dir
            # 构建目录格式：build_优化类型_标签
            bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{self.label}"
        elif action_type == ActionType.run:
            bench_parent_dir = self.spec_run_dir
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

    def get_binary_path_map(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> dict:
        bench_dirs = self.get_bench_path(ActionType.build, tune_type, input_type, spec_mode)
        binary_path_map = {}
        for bench_dir in bench_dirs:
            bench_name = os.path.basename(os.path.dirname(os.path.dirname(bench_dir)))
            if bench_name in self.spec_bench_map:
                binary_path_map[bench_name] = os.path.join(bench_dir, self.spec_bench_map[bench_name])
        return binary_path_map

class SPEC2006V1P01Driver(SPEC2006Driver):
    def __init__(self, 
                 spec_cfg_path: str,
                 tune_type: TuneType, 
                 input_type: InputType, 
                 spec_mode: SPECMode,
                 spec_benches: str,
                 utils: 'PackUtils',
                 iterations: int = 3,
                 rebuild: bool = False,
                 ):
        super().__init__(spec_cfg_path, tune_type, input_type, spec_mode, 
                         spec_benches, utils, iterations, rebuild)
        # TODO: 目前v1.0.1版本的SPEC2006打包即将被废弃
        self.spec_build_dir = 'run'