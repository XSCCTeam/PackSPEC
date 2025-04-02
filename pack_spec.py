from config import *
from enum import Enum
import shutil
import os
import subprocess

class ActionType(Enum):
    """
    SPEC基准测试动作类型枚举类
    
    定义SPEC基准测试的不同操作阶段类型
    
    Attributes:
        none (int): 未定义动作类型，默认值0
        build (int): 构建阶段，对应值1
        run (int): 运行阶段，对应值2
    
    Note:
        用于指定SPEC基准测试的执行阶段，build阶段编译测试程序，run阶段运行测试程序
    """
    none = 0
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

class SPECBench(Enum):
    """
    SPEC基准测试套件枚举类
    
    定义不同版本的SPEC基准测试套件及其子集
    
    Attributes:
        spec2006 (int): SPEC2006完整基准套件，对应值1
        spec2006int (int): SPEC2006整数基准子集，对应值2
        spec2006fp (int): SPEC2006浮点基准子集，对应值3
        spec2017 (int): SPEC2017完整基准套件，对应值4
        spec2017int (int): SPEC2017整数基准子集，对应值5
        spec2017fp (int): SPEC2017浮点基准子集，对应值6
    """
    spec2006 = 1
    spec2006int = 2
    spec2006fp = 3
    spec2017 = 4
    spec2017int = 5
    spec2017fp = 6


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
        action_type (ActionType): 动作类型枚举值(构建/运行)
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
                 spec_bench: SPECBench, 
                 action_type: ActionType, 
                 tune_type: TuneType, 
                 input_type: InputType,
                 iterations: int = 3,
                 test_core_num: int = 4):
        self.spec_bench = spec_bench
        self.action_type = action_type
        self.tune_type = tune_type
        self.input_type = input_type
        self.iterations = iterations
        self.test_core_num = test_core_num
        if self.spec_bench in [SPECBench.spec2006, SPECBench.spec2006int, SPECBench.spec2006fp]:
            self.spec_dir = SPEC2006_PATH
            self.spec_bench_map = SPEC2006_MAP
        elif self.spec_bench in [SPECBench.spec2017 ,SPECBench.spec2017int, SPECBench.spec2017fp]:
            self.spec_dir = SPEC2017_PATH
            self.spec_bench_map = SPEC2017_MAP
        else:
            logger.error(f"Unknown SPECBench Type: {self.spec_bench}")
            return
        self.set_bench_info()


    def set_bench_info(self):
        """
        设置基准测试信息
        
        根据spec_bench设置基准测试路径、基准测试列表和构建目录
        """
        if self.spec_bench == SPECBench.spec2006:
            self.spec_bench_path = SPEC2006_BENCH_PATH
            self.spec_benches = SPEC2006_BENCHES
            self.spec_build_dir = 'run'
        elif self.spec_bench == SPECBench.spec2006int:
            self.spec_bench_path = SPEC2006_BENCH_PATH
            self.spec_benches = SPEC2006_INT_BENCHES
            self.spec_build_dir = 'run'
        elif self.spec_bench == SPECBench.spec2006fp:
            self.spec_bench_path = SPEC2006_BENCH_PATH
            self.spec_benches = SPEC2006_FP_BENCHES
            self.spec_build_dir = 'run'
        elif self.spec_bench == SPECBench.spec2017:
            self.spec_bench_path = SPEC2017_BENCH_PATH
            self.spec_benches = SPEC2017_BENCHES
            self.spec_build_dir = 'build'
        elif self.spec_bench == SPECBench.spec2017int:
            self.spec_bench_path = SPEC2017_BENCH_PATH
            self.spec_benches = SPEC2017_INT_BENCHES
            self.spec_build_dir = 'build'
        elif self.spec_bench == SPECBench.spec2017fp:
            self.spec_bench_path = SPEC2017_BENCH_PATH
            self.spec_benches = SPEC2017_FP_BENCHES
            self.spec_build_dir = 'build'
    
    def get_bench_path(self, label: str, action_type: ActionType = ActionType.none) -> list:

        """
        获取指定配置的基准测试路径
        
        根据构建标签和动作类型查找匹配的基准测试目录路径。对于SPEC2017，
        会查找build目录；对于SPEC2006，会查找run目录。
        
        Args:
            label (str): 构建标签(如llvm19-m64)，用于匹配目录名称
            action_type (ActionType, optional): 指定动作类型，默认为ActionType.none
                                              None时会使用类初始化时设置的动作类型
        
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

        if action_type == ActionType.none:
            # 根据动作类型构建目录前缀
            if self.action_type == ActionType.build:
                # 编译目录格式：build_优化类型_标签
                bench_dir_perfix = f"{self.action_type.name}_{self.tune_type.name}_{label}"
            elif self.action_type == ActionType.run:
                # 运行目录格式：run_优化类型_输入类型_标签
                bench_dir_perfix = f"{self.action_type.name}_{self.tune_type.name}_{self.input_type.name}_{label}"
            else:
                logger.error(f"Unknown ActionType: {self.action_type}!")
                return []
        else:
            if action_type == ActionType.build:
                # 编译目录格式：build_优化类型_标签
                bench_dir_perfix = f"{action_type.name}_{self.tune_type.name}_{label}"
            elif action_type == ActionType.run:
                # 运行目录格式：run_优化类型_输入类型_标签
                bench_dir_perfix = f"{action_type.name}_{self.tune_type.name}_{self.input_type.name}_{label}"

        selected_bench_dir = []
        
        # 遍历SPEC2017基准测试目录
        for bench_dir in os.listdir(self.spec_bench_path):
            # 检查是否为指定的基准测试集合
            if bench_dir in self.spec_benches:
                # 根据动作类型构建完整路径（build或run目录）
                bench_run_dir = os.path.join(self.spec_bench_path, bench_dir, self.spec_build_dir)
                run_dir_path_list = []
                
                # 查找符合前缀的目录
                for run_dir in os.listdir(bench_run_dir):
                    if run_dir.startswith(bench_dir_perfix):
                        run_dir_path_list.append(os.path.join(bench_run_dir, run_dir))
                        
                # 处理查找结果
                if len(run_dir_path_list) == 0:
                    # 未找到符合条件的目录
                    logger.warning(f"Bench{os.path.basename(bench_dir)} not found in {bench_dir_perfix}.")
                elif len(run_dir_path_list) > 1:
                    # 找到多个符合条件的目录，选择编号最大的那个（最新的）
                    logger.warning(f"Bench{os.path.basename(bench_dir)} found in more than one {bench_dir_perfix}.")
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


    def copy_binarys(self, label: str, dest_binary_dir: str = "") -> str:
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
        src_bench_dir = self.get_bench_path(label)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_binary_dir == "":
            dest_binary_dir = os.path.join(PACK_PATH, f"bin_{label}")
            os.makedirs(dest_binary_dir, exist_ok=False)

        copy_num = 0
        for bench_dir in src_bench_dir:
            # 获取基准测试名称（目录的最后两级：如 500.perlbench_r/run_base_test_llvm19-m64）
            bench_name = os.path.basename(os.path.dirname(os.path.dirname(bench_dir)))
            binary_path = os.path.join(bench_dir, self.spec_bench_map[bench_name])
            if self.action_type == ActionType.run:
                binary_path = f"{binary_path}_{self.tune_type.name}.{label}"
            dest_path = os.path.join(dest_binary_dir, bench_name)
            logger.info(f"Copying {bench_name}\n\tFrom {binary_path} -to-> {dest_path}")

            try:
                shutil.copy2(binary_path, dest_path)
                copy_num += 1
                logger.debug(f"Copie {bench_name} binary done.")
            except Exception as e:
                logger.error(f"Failed to copy {bench_name}: {str(e)}")
                continue
        if copy_num != 0:
            logger.success(f"Successfully copied {copy_num} files.")
        else:
            logger.error(f"No binary to copy.")
        return dest_binary_dir


    def copy_benches(self, label: str, dest_bench_dir: str = "") -> list:
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

        src_build_bench_dir = self.get_bench_path(label, ActionType.build)
        src_run_bench_dir = self.get_bench_path(label, ActionType.run)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_bench_dir == "":
            dest_bench_dir = os.path.join(PACK_PATH, f"buildrun_{label}")
            os.makedirs(dest_bench_dir, exist_ok=False)

        dest_dir_list = []
        for bench_name in self.spec_benches:
            src_build_dir = get_bench_dir(bench_name, src_build_bench_dir)
            if src_build_dir == "":
                logger.warning(f"Cannot match '{bench_name}' from '{src_build_bench_dir}'")
                continue
            src_run_dir = get_bench_dir(bench_name, src_run_bench_dir)
            if src_run_dir == "":
                logger.warning(f"Cannot match '{bench_name}' from '{src_run_dir}'")
                continue
            dest_dir = os.path.join(dest_bench_dir, bench_name)

            logger.info(f"Copying {bench_name}\n")
            try:
                logger.info(f"\tFrom {src_build_dir} -to-> {dest_dir}")
                shutil.copytree(src_build_dir, dest_dir, symlinks=True)
                logger.debug(f"Copie {bench_name} build dir done.")
                logger.info(f"\tFrom {src_run_dir} -to-> {dest_dir}")
                shutil.copytree(src_run_dir, dest_dir, symlinks=True, dirs_exist_ok=True)
                logger.debug(f"Copie {bench_name} run dir done.")
                dest_dir_list.append(dest_dir)
            except Exception as e:
                logger.error(f"Failed to copy {bench_name}: {str(e)}")
                continue

            if self.execute_specinvoke(src_run_dir, dest_dir):
                logger.success(f"Successfully generated run_{self.input_type.name}.sh in {dest_dir}")
            else:
                logger.error(f"Failed to generate run_test.sh in {dest_dir}")

            self.create_test_script(label, bench_name, self.test_core_num, dest_dir)

        if dest_dir_list != []:
            logger.success(f"Successfully copied {len(dest_dir_list)} benches.")
        else:
            logger.error(f"No benches to copy.")
        return dest_dir_list

    def execute_specinvoke(self, src_dir: str, dest_dir: str) -> bool:
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
            output_file = os.path.join(dest_dir, f"run_{self.input_type.name}.sh")
            with open(output_file, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("\n".join(processed_commands))  # 将处理后的命令写入文件
            
            # 添加执行权限
            os.chmod(output_file, 0o755)
            
            logger.success(f"Successfully created {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            return False

    def create_test_script(self, label: str, bench_name: str, core_num: int, 
                            dest_dir: str, iterations: int = 0):

        if iterations == 0:
            iterations = self.iterations

        run_test_script = os.path.join(dest_dir, f"test_{self.input_type.name}.sh")

        script_content = [
            "#!/bin/bash",
            "",
            # 检查 curl 是否安装
            "if ! command -v curl &> /dev/null",
            "then",
            "    echo \"ERROR! curl is not installed.\"",
            "    exit 1",
            "fi",
            "set -x",
            "set -e",
            "",
            "# 获取脚本所在目录的绝对路径",
            "SCRIPT_DIR=$(pwd)",
            f"LOG_FILE=test_{self.input_type.name}.log\"",
            f"CORE_NUM={core_num}",
            "",
            "ulimit -s unlimited",
            "",
        ]

        for i in range(iterations):
            script_content.extend([
                f"echo \"Test {bench_name} {i} time:\" | tee -a \"$LOG_FILE\"",
                f"(time -p taskset -c $CORE_NUM bash run_{self.input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"",
                f"echo | tee -a \"$LOG_FILE\""
            ])

        if BOSC_API_KEY != "":
            script_content.extend([
                f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                f"     -H \"Content-Type: application/json\" \\",
                f"     -d '{{\"content\": \"{bench_name}.{label} 测试完成喵！\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\", \"at_user_ids\": [\"{BOSC_AT_USER}\"]}}'"
            ])

        # 写入脚本文件
        with open(run_test_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_test_script, 0o755)
        logger.info(f"Created test_{self.input_type.name}.sh script at {run_test_script}")
        

    def create_run_all_script(self, label: str, core_num: int, buildrun_bench_dir_list: list, iterations: int = 0):
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
            "set -x",
            "set -e",
            "",
            "# 获取脚本所在目录的绝对路径",
            "SCRIPT_DIR=$(pwd)",
            "LOG_FILE=\"$SCRIPT_DIR/run_all.log\"",
            f"CORE_NUM={core_num}",
            "",
            "# 运行所有基准测试并记录时间",
            "echo \"Starting benchmarks run at $(date)\" > \"$LOG_FILE\"",
            "",
            "ulimit -s unlimited",
            "",
            "# 运行每个基准测试",
        ]
        
        for bench_dir in buildrun_bench_dir_list:
            bench_name = os.path.basename(bench_dir)
            
            script_content.extend([
                f"echo -e '\\nRunning {bench_name}...' | tee -a \"$LOG_FILE\"",
                f"cd {bench_name}"
            ])
            for i in range(iterations):
                script_content.append(
                    f"(time -p taskset -c $CORE_NUM bash run_{self.input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"")
            script_content.extend([
                f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
                "cd \"$SCRIPT_DIR\"",
                ""
            ])
        
        script_content.extend([
            "echo -e '\\nAll benchmarks completed' | tee -a \"$LOG_FILE\"",
            "echo \"Finished at $(date)\" >> \"$LOG_FILE\""
        ])

        if BOSC_API_KEY != "" and BOSC_AT_USER != "":
            script_content.extend([
                f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
                f"     -H \"api-key: {BOSC_API_KEY}\" \\",
                f"     -H \"Content-Type: application/json\" \\",
                f"     -d '{{\"content\": \"{label} 测试完成喵！\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\", \"at_user_ids\": [\"{BOSC_AT_USER}\"]}}'"
            ])
        
        # 写入脚本文件
        with open(run_all_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_all_script, 0o755)
        logger.info(f"Created run_all script at {run_all_script}")
        

