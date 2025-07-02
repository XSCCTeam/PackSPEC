from config import *
from pack_spec.pack_utils import *
import shutil
import os
import re
import subprocess

class PackSPEC:
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
                 auto_mode: bool = False,
                 host_mode: bool = False,
                 ):
        self.utils = PackUtils(logger)
        self.spec_name = spec_name
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
        self.spec_benches = spec_benches
        self.spec_bench_list = self.get_bench_list(spec_benches)
        self.tune_type = tune_type
        self.input_type = input_type
        self.spec_mode = spec_mode
        self.iterations = iterations
        self.test_core_num = test_core_num
        self.rebuild = rebuild
        self.profile_gen = profile_gen
        if self.profile_gen: # profile 生成模式只跑一次程序
            self.iterations = 1
        self.auto_mode = auto_mode
        self.host_mode = host_mode
        self.test_clock_rate = test_clock_rate

    def get_bench_list(self, spec_benches: str):
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
                    exit(1)
            except Exception as e:
                logger.error(f"Failed to get reftime from '{reftime_path}': {str(e)}")
                exit(1)
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        assert is_number(reftime_result), f"Failed to get reftime from '{reftime_path}': Expect a numeric but get '{reftime_result}'"
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

    def get_bench_path(self, spec_bench_list: list, label: str, action_type: ActionType, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> list:

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
                if input_type == InputType.ref:
                    # 运行目录格式：run_优化类型_输入类型+模式_标签
                    bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}{spec_mode.name}_{label}"
                else:
                    # 运行目录格式：run_优化类型_输入类型_标签
                    bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}_{label}"

        selected_bench_dir = []
        
        # 遍历SPEC2017基准测试目录
        for bench_dir in os.listdir(self.spec_bench_path):
            # 检查是否为指定的基准测试集合
            if bench_dir in spec_bench_list:
                # 根据动作类型构建完整路径（build或run目录）
                bench_run_dir = os.path.join(self.spec_bench_path, bench_dir, bench_parent_dir)
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
        output_log = []
        spec_setup_cmd = [
            self.setup_script_path, 
            "--spec-dir", self.spec_dir,
            "--config", spec_cfg,
            "--action", "setup",
            "--tune", tune_type.name,
            "--input", input_type.name,
            "--benches", self.spec_benches,
            "--iterations", str(self.iterations)
        ]
        if rebuild:
            spec_setup_cmd.append(
                "--rebuild"
            )

        try:
            # 执行setup_spec脚本并实时输出
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

            spec_log_path = self.utils.create_spec_setup_log_path(output_log, 
                spec_cfg, tune_type, input_type)
            return spec_log_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e.stderr}")
            exit(1)
        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            exit(1)


    def copy_binarys(self, label: str, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode, 
                     dest_binary_dir: str = "", spec_cfg: str = "") -> str:
        src_bench_dir = self.get_bench_path(self.spec_bench_list, label, ActionType.build, tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_binary_dir == "":
            dest_binary_dir = self.utils.create_dest_dir(label, self.profile_gen, self.auto_mode, PACKMode.bin,
                                                         self.spec_name, tune_type, input_type, spec_mode)

        # 复制二进制文件至目标目录
        copy_num = 0
        for bench_dir in src_bench_dir:
            # 获取基准测试名称（目录的最后两级：如 500.perlbench_r/run_base_test_llvm19-m64）
            bench_name = os.path.basename(os.path.dirname(os.path.dirname(bench_dir)))
            binary_path = os.path.join(bench_dir, self.spec_bench_map[bench_name])
            dest_path = os.path.join(dest_binary_dir, bench_name)
            self.utils.copy_file_to_target_dir(binary_path, dest_path, f"{bench_name} binary")
            copy_num += 1
        if copy_num != 0:
            logger.success(f"Successfully copied {copy_num} files.")
        else:
            logger.error(f"No binary to copy.")
            exit(1)

        # 复制配置文件及相关日志至目标目录
        if spec_cfg != "":
            self.utils.copy_spec_cfg_and_logs_to_target_dir(
                self.spec_dir, spec_cfg, dest_binary_dir, tune_type, input_type)

        return dest_binary_dir


    def copy_benches(self, label: str, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode,
                     with_build: bool = False, dest_bench_dir: str = "", spec_cfg: str = "") -> list:
        if with_build:
            src_build_bench_dir = self.get_bench_path(self.spec_bench_list, label, ActionType.build, tune_type, input_type, spec_mode)
        src_run_bench_dir = self.get_bench_path(self.spec_bench_list, label, ActionType.run, tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
        if dest_bench_dir == "":
            if with_build:
                dest_bench_dir = self.utils.create_dest_dir(label, self.profile_gen, self.auto_mode, PACKMode.buildrun,
                                                            self.spec_name, tune_type, input_type, spec_mode)
            else:
                dest_bench_dir = self.utils.create_dest_dir(label, self.profile_gen, self.auto_mode, PACKMode.run,
                                                            self.spec_name, tune_type, input_type, spec_mode)
 
        dest_dir_list = []
        for bench_name in self.spec_bench_list:
            if with_build:
                src_build_dir = self.utils.get_bench_dir(bench_name, src_build_bench_dir)
                if src_build_dir == "":
                    logger.warning(f"Cannot match '{bench_name}' from '{src_build_bench_dir}'")
                    continue

            src_run_dir = self.utils.get_bench_dir(bench_name, src_run_bench_dir)
            if src_run_dir == "":
                logger.warning(f"Cannot match '{bench_name}' from '{src_run_bench_dir}'")
                continue

            dest_dir = os.path.join(dest_bench_dir, bench_name)
            logger.info(f"Copying {bench_name}...")
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
        
        self.create_run_all_script(label, self.test_core_num, dest_dir_list, tune_type, input_type)

        # 复制配置文件及相关日志至目标目录
        if spec_cfg != "":
            self.utils.copy_spec_cfg_and_logs_to_target_dir(
                self.spec_dir, spec_cfg, 
                os.path.dirname(dest_dir_list[0]), 
                tune_type, input_type)

        return dest_dir_list

    def execute_specinvoke(self, src_dir: str, dest_dir: str, input_type: InputType, binary_name: tuple = ("", "")) -> bool:
        specinvoke = os.path.join(self.spec_dir, "bin", "specinvoke")
        specinvoke_cmd = f"{specinvoke} -nn speccmds.cmd"

        src_dir_name = os.path.basename(src_dir)

        commands = self.utils.execute_commands(specinvoke_cmd, dest_dir)
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
            # 替换二进制文件名
            if binary_name[0] != "":
                line = line.replace(binary_name[0], binary_name[1])
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


    def create_test_script(self, label: str, bench_name: str, core_num: int, 
                            dest_dir: str, tune_type: TuneType, input_type: InputType, iterations: int = 0):

        if iterations == 0:
            iterations = self.iterations
        
        run_test_script = os.path.join(dest_dir, self.utils.get_run_script_name(self.profile_gen, input_type))

        script_content = self.utils.commands_to_prepare_run(
            f"test_{input_type.name}.log", core_num, iterations)

        script_content.extend(
            self.utils.commands_to_run_bench(bench_name, self.profile_gen, self.spec_bench_map,
                                             core_num, self.get_ref_time(bench_name, input_type),
                                             tune_type, label, input_type)
        )

        if self.profile_gen:
            self.utils.use_template_to_create_script(
                "merge_profile.sh.template", 
                dest_dir, 
                {"<your llvm-profdata abspath>": DEFAULT_LLVM_PROFDATA_PATH}
            )

        if BOSC_API_KEY != None and BOSC_AT_USER != None:
            if self.profile_gen:
                # 发送完成消息
                message = f"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} Profile 生成完成喵！"
                script_content.append(f"HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
            else:
                # 发送完成消息
                message = f"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} 测试完成喵！"
                script_content.append(f"HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
                # 计算分数
                script_content.extend(self.utils.commands_to_cal_score(dest_dir, self.test_clock_rate, "score.txt"))
                # 发送分数
                title_message = f"{bench_name}.{label}.{tune_type.name}_{input_type.name} 测试结果"
                text_message = f"在 $HOST_NAME 上的 {bench_name}.{label}.{tune_type.name}_{input_type.name} 测试结果喵："
                script_content.extend(self.utils.commands_to_send_md_message(dest_dir, title_message, text_message, "score.txt"))
        else:
            # 计算分数
            script_content.extend(self.utils.commands_to_cal_score(dest_dir, self.test_clock_rate))

        # 写入脚本文件
        with open(run_test_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_test_script, 0o700)
        logger.info(f"Created {self.utils.get_run_script_name(self.profile_gen, input_type)} script at {run_test_script}")
        

    def create_run_all_script(self, label: str, core_num: int, buildrun_bench_dir_list: list, 
                              tune_type: TuneType, input_type: InputType, iterations: int = 0):
        if not buildrun_bench_dir_list:
            logger.warning("No benchmark directories to run")
            return
            
        if iterations == 0:
            iterations = self.iterations

        # 获取父目录
        parent_dir = os.path.dirname(buildrun_bench_dir_list[0])
        run_all_script = os.path.join(parent_dir, self.utils.get_run_script_name(self.profile_gen, input_type, "all"))
        
        script_content = self.utils.commands_to_prepare_run(
            "run_all.log", core_num, iterations)

        script_content.extend([
            "",
            "# 运行所有基准测试并记录时间",
            "echo \"Starting benchmarks run at $(date)\" | tee -a \"$LOG_FILE\"",
            "",
            "# 依次运行每个基准测试",
            ""
        ])

        for bench_dir in buildrun_bench_dir_list:
            bench_name = os.path.basename(bench_dir)

            script_content.append(f"cd {bench_name}")
            script_content.extend(
                self.utils.commands_to_run_bench(bench_name, self.profile_gen, self.spec_bench_map, 
                                                 core_num, self.get_ref_time(bench_name, input_type),
                                                 tune_type, label, input_type)
            )
            script_content.extend([
                f"cd $SCRIPT_DIR",
                ""
            ])
        
        script_content.extend([
            "echo -e '\\nAll benchmarks completed' | tee -a \"$LOG_FILE\"",
            "echo \"Finished at $(date)\" | tee -a \"$LOG_FILE\"",
            ""
        ])

        if self.profile_gen:
            # 收集profile
            script_content.extend(self.utils.commands_to_collect_profiles(parent_dir))

        if BOSC_API_KEY != None and BOSC_AT_USER != None:
            if self.profile_gen:
                # 发送完成消息
                message = f"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} Profile 生成完成喵！"
                script_content.append(f"HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
            else:
                # 发送完成消息
                message = f"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} 测试完成喵！"
                script_content.append(f"HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
                # 计算分数
                script_content.extend(self.utils.commands_to_cal_score(parent_dir, self.test_clock_rate, "score.txt"))
                # 发送分数
                title_message = f"{label}.{tune_type.name}_{input_type.name} 测试结果"
                text_message = f"在 $HOST_NAME 上的 {label}.{tune_type.name}_{input_type.name} 测试结果喵："
                script_content.extend(self.utils.commands_to_send_md_message(parent_dir, title_message, text_message, "score.txt"))
        else:
            # 计算分数
            script_content.extend(self.utils.commands_to_cal_score(parent_dir, self.test_clock_rate))

        # 写入脚本文件
        with open(run_all_script, 'w') as f:
            f.write("\n".join(script_content))
        
        # 添加执行权限
        os.chmod(run_all_script, 0o700)
        logger.success(f"Successfully created {self.utils.get_run_script_name(self.profile_gen, input_type, 'all')} script at {run_all_script}")

    def setup_spec(self, spec_cfg: str):
        self.run_setup_spec(spec_cfg, self.tune_type, self.input_type, rebuild=self.rebuild)

    def pack_binarys(self, label: str, spec_cfg: str = "") -> list:
        if self.tune_type == TuneType.all:
            if self.input_type == InputType.all:
                self.copy_binarys(label, TuneType.base, InputType.test, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.base, InputType.train, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.base, InputType.ref, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.peak, InputType.test, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.peak, InputType.train, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.peak, InputType.ref, self.spec_mode, spec_cfg=spec_cfg)
            else:
                self.copy_binarys(label, TuneType.base, self.input_type, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, TuneType.peak, self.input_type, self.spec_mode, spec_cfg=spec_cfg)
        else:
            if self.input_type == InputType.all:
                self.copy_binarys(label, self.tune_type, InputType.test, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, self.tune_type, InputType.train, self.spec_mode, spec_cfg=spec_cfg)
                self.copy_binarys(label, self.tune_type, InputType.ref, self.spec_mode, spec_cfg=spec_cfg)
            else:
                self.copy_binarys(label, self.tune_type, self.input_type, self.spec_mode, spec_cfg=spec_cfg)
    
    def pack_binarys_cfg(self, spec_cfg: str):
        label = self.analyze_spec_config(spec_cfg)
        self.pack_binarys(label, spec_cfg)

    def pack_benches(self, label: str, with_build:bool = False, spec_cfg: str = "") -> list:
        dest_benches_dir_list = []
        if self.tune_type == TuneType.all:
            if self.input_type == InputType.all:
                self.copy_benches(label, TuneType.base, InputType.test, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.base, InputType.train, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.base, InputType.ref, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.peak, InputType.test, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.peak, InputType.train, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.peak, InputType.ref, self.spec_mode, with_build, spec_cfg=spec_cfg)
            else:
                self.copy_benches(label, TuneType.base, self.input_type, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, TuneType.peak, self.input_type, self.spec_mode, with_build, spec_cfg=spec_cfg)

        else:
            if self.input_type == InputType.all:
                self.copy_benches(label, self.tune_type, InputType.test, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, self.tune_type, InputType.train, self.spec_mode, with_build, spec_cfg=spec_cfg)
                self.copy_benches(label, self.tune_type, InputType.ref, self.spec_mode, with_build, spec_cfg=spec_cfg)
            else:
                self.copy_benches(label, self.tune_type, self.input_type, self.spec_mode, with_build, spec_cfg=spec_cfg)

        return dest_benches_dir_list

    def pack_benches_cfg(self, spec_cfg: str, with_build=False):
        label = self.analyze_spec_config(spec_cfg)
        self.pack_benches(label, with_build, spec_cfg)

if __name__ == "__main__":
    packer = PackSPEC(
        spec_name=SPECName.spec2017,
        spec_benches="625",
        tune_type=TuneType.base,
        input_type=InputType.ref,
        spec_mode=SPECMode.speed,
        iterations=3,
        test_core_num=4,
    )

