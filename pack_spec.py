from config import *
from enum import Enum
import shutil
import os
import re
import subprocess

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
    spec2017 = 2

class SPECSubBench(Enum):
    all = 1
    int = 2
    fp = 3

class SPECMode(Enum):
    speed = 1
    rate = 2

def get_bench_dir(bench_name: str, bench_dirs: list) -> str:
    for bench_dir in bench_dirs:
        dir_bench_name = os.path.basename(
            os.path.dirname(
                os.path.dirname(bench_dir)))
        if dir_bench_name == bench_name:
            return bench_dir
    return ""

class PackSPEC:
    """
    SPEC基准测试二进制打包类
    
    用于查找和打包指定配置的SPEC基准测试二进制文件，支持SPEC2006和SPEC2017版本
    
    Attributes:
        spec_bench (SPECBench): SPEC基准测试类型枚举值
        tune_type (TuneType): 优化类型枚举值
        input_type (InputType): 输入类型枚举值
        iterations (int): 每个基准测试的运行迭代次数，默认为3
        test_core_num (int): 测试使用的核心编号
        spec_dir (str): SPEC安装目录路径
        spec_bench_map (dict): 基准测试名称到二进制文件名的映射
        spec_bench_path (str): 基准测试目录路径
        spec_benches (list): 当前基准测试集合列表
        spec_build_dir (str): 构建目录名称('run'或'build')
    
    Methods:
        get_bench_path: 获取指定配置的基准测试路径
        copy_binarys: 复制二进制文件到目标目录
        copy_benches: 复制完整的基准测试目录结构
        execute_specinvoke: 生成基准测试的运行脚本
        create_run_all_script: 创建运行所有基准测试的批处理脚本
        create_test_script: 创建单个基准测试的运行脚本
        set_bench_info: 设置基准测试相关信息
    """
    def __init__(self,
                 spec_name: SPECName, 
                 spec_benches: str,
                 tune_type: TuneType, 
                 input_type: InputType,
                 spec_mode: SPECMode,
                 iterations: int = 3,
                 test_core_num: int = -1,
                 test_clock_rate: float = 1,
                 rebuild: bool = True,
                 profile_gen: bool = False,
                 overwrite_check: bool = True,
                 ):
        self.spec_name = spec_name
        self.tune_type = tune_type
        self.input_type = input_type
        self.spec_mode = spec_mode
        self.iterations = iterations
        self.overwrite_check = overwrite_check
        self.test_core_num = test_core_num
        self.rebuild = rebuild
        self.test_clock_rate = test_clock_rate
        if self.spec_name == SPECName.spec2006:
            self.spec_dir = SPEC2006_PATH
            self.spec_bench_path = SPEC2006_BENCH_PATH
            self.spec_bench_map = SPEC2006_BIN_MAP
            self.spec_build_dir = 'run'
            self.spec_run_dir = 'run'
            self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec06.sh")
        elif self.spec_name == SPECName.spec2017:
            self.spec_dir = SPEC2017_PATH
            self.spec_bench_path = SPEC2017_BENCH_PATH
            self.spec_bench_map = SPEC2017_BIN_MAP
            self.spec_build_dir = 'build'
            self.spec_run_dir = 'run'
            self.setup_script_path = os.path.join(SCRIPTS_PATH, "setup-spec17.sh")
        self.spec_bench_list = self.get_bench_list(spec_benches)
        self.profile_gen = profile_gen
        if self.profile_gen: # profile 生成模式只跑一次程序
            self.iterations = 1

    def get_bench_list(self, spec_benches: str):
        """
        设置基准测试信息
        
        根据spec_bench设置基准测试列表
        """
        spec_bench_set = set()
        spec_bench_list = []
        if self.spec_name == SPECName.spec2006:
            for bench in spec_benches.split():
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
        elif self.spec_name == SPECName.spec2017:
            for bench in spec_benches.split():
                if bench == "all":
                    spec_bench_set.update(SPEC2017_BENCHES) 
                elif bench == "int":
                    spec_bench_set.update(SPEC2017_INT_BENCHES)
                elif bench == "fp":
                    spec_bench_set.update(SPEC2017_FP_BENCHES)
                else:
                    for spec_bench in SPEC2017_BENCHES:
                        if bench == spec_bench.split('.')[0]:
                            spec_bench_set.add(spec_bench)
            spec_bench_list = sorted(spec_bench_set, 
                key=lambda x: (0 if x in SPEC2017_INT_BENCHES else 1, 
                    x.split('.')[0]))

        if spec_bench_list == []:
            logger.error(f"No bench selected from {spec_benches} in {self.spec_name.name}.")
            exit(1)
        else:
            logger.info(f"Selected {len(spec_bench_list)} benches from {spec_benches} in {self.spec_name.name}.")
            for spec_bench in spec_bench_list:
                logger.debug(f"Selected {spec_bench}.")
        return spec_bench_list

    def get_ref_time(self, bench_name: str, input_type: InputType):
        reftime_result = ""
        if self.spec_name == SPECName.spec2006:
            reftime_path = os.path.join(self.spec_bench_path, bench_name, "data", 
                                        input_type.name, "reftime")
            try:
                logger.debug(f"Get reftime {bench_name}.{input_type.name} from {reftime_path}.")
                with open(reftime_path, 'r') as f:
                    reftime = f.readlines()
                reftime_result = reftime[1].strip()
            except Exception as e:
                logger.error(f"Failed to get reftime from '{reftime_path}': {str(e)}")
                exit(1)
        elif self.spec_name == SPECName.spec2017:
            reftime_path = os.path.join(
                self.spec_bench_path, 
                os.path.sep.join(SPEC2017_REFTIME_MAP[bench_name][input_type.name]),
                "reftime")
            try:
                logger.debug(f"Get reftime {bench_name}.{input_type.name} from {reftime_path}.")
                with open(reftime_path, 'r') as f:
                    reftime = f.readlines()
                    for reftime_line in reftime:
                        if reftime_line.startswith(f"{input_type.name}{self.spec_mode.name}"):
                            reftime_result = reftime_line.split(" ")[2].strip()
                            break
                if reftime_result == "":
                    logger.error(f"Failed to get reftime from '{reftime_path}'")
                    exit(1)
            except Exception as e:
                logger.error(f"Failed to get reftime from '{reftime_path}': {str(e)}")
                exit(1)
        assert reftime_result.isnumeric(), f"Failed to get reftime from '{reftime_path}': Expect a numeric but get '{reftime_result}'"
        return reftime_result

    def get_spec_log(self, spec_log_file):
        marked_line = f"The log for this run is in {self.spec_dir}"
        try:
            with open(spec_log_file, "r") as f:
                spec_log = f.readlines()
            for spec_log_line in spec_log:
                if spec_log_line.startswith(marked_line):
                    logger.debug(f"Find spec log from '{spec_log_file}'")
                    return spec_log_line.replace("The log for this run is in ", "").strip()
        except Exception as e:
            logger.debug(f"Failed find spec log from '{spec_log_file}': {str(e)}")
            return ""

    def get_bench_path(self, label: str, action_type: ActionType, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> list:

        """
        获取指定配置的基准测试路径
        
        根据构建标签和动作类型查找匹配的基准测试目录路径。对于SPEC2017，
        会查找build目录；对于SPEC2006，会查找run目录。
        
        Args:
            label (str): 构建标签(如llvm19-m64)，用于匹配目录名称
            action_type (ActionType): 指定动作类型
        
        Returns:
            list: 返回匹配的基准测试路径列表，每个元素是一个基准测试的完整路径
            
        Note:
            1. 目录名称格式:
               - 构建目录: build_{优化类型}_{标签}
               - 运行目录: run_{优化类型}_{输入类型}_{标签}
            2. 对于多个匹配目录(如多次构建)，会选择编号最大的那个(最新的)
            3. 找不到匹配目录时会记录警告日志
            4. 返回的路径列表顺序与spec_benches列表顺序一致
        """

        if action_type == ActionType.build:
            bench_parent_dir = self.spec_build_dir
            # 构建目录格式：build_优化类型_标签
            bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{label}"
        elif action_type == ActionType.run:
            bench_parent_dir = self.spec_run_dir
            if self.spec_name == SPECName.spec2006:
                # 运行目录格式：run_优化类型_输入类型_标签
                bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}_{label}"
            elif self.spec_name == SPECName.spec2017:
                # 运行目录格式：run_优化类型_输入类型+模式_标签
                bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}{spec_mode.name}_{label}"

        selected_bench_dir = []
        
        # 遍历SPEC2017基准测试目录
        for bench_dir in os.listdir(self.spec_bench_path):
            # 检查是否为指定的基准测试集合
            if bench_dir in self.spec_bench_list:
                # 根据动作类型构建完整路径（build或run目录）
                bench_run_dir = os.path.join(self.spec_bench_path, bench_dir, bench_parent_dir)
                run_dir_path_list = []

                pattern = re.compile(rf"^{re.escape(bench_dir_perfix)}\.\d{{4}}$")
                
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
            else:
                # 不在指定的基准测试集合中，跳过
                logger.debug(f"bench_dir: {bench_dir} not included.")

        return selected_bench_dir

    def analyze_spec_config(self, spec_cfg: str):
        spec_cfg_path = os.path.join(self.spec_dir, "config", spec_cfg)
        label = ""
        try:
            with open(spec_cfg_path, 'r') as file:
                for line in file:
                    index = line.find('#')
                    if index != -1:
                        line = line[:index].strip()
                    if self.spec_name == SPECName.spec2006 and \
                            line.strip().startswith('ext') and \
                            '=' in line:
                        parts = line.split('=')
                        if parts[0].strip().startswith('ext'):
                            label = line.split("=")[1].strip()
                            break
                    elif self.spec_name == SPECName.spec2017 and \
                            line.strip().startswith('label') and \
                            '=' in line:
                        parts = line.split('=')
                        if parts[0].strip().startswith('label'):
                            label = line.split("=")[1].strip()
                            break

                for line in file:
                    if line.strip().startswith('basepeak') and 'yes' in line:
                        logger.warning(f"'basepeak' is set to yes in {spec_cfg_path}.")
                        logger.warning(f"Set 'basepeak' to yes means:")
                        logger.warning(
                            "\tUse base binary and/or base result for peak. "
                            "If applied to the whole suite (in the header section), "
                            "then only base is run, and its results are reported "
                            "for both the base and peak metrics. If applied to a "
                            "single benchmark, the same binary will be used for "
                            "both base and peak runs, and the median of the base "
                            "run will be reported for both. ———— SPEC2006 Docs"
                            "(https://www.spec.org/cpu2006/Docs/config.html#basepeak)"
                        )
                        choice = input(f"Are you sure you use it right? (y/n): ")
                        if choice.lower() == 'y':
                            logger.warning("Process continue with 'basepeak' setting.")
                        else:
                            logger.error("Aborted by user.")
                            exit(1)
                        
        except FileNotFoundError:
            logger.error(f"File {spec_cfg_path} not found.")
            exit(1)
        if self.spec_name == SPECName.spec2006:
            assert label != "", f"Ext not found in file {spec_cfg_path}."
        elif self.spec_name == SPECName.spec2017:
            assert label!= "", f"Label not found in file {spec_cfg_path}."
        return label

    def run_setup_spec(self, spec_cfg: str, tune_type: TuneType, input_type: InputType, rebuild: bool = True):
        if self.spec_name == SPECName.spec2006:
            selected_benches = f"{' '.join([x.split('.')[0] for x in self.spec_bench_list])}"

            spec_setup_cmd = [
                self.setup_script_path, 
                "-p", self.spec_dir,
                "-c", spec_cfg,
                "-t", tune_type.name,
                "-i", input_type.name,
                "-s", selected_benches,
                "-n", str(self.iterations)]
            if rebuild:
                spec_setup_cmd.append(
                    "-r"
                )
        elif self.spec_name == SPECName.spec2017:
            # TODO: 完善SPEC2017 setup 脚本
            spec_setup_cmd = f"{self.setup_script_path}"
            logger.error(f"The SPEC2017 setup script has not been implemented yet.")
            exit(1)

        try:
            # 执行run_setup_spec脚本并实时输出
            logger.info(f"Setting up spec from config: {spec_cfg}")
            logger.debug(f"Executing command: {spec_setup_cmd}")
            
            process = subprocess.Popen(
                spec_setup_cmd,
                cwd=P_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # 行缓冲
            )

            output_log = []
            # 实时读取输出
            while True:
                output = process.stdout
                if output is not None:
                    output = output.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        logger.info(output.strip())
                        output_log.append(output.strip())
            
            # 检查返回码
            return_code = process.wait()
            if return_code != 0:
                error = process.stderr
                if error is not None:
                    error = error.read()
                    logger.error(f"Command failed with error: {error}")
                    exit(1)

            logger.success(f"Successfully setup spec with {tune_type}_{input_type} from config: {spec_cfg}")
            spec_log_file = os.path.join(SPEC_LOG_PATH, f"{spec_cfg.replace('.cfg', '')}.{tune_type.name}_{input_type.name}.setuplog")
            os.makedirs(SPEC_LOG_PATH, exist_ok=True)
            with open(spec_log_file, "w") as f:
                f.write("\n".join(output_log))
            return spec_log_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e.stderr}")
            exit(1)
        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            exit(1)

    def copy_binarys(self, label: str, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode, dest_binary_dir: str = "") -> str:
        """
        复制二进制文件到目标目录
        
        将指定标签的SPEC基准测试二进制文件复制到目标目录，
        目标目录默认创建在PACK_PATH/bin_{label}下。
        
        Args:
            label (str): 构建标签(如llvm19-m64)
            dest_binary_dir (str, optional): 目标目录路径。如果为空字符串，
                                            会自动创建默认目录
        
        Returns:
            str: 返回最终使用的目标目录路径
            
        Note:
            1. 使用get_bench_path方法获取源基准测试目录
            2. 根据spec_bench选择不同的基准测试映射(spec_bench_map)
            3. 对于每个基准测试，尝试复制其二进制文件到目标目录
            4. 成功或失败都会记录相应日志
            5. 如果目标目录不存在会自动创建
            6. 返回的目标目录路径可用于后续操作
        """
        src_bench_dir = self.get_bench_path(label, ActionType.build, tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_binary_dir == "":
            if self.profile_gen:
                dest_binary_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_bin_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}_profilegen")
            else:
                dest_binary_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_bin_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}")
            if os.path.exists(dest_binary_dir):
                logger.info(f"Directory {dest_binary_dir} already exists.")
                if self.overwrite_check:
                    logger.debug(f"Do you want to overwrite it? (y/n): ")
                    choice = input(f"Do you want to overwrite it? (y/n): ")
                if self.overwrite_check == False or choice.lower() == 'y':
                    logger.debug(f"Overwriting directory {dest_binary_dir} ")
                    shutil.rmtree(dest_binary_dir)
                    os.makedirs(dest_binary_dir, exist_ok=False)
                else:
                    logger.error("User canceled the operation. Directory not overwritten.")
                    exit(1)
            else:
                logger.debug(f"Creating directory {dest_binary_dir} ")
                os.makedirs(dest_binary_dir, exist_ok=False)

        copy_num = 0
        for bench_dir in src_bench_dir:
            # 获取基准测试名称（目录的最后两级：如 500.perlbench_r/run_base_test_llvm19-m64）
            bench_name = os.path.basename(os.path.dirname(os.path.dirname(bench_dir)))
            binary_path = os.path.join(bench_dir, self.spec_bench_map[bench_name])
            dest_path = os.path.join(dest_binary_dir, bench_name)
            logger.info(f"Copying {bench_name}\n\tFrom {binary_path} -to-> {dest_path}")

            try:
                shutil.copy2(binary_path, dest_path)
                copy_num += 1
                logger.debug(f"Copie {bench_name} binary done.")
            except Exception as e:
                logger.error(f"Failed to copy {bench_name}: {str(e)}")
                exit(1)
        if copy_num != 0:
            logger.success(f"Successfully copied {copy_num} files.")
        else:
            logger.error(f"No binary to copy.")
            exit(1)
        return dest_binary_dir


    def copy_benches(self, label: str, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode, with_build: bool = False, dest_bench_dir: str = "") -> list:
        """
        复制完整的基准测试目录结构
        
        复制指定标签的SPEC基准测试完整目录结构到目标目录，
        包括构建目录和运行目录。
        
        Args:
            label (str): 构建标签(如llvm19-m64)
            dest_bench_dir (str, optional): 目标目录路径。如果为空字符串，
                                          会自动创建默认目录
        
        Returns:
            list: 返回成功复制的基准测试目录列表
            
        Raises:
            FileNotFoundError: 当源目录不存在时抛出异常
            OSError: 当复制过程中发生错误时抛出异常
        """
        if with_build:
            src_build_bench_dir = self.get_bench_path(label, ActionType.build, tune_type, input_type, spec_mode)
        src_run_bench_dir = self.get_bench_path(label, ActionType.run, tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_bench_dir == "":
            if with_build:
                if self.profile_gen:
                    dest_bench_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_buildrun_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}_profilegen")
                else:
                    dest_bench_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_buildrun_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}")
            else:
                if self.profile_gen:
                    dest_bench_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_run_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}_profilegen")
                else:
                    dest_bench_dir = os.path.join(PACK_PATH, f"{self.spec_name.name}_run_{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}")
            if os.path.exists(dest_bench_dir):
                logger.info(f"Directory {dest_bench_dir} already exists.")
                if self.overwrite_check:
                    logger.debug(f"Do you want to overwrite it? (y/n): ")
                    choice = input(f"Do you want to overwrite it? (y/n): ")
                if self.overwrite_check == False or choice.lower() == 'y':
                    logger.debug(f"Overwriting directory {dest_bench_dir} ")
                    shutil.rmtree(dest_bench_dir)
                    os.makedirs(dest_bench_dir, exist_ok=False)
                else:
                    logger.error("User canceled the operation. Directory not overwritten.")
                    exit(1)
            else:
                logger.debug(f"Creating directory {dest_bench_dir} ")
                os.makedirs(dest_bench_dir, exist_ok=False)

        dest_dir_list = []
        for bench_name in self.spec_bench_list:
            if with_build:
                src_build_dir = get_bench_dir(bench_name, src_build_bench_dir)
                if src_build_dir == "":
                    logger.warning(f"Cannot match '{bench_name}' from '{src_build_bench_dir}'")
                    continue
            src_run_dir = get_bench_dir(bench_name, src_run_bench_dir)
            if src_run_dir == "":
                logger.warning(f"Cannot match '{bench_name}' from '{src_run_bench_dir}'")
                continue
            dest_dir = os.path.join(dest_bench_dir, bench_name)

            logger.info(f"Copying {bench_name}\n")
            try:
                if with_build:
                    logger.info(f"\tFrom {src_build_dir} -to-> {dest_dir}")
                    shutil.copytree(src_build_dir, dest_dir, symlinks=True)
                    logger.debug(f"Copie {bench_name} build dir done.")
                logger.info(f"\tFrom {src_run_dir} -to-> {dest_dir}")
                shutil.copytree(src_run_dir, dest_dir, symlinks=True, dirs_exist_ok=True)
                logger.debug(f"Copie {bench_name} run dir done.")
                dest_dir_list.append(dest_dir)
            except Exception as e:
                logger.error(f"Failed to copy {bench_name}: {str(e)}")
                exit(1)

            if self.execute_specinvoke(src_run_dir, dest_dir, input_type):
                logger.success(f"Successfully generated run_{input_type.name}.sh in {dest_dir}")
            else:
                logger.error(f"Failed to generate run_test.sh in {dest_dir}")
                exit(1)

            self.create_test_script(label, bench_name, self.test_core_num, dest_dir, tune_type, input_type)

        if dest_dir_list != []:
            logger.success(f"Successfully copied {len(dest_dir_list)} benches.")
        else:
            logger.error(f"No benches to copy.")
            exit(1)
        return dest_dir_list

    def execute_specinvoke(self, src_dir: str, dest_dir: str, input_type: InputType) -> bool:
        """生成基准测试的运行脚本
        
        使用specinvoke命令生成运行脚本，并处理路径替换。
        
        Args:
            src_dir: 源基准测试目录
            dest_dir: 目标基准测试目录
            input_type: 输入类型
        
        Returns:
            bool: 是否成功生成运行脚本
        """
        specinvoke = os.path.join(self.spec_dir, "bin", "specinvoke")
        specinvoke_cmd = f"{specinvoke} -nn speccmds.cmd"

        src_dir_name = os.path.basename(src_dir)

        try:
            # 切换到目标目录
            logger.debug(f"Changing directory to {dest_dir}")
            
            # 执行specinvoke命令并捕获输出
            logger.debug(f"Executing command: {specinvoke_cmd}")
            result = subprocess.run(
                specinvoke_cmd.split(),
                cwd=dest_dir,
                capture_output=True,
                text=True,
                check=True
            )

            # 处理命令输出
            commands = result.stdout.split("\n")
            start_index = -1
            
            # 查找第一次出现"# Starting run"的行
            for i, line in enumerate(commands):
                if line.strip().startswith("# Starting run"):
                    start_index = i
                    break
            
            # 如果找到了起始行，只保留该行及其后面的内容
            if start_index != -1:
                commands = commands[start_index:]
            else:
                logger.warning("No '# Starting run' found in command output")

            # 替换路径和目录名
            processed_commands = []
            for line in commands:
                # 删除cd本目录命令
                line = line.replace(f"cd {src_dir}", "")
                # 替换完整路径
                line = line.replace(src_dir, ".")
                # 替换目录名
                line = line.replace(f"../{src_dir_name}/", f"./")
                if not line.startswith("specinvoke"):
                    processed_commands.append(line)
            
            # 将输出写入run.sh文件
            output_file = os.path.join(dest_dir, f"run_{input_type.name}.sh")
            with open(output_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("\n".join(processed_commands))  # 将处理后的命令写入文件
            
            # 添加执行权限
            os.chmod(output_file, 0o755)
            
            logger.success(f"Successfully created {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e.stderr}")
            exit(1)

        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            exit(1)

    def create_test_script(self, label: str, bench_name: str, core_num: int, 
                            dest_dir: str, tune_type: TuneType, input_type: InputType, iterations: int = 0):

        if iterations == 0:
            iterations = self.iterations

        run_test_script = os.path.join(dest_dir, f"test_{input_type.name}.sh")

        script_content = [
            "#!/bin/bash",
            "",
            # 检查 curl 是否安装
            "if ! command -v curl &> /dev/null",
            "then",
            "    echo \"ERROR! curl is not installed.\"",
            "    exit 1",
            "fi",
            "set -e",
            "",
        ]
        if self.profile_gen:
            script_content.extend([
                "# 生成profile文件避免覆盖",
                f"export LLVM_PROFILE_FILE=\"profiles/{bench_name}-%m-%p.profraw\"",
                ""
            ])
        script_content.extend([
            "# 获取脚本所在目录的绝对路径",
            "SCRIPT_DIR=$(pwd)",
            f"LOG_FILE=\"test_{input_type.name}.log\""
        ])
        if core_num != -1:
            script_content.append(
                f"CORE_NUM={core_num}"
            )
        script_content.extend([
            "",
            "ulimit -s unlimited",
            "",
        ])

        script_content.extend([
            f"chmod +x ./{self.spec_bench_map[bench_name]}_{tune_type.name}.{label}",
            ""
        ])

        script_content.extend([
            f"echo -e '\\nRunning {bench_name}...' | tee -a \"$LOG_FILE\"",
            f"echo -e 'Reftime: {self.get_ref_time(bench_name, input_type)}' | tee -a \"$LOG_FILE\""
            ])
        if core_num != -1:
            for i in range(iterations):
                script_content.extend([
                    f"# 执行第 {i+1} 次测试",
                    f"echo \"Test {bench_name} #{i+1}:\" | tee -a \"$LOG_FILE\"",
                    f"(time -p taskset -c $CORE_NUM bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
                ])
        else:
            for i in range(iterations):
                script_content.extend([
                    f"# 执行第 {i+1} 次测试",
                    f"echo \"Test {bench_name} #{i+1}:\" | tee -a \"$LOG_FILE\"",
                    f"(time -p bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
                ])
        script_content.extend([
            f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
            ""
        ])
        
        try:
            shutil.copy2(os.path.join(SCRIPTS_PATH, "cal_score.py"), dest_dir)
            logger.debug(f"Copie cal_score.py to {dest_dir}.")
        except Exception as e:
            logger.error(f"Failed to cal_score.py to {dest_dir}: {str(e)}")
            exit(1)
        
        try:
            shutil.copy2(os.path.join(SCRIPTS_PATH, "send_md_message.py"), dest_dir)
            logger.debug(f"Copie send_md_message.py to {dest_dir}.")
        except Exception as e:
            logger.error(f"Failed to send_md_message.py to {dest_dir}: {str(e)}")
            exit(1)

        if self.profile_gen:
            merge_profile_template = ""
            with open(os.path.join(SCRIPTS_PATH, "merge_profile.sh.template"), "r") as f:
                merge_profile_template = f.read()
            if DEFAULT_LLVM_PROFDATA_PATH != "":
                merge_profile_template = merge_profile_template.replace("<your llvm-profdata abspath>", DEFAULT_LLVM_PROFDATA_PATH)
            with open(os.path.join(dest_dir, "merge_profile.sh"), 'w') as f:
                f.write(merge_profile_template)
            os.chmod(os.path.join(dest_dir, "merge_profile.sh"), 0o700)

        if BOSC_API_KEY != None and BOSC_AT_USER != None:
            if self.profile_gen:
                script_content.extend([
                    f"HOST_NAME=$(hostname)",
                    f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                    f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                    f"     -H \"Content-Type: application/json\" \\",
                    f"     -d \"{{\\\"content\\\": \\\"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} Profile 生成完成喵！\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\\", \\\"at_user_ids\\\": [\\\"{BOSC_AT_USER}\\\"]}}\""
                ])
            else:
                script_content.extend([
                    f"HOST_NAME=$(hostname)",
                    f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                    f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                    f"     -H \"Content-Type: application/json\" \\",
                    f"     -d \"{{\\\"content\\\": \\\"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} 测试完成喵！\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\\", \\\"at_user_ids\\\": [\\\"{BOSC_AT_USER}\\\"]}}\"",
                    "",
                    f"chmod +x cal_score.py",
                    f"./cal_score.py $LOG_FILE {self.test_clock_rate} | tee score.txt",
                    f""
                ])
                title_message = f"{bench_name}.{label}.{tune_type.name}_{input_type.name} 测试结果"
                text_message = f"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} 测试结果喵："
                script_content.extend([
                    f"chmod +x send_md_message.py",
                    f"./send_md_message.py --api_key {BOSC_API_KEY} \\",
                    f"     --title \"{title_message}\" \\",
                    f"     --text \"{text_message}\" \\",
                    f"     --md_path \"score.txt\" \\",
                    f"     --at_mobiles \"{BOSC_AT_USER}\"",
                ])
        else:
            script_content.extend([
                f"chmod +x cal_score.py",
                f"./cal_score.py $LOG_FILE {self.test_clock_rate}"
            ])


        # 写入脚本文件
        with open(run_test_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_test_script, 0o700)
        logger.info(f"Created test_{input_type.name}.sh script at {run_test_script}")
        

    def create_run_all_script(self, label: str, core_num: int, buildrun_bench_dir_list: list, tune_type: TuneType, input_type: InputType, iterations: int = 0):
        """创建运行所有基准测试的批处理脚本
        
        生成一个shell脚本，用于按顺序运行所有基准测试并记录运行时间。
        脚本会记录每个基准测试的开始时间、结束时间和运行时长，
        所有输出都会被记录到run_all.log文件中。
        
        Args:
            buildrun_bench_dir_list: 打包后的基准测试目录列表
            input_type: 输入类型，用于确定运行哪个脚本（如run_test.sh）
        """
        if not buildrun_bench_dir_list:
            logger.warning("No benchmark directories to run")
            return
            
        if iterations == 0:
            iterations = self.iterations

        # 获取父目录
        parent_dir = os.path.dirname(buildrun_bench_dir_list[0])
        run_all_script = os.path.join(parent_dir, "run_all.sh")
        
        script_content = [
            "#!/bin/bash",
            "",
            # 检查 curl 是否安装
            "if ! command -v curl &> /dev/null",
            "then",
            "    echo \"ERROR! curl is not installed.\"",
            "    exit 1",
            "fi",
            "set -e",
            "",
            "",
            "# 获取脚本所在目录的绝对路径",
            "SCRIPT_DIR=$(pwd)",
            "LOG_FILE=\"$SCRIPT_DIR/run_all.log\""
        ]
        if core_num!= -1:
            script_content.append(
                f"CORE_NUM={core_num}"
            )
        script_content.extend([
            "",
            "# 运行所有基准测试并记录时间",
            "echo \"Starting benchmarks run at $(date)\" | tee -a \"$LOG_FILE\"",
            "",
            "ulimit -s unlimited",
            "",
            "# 运行每个基准测试",
        ])
        
        for bench_dir in buildrun_bench_dir_list:
            bench_name = os.path.basename(bench_dir)
            
            script_content.extend([
                f"echo -e '\\nRunning {bench_name}...' | tee -a \"$LOG_FILE\"",
                f"echo -e 'Reftime: {self.get_ref_time(bench_name, input_type)}' | tee -a \"$LOG_FILE\"",
                f"cd {bench_name}"
            ])
            if self.profile_gen:
                script_content.extend([
                    "# 生成profile文件避免覆盖",
                    f"export LLVM_PROFILE_FILE=\"profiles/{bench_name}-%m-%p.profraw\"",
                ])
            script_content.extend([
                f"chmod +x ./{self.spec_bench_map[bench_name]}_{tune_type.name}.{label}",
            ])
            if core_num!= -1:
                for i in range(iterations):
                    script_content.extend([
                        f"# 执行第{i+1}次测试",
                        f"echo \"Test {bench_name} #{i+1}:\" | tee -a \"$LOG_FILE\"",
                        f"(time -p taskset -c $CORE_NUM bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
                        ])
            else:
                for i in range(iterations):
                    script_content.extend([
                        f"# 执行第{i+1}次测试",
                        f"echo \"Test {bench_name} #{i+1}:\" | tee -a \"$LOG_FILE\"",
                        f"(time -p bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
                        ])
            script_content.extend([
                f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
                "cd \"$SCRIPT_DIR\"",
                ""
            ])
        
        script_content.extend([
            "echo -e '\\nAll benchmarks completed' | tee -a \"$LOG_FILE\"",
            "echo \"Finished at $(date)\" | tee -a \"$LOG_FILE\""
        ])

        try:
            shutil.copy2(os.path.join(SCRIPTS_PATH, "cal_score.py"), parent_dir)
            logger.debug(f"Copie cal_score.py to {parent_dir}.")
        except Exception as e:
            logger.error(f"Failed to cal_score.py to {parent_dir}: {str(e)}")
            exit(1)

        try:
            shutil.copy2(os.path.join(SCRIPTS_PATH, "send_md_message.py"), parent_dir)
            logger.debug(f"Copie send_md_message.py to {parent_dir}.")
        except Exception as e:
            logger.error(f"Failed to send_md_message.py to {parent_dir}: {str(e)}")
            exit(1)

        if self.profile_gen:
            collect_profiles_template = ""
            with open(os.path.join(SCRIPTS_PATH, "collect_profiles.sh.template"), "r") as f:
                collect_profiles_template = f.read()
            if DEFAULT_LLVM_PROFDATA_PATH != "":
                collect_profiles_template = collect_profiles_template.replace("<your llvm-profdata abspath>", DEFAULT_LLVM_PROFDATA_PATH)
            with open(os.path.join(parent_dir, "collect_profiles.sh"), 'w') as f:
                f.write(collect_profiles_template)
            os.chmod(os.path.join(parent_dir, "collect_profiles.sh"), 0o700)

        if BOSC_API_KEY != None and BOSC_AT_USER != None:
            if self.profile_gen:
                script_content.extend([
                    f"chmod +x collect_profiles.sh",
                    f"./collect_profiles.sh",
                    f""
                ])
                script_content.extend([
                    f"HOST_NAME=$(hostname)",
                    f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                    f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                    f"     -H \"Content-Type: application/json\" \\",
                    f"     -d \"{{\\\"content\\\": \\\"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} Profile 生成完成喵！\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\\", \\\"at_user_ids\\\": [\\\"{BOSC_AT_USER}\\\"]}}\""
                ])
            else:
                script_content.extend([
                    f"HOST_NAME=$(hostname)",
                    f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                    f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                    f"     -H \"Content-Type: application/json\" \\",
                    f"     -d \"{{\\\"content\\\": \\\"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} 测试完成喵！\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\\", \\\"at_user_ids\\\": [\\\"{BOSC_AT_USER}\\\"]}}\"",
                    "",
                    f"chmod +x cal_score.py",
                    f"./cal_score.py $LOG_FILE {self.test_clock_rate} | tee score.txt",
                    f""
                ])
                title_message = f"{label}.{tune_type.name}_{input_type.name} 测试结果"
                text_message = f"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} 测试结果喵："
                script_content.extend([
                    f"chmod +x send_md_message.py",
                    f"./send_md_message.py --api_key {BOSC_API_KEY} \\",
                    f"     --title \"{title_message}\" \\",
                    f"     --text \"{text_message}\" \\",
                    f"     --md_path \"score.txt\" \\",
                    f"     --at_mobiles \"{BOSC_AT_USER}\"",
                ])
        else:
            if self.profile_gen:
                script_content.extend([
                    f"chmod +x collect_profiles.sh",
                    f"./collect_profiles.sh",
                    ""
                ])
            script_content.extend([
                f"chmod +x cal_score.py",
                f"./cal_score.py $LOG_FILE {self.test_clock_rate}"
            ])

        # 写入脚本文件
        with open(run_all_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_all_script, 0o700)
        logger.success(f"Successfully created run_all script at {run_all_script}")

    def setup_spec(self, spec_cfg: str):
        if self.tune_type == TuneType.all:
            if self.input_type == InputType.all:
                self.run_setup_spec(spec_cfg, TuneType.base, InputType.test, rebuild=self.rebuild)
                self.run_setup_spec(spec_cfg, TuneType.base, InputType.train, rebuild=False)
                self.run_setup_spec(spec_cfg, TuneType.base, InputType.ref, rebuild=False)
                self.run_setup_spec(spec_cfg, TuneType.peak, InputType.test, rebuild=self.rebuild)
                self.run_setup_spec(spec_cfg, TuneType.peak, InputType.train, rebuild=False)
                self.run_setup_spec(spec_cfg, TuneType.peak, InputType.ref, rebuild=False)
            else:
                self.run_setup_spec(spec_cfg, TuneType.base, self.input_type, rebuild=self.rebuild)
                self.run_setup_spec(spec_cfg, TuneType.peak, self.input_type, rebuild=self.rebuild)
        else:
            if self.input_type == InputType.all:
                self.run_setup_spec(spec_cfg, self.tune_type, InputType.test, rebuild=self.rebuild)
                self.run_setup_spec(spec_cfg, self.tune_type, InputType.train, rebuild=False)
                self.run_setup_spec(spec_cfg, self.tune_type, InputType.ref, rebuild=False)
            else:
                self.run_setup_spec(spec_cfg, self.tune_type, self.input_type, rebuild=self.rebuild)

    def pack_binarys(self, label: str) -> list:
        dest_binarys_dir_list = []
        if self.tune_type == TuneType.all:
            if self.input_type == InputType.all:
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.base, InputType.test, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.base, InputType.train, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.base, InputType.ref, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.peak, InputType.test, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.peak, InputType.train, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.peak, InputType.ref, self.spec_mode))
            else:
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.base, self.input_type, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, TuneType.peak, self.input_type, self.spec_mode))
        else:
            if self.input_type == InputType.all:
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, self.tune_type, InputType.test, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, self.tune_type, InputType.train, self.spec_mode))
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, self.tune_type, InputType.ref, self.spec_mode))
            else:
                dest_binarys_dir_list.append(
                    self.copy_binarys(label, self.tune_type, self.input_type, self.spec_mode))
        return dest_binarys_dir_list
    
    def pack_binarys_cfg(self, spec_cfg: str):
        label = self.analyze_spec_config(spec_cfg)
        dest_binarys_dir_list = self.pack_binarys(label)
        spec_cfg_path = os.path.join(self.spec_dir, "config", spec_cfg)
        for dest_binarys_dir in dest_binarys_dir_list:
            try:
                logger.info(f"Copy spec config from {spec_cfg_path} to {dest_binarys_dir}.")
                shutil.copy2(spec_cfg_path, dest_binarys_dir)
            except Exception as e:
                logger.error(f"Failed to copy spec config from {spec_cfg_path} to {dest_binarys_dir}: {str(e)}")
                exit(1)
            spec_cfg_name = spec_cfg.replace(".cfg", "")
            spec_log_name = f"{spec_cfg_name}.{self.tune_type.name}_{self.input_type.name}.setuplog"
            spec_log_path = os.path.join(SPEC_LOG_PATH, spec_log_name)
            try:
                logger.info(f"Copy spec_setup log from {spec_log_path} to {dest_binarys_dir}.")
                shutil.copy2(spec_log_path, dest_binarys_dir)
            except Exception as e:
                logger.debug(f"Failed to copy spec_setup log from {spec_log_path} to {dest_binarys_dir}: {str(e)}")
            spec_log = self.get_spec_log(spec_log_path)
            if spec_log != "":
                try:
                    logger.info(f"Copy spec log from {spec_log} to {dest_binarys_dir}.")
                    shutil.copy2(spec_log, dest_binarys_dir)
                except Exception as e:
                    logger.debug(f"Failed to copy spec log from {spec_log} to {dest_binarys_dir}: {str(e)}")
            else:
                logger.debug(f"Not find spec log from {spec_log}.")


    def pack_benches(self, label: str, with_build=False) -> list:
        dest_benches_dir_list = []
        if self.tune_type == TuneType.all:
            if self.input_type == InputType.all:
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.base, InputType.test, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.base, InputType.test)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.base, InputType.train, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.base, InputType.train)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.base, InputType.ref, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.base, InputType.ref)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.peak, InputType.test, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.peak, InputType.test)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.peak, InputType.train, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.peak, InputType.train)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.peak, InputType.ref, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.peak, InputType.ref)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
            else:
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.base, self.input_type, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.base, self.input_type)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, TuneType.peak, self.input_type, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, TuneType.peak, self.input_type)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
        else:
            if self.input_type == InputType.all:
                buildrun_bench_dir_list = self.copy_benches(label, self.tune_type, InputType.test, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, self.tune_type, InputType.test)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, self.tune_type, InputType.train, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, self.tune_type, InputType.train)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
                buildrun_bench_dir_list = self.copy_benches(label, self.tune_type, InputType.ref, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, self.tune_type, InputType.ref)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
            else:
                buildrun_bench_dir_list = self.copy_benches(label, self.tune_type, self.input_type, self.spec_mode, with_build)
                self.create_run_all_script(label, self.test_core_num, buildrun_bench_dir_list, self.tune_type, self.input_type)
                dest_benches_dir_list.append(os.path.dirname(buildrun_bench_dir_list[0]))
        return dest_benches_dir_list

    def pack_benches_cfg(self, spec_cfg: str, with_build=False):
        label = self.analyze_spec_config(spec_cfg)
        buildrun_bench_dir_list = self.pack_benches(label, with_build)
        spec_cfg_path = os.path.join(self.spec_dir, "config", spec_cfg)
        for buildrun_bench_dir in buildrun_bench_dir_list:
            try:
                logger.info(f"Copy spec config from {spec_cfg_path} to {buildrun_bench_dir}.")
                shutil.copy2(spec_cfg_path, buildrun_bench_dir)
            except Exception as e:
                logger.error(f"Failed to copy spec config from {spec_cfg_path} to {buildrun_bench_dir}: {str(e)}")
                exit(1)
            spec_cfg_name = spec_cfg.replace(".cfg", "")
            spec_log_name = f"{spec_cfg_name}.{self.tune_type.name}_{self.input_type.name}.setuplog"
            spec_log_path = os.path.join(SPEC_LOG_PATH, spec_log_name)
            try:
                logger.info(f"Copy spec_setup log from {spec_log_path} to {buildrun_bench_dir}.")
                shutil.copy2(spec_log_path, buildrun_bench_dir)
            except Exception as e:
                logger.debug(f"Failed to copy spec_setup log from {spec_log_path} to {buildrun_bench_dir}: {str(e)}")
            spec_log = self.get_spec_log(spec_log_path)
            if spec_log != "":
                try:
                    logger.info(f"Copy spec log from {spec_log} to {buildrun_bench_dir}.")
                    shutil.copy2(spec_log, buildrun_bench_dir)
                except Exception as e:
                    logger.debug(f"Failed to copy spec log from {spec_log} to {buildrun_bench_dir}: {str(e)}")
            else:
                logger.debug(f"Not find spec log from {spec_log}.")

if __name__ == "__main__":
    # packer = PackSPEC(
    #     spec_name=SPECName.spec2006,
    #     spec_benches="int",
    #     tune_type=TuneType.base,
    #     input_type=InputType.test,
    #     iterations=3,
    #     test_core_num=4
    # )
    # packer.get_ref_time("400.perlbench", InputType.test)
    # packer.get_spec_log("/home/wll/PackSPEC/spec_logs/x86_llvm19_novec_wll.base_ref")
    print(os.path.join(HOME_PATH, os.path.sep.join(SPEC2017_REFTIME_MAP["600.perlbench_s"]["test"])))
