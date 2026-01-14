import sys
import os
import re

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pack_spec.pack_config import *
from .spec_driver import SPECDriver
from pack_spec.pack_utils import PackUtils

#########################################
# SPEC 2017 Configs
#########################################
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


class SPEC2017Driver(SPECDriver):
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
        super().__init__(spec_cfg_path, SPECName.spec2017, 
                        tune_type, input_type, spec_mode, 
                        spec_benches, utils, iterations, rebuild)
        self.spec_bench_path = SPEC2017_BENCH_PATH
        self.spec_bench_map = SPEC2017_BIN_MAP
        self.spec_build_dir = 'build'
        self.spec_run_dir = 'run'
        self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec17.sh")
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
            
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        assert is_number(reftime_result), f"Failed to get reftime from '{reftime_path}': Expect a numeric but get '{reftime_result}'"
        return reftime_result

    def get_bench_path(self, action_type: ActionType, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> list:
        """
        获取基准测试的构建或运行目录
        
        Args:
            spec_bench_list (list): 基准测试列表
            label (str): 配置标签
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

    def get_binary_path_map(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> dict:
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