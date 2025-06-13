from asyncio import streams
import os
from config import *
import subprocess
import shutil


class PackUtils:
    def __init__(self, logger, debug_mode=False):
        self.logger = logger
        self.debug_mode = debug_mode

    def get_bench_dir(self, bench_name: str, bench_dirs: list) -> str:
        if self.debug_mode:
            self.logger.debug(f"Get bench dir with:")
            self.logger.debug(f"  bench_name: {bench_name}")
            self.logger.debug(f"  bench_dirs: {bench_dirs}")
        for bench_dir in bench_dirs:
            dir_bench_name = os.path.basename(
                os.path.dirname(
                    os.path.dirname(bench_dir)))
            if dir_bench_name == bench_name:
                return bench_dir
        self.logger.warning(f"Failed to find bench dir for {bench_name}.")
        return ""

    def get_dest_dir(self, label: str, profile_gen: bool, auto_mode: bool, pack_mode: PACKMode,
                     spec_name: SPECName, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode):
        if self.debug_mode:
            self.logger.debug(f"Get dest dir with:")
            self.logger.debug(f"  spec_name: {spec_name.name}")
            self.logger.debug(f"  label: {label}")
            self.logger.debug(f"  profile_gen: {profile_gen}")
            self.logger.debug(f"  auto_mode: {auto_mode}")
            self.logger.debug(f"  pack_mode: {pack_mode.name}")
            self.logger.debug(f"  tune_type: {tune_type}")
            self.logger.debug(f"  input_type: {input_type}")
            self.logger.debug(f"  spec_mode: {spec_mode}")
        test_name = f"{label}.{tune_type.name}_{input_type.name}_{spec_mode.name}"
        dest_bench_name = f"{spec_name.name}_{pack_mode.name}_{test_name}"
        
        if profile_gen:
            dest_bench_name = f"{dest_bench_name}_profilegen"

        if auto_mode:
            dest_bench_dir = os.path.join(PACK_PATH, dest_bench_name)
        else:
            dest_bench_dir = os.path.join(PACK_PATH, spec_name.name, 
                pack_mode.name, f"{CURRENT_DATE}_{dest_bench_name}")
        return dest_bench_dir

    def get_spec_log_file_path(self, spec_dir: str, spec_log_file: str) -> str:
        if self.debug_mode:
            self.logger.debug(f"Get spec log file path with:")
            self.logger.debug(f"  spec_dir: {spec_dir}")
            self.logger.debug(f"  spec_log_file: {spec_log_file}")
        marked_line = f"The log for this run is in {spec_dir}"
        try:
            with open(spec_log_file, "r") as f:
                spec_log = f.readlines()
            for spec_log_line in spec_log:
                if spec_log_line.startswith(marked_line):
                    self.logger.debug(f"Find spec log from '{spec_log_file}'")
                    return spec_log_line.replace("The log for this run is in ", "").strip()
        except Exception as e:
            self.logger.debug(f"Failed find spec log from '{spec_log_file}': {str(e)}")
            return ""

    def get_spec_setup_log_path(self, spec_cfg: str, tune_type: TuneType, input_type: InputType):
        if self.debug_mode:
            self.logger.debug(f"Get spec setup log path with:")
            self.logger.debug(f"  spec_cfg: {spec_cfg}")
            self.logger.debug(f"  tune_type: {tune_type}")
            self.logger.debug(f"  input_type: {input_type}")
        spec_cfg_name = spec_cfg.replace('.cfg', '')
        spec_log_file = f"{spec_cfg_name}.{tune_type.name}_{input_type.name}.setuplog"
        spec_log_path = os.path.join(SPEC_LOG_PATH, spec_log_file)
        return spec_log_path

    def create_spec_setup_log_path(self, log_content: str, 
                                   spec_cfg: str, tune_type: TuneType, input_type: InputType):
        if self.debug_mode:
            self.logger.debug(f"Create spec setup log path with:")
            self.logger.debug(f"  log_content: {log_content}")
            self.logger.debug(f"  spec_cfg: {spec_cfg}")
            self.logger.debug(f"  tune_type: {tune_type}")
            self.logger.debug(f"  input_type: {input_type}")
        spec_log_path = self.get_spec_setup_log_path(spec_cfg, tune_type, input_type)
        os.makedirs(SPEC_LOG_PATH, exist_ok=True)
        with open(spec_log_path, "w") as f:
            f.write("\n".join(log_content))
        return spec_log_path
    
    def create_dest_dir(self, label: str, profile_gen: bool, auto_mode: bool, pack_mode: PACKMode,
                        spec_name: SPECName, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode):
        if self.debug_mode:
            self.logger.debug(f"Create dest dir with:")
            self.logger.debug(f"  spec_name: {spec_name.name}")
            self.logger.debug(f"  label: {label}")
            self.logger.debug(f"  profile_gen: {profile_gen}")
            self.logger.debug(f"  auto_mode: {auto_mode}")
            self.logger.debug(f"  pack_mode: {pack_mode.name}")
            self.logger.debug(f"  tune_type: {tune_type}")
            self.logger.debug(f"  input_type: {input_type}")
            self.logger.debug(f"  spec_mode: {spec_mode}")
        dest_bench_dir = self.get_dest_dir(label,
                                           profile_gen, auto_mode, pack_mode,
                                           spec_name, tune_type, input_type, spec_mode)
        if os.path.exists(dest_bench_dir):
            self.logger.info(f"Directory {dest_bench_dir} already exists.")
            if not auto_mode:
                self.logger.debug(f"Do you want to overwrite it? (y/n): ")
                choice = input(f"Do you want to overwrite it? (y/n): ")
            if auto_mode == True or choice.lower() == 'y':
                self.logger.debug(f"Overwriting directory {dest_bench_dir} ")
                shutil.rmtree(dest_bench_dir)
                os.makedirs(dest_bench_dir, exist_ok=False)
            else:
                self.logger.error("User canceled the operation. Directory not overwritten.")
                exit(1)
        else:
            self.logger.debug(f"Creating directory {dest_bench_dir} ")
            os.makedirs(dest_bench_dir, exist_ok=False)
        return dest_bench_dir

    def create_env_file(self, dest_dir: str, env_name: str):
        try:
            self.logger.info(f"Create {env_name}.env to record compile environment.")
            with open(os.path.join(dest_dir, f"{env_name}.env"), 'w') as f:
                # 将当前环境变量写入文件
                for key, value in os.environ.items():
                    if key not in ["BOSC_API_KEY", "BOSC_AT_USER"]:
                        f.write(f"{key}={value}\n")
        except Exception as e:
            self.logger.error(f"Failed to create compile.env: {str(e)}")


    def execute_commands(self, command: str, work_dir: str) -> list[str]:
        try:
            # 执行specinvoke命令并捕获输出
            self.logger.debug(f"Executing command: {command}")
            if self.debug_mode:
                self.logger.debug(f"On: {work_dir}")
            result = subprocess.run(
                command.split(),
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            # 处理命令输出
            bash_result = result.stdout.split("\n")
            if self.debug_mode:
                self.logger.debug(f"Command output: {bash_result}")
            return bash_result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with error: {e.stderr}")
            exit(1)
        except Exception as e:
            self.logger.error(f"Failed to execute command: {str(e)}")
            exit(1)
        
    def copy_file_to_target_dir(self, src_path: str, dest_path: str, file_info: str=""):
        try:
            src_file_name = os.path.basename(src_path)
            dest_file_name = os.path.basename(dest_path)
            shutil.copy2(src_path, dest_path)
            self.logger.debug(f"Copie {file_info} file '{src_file_name}' to '{dest_file_name}'.")
            self.logger.debug(f"Copying {src_file_name}\n\tFrom {src_path} -to-> {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy {file_info} file '{src_path}' to '{dest_path}': {str(e)}")
            return False

    def copy_script_file_to_target_dir(self, script_name: str, script_target_dir: str):
        src_dir = os.path.join(SCRIPTS_PATH, script_name)
        return self.copy_file_to_target_dir(src_dir, script_target_dir, f"script {script_name}")

    def use_template_to_create_script(self, template_name: str, script_target_dir: str, replace_dict: dict):
        if self.debug_mode:
            self.logger.debug(f"Use template to create script with:")
            self.logger.debug(f"  template_name: {template_name}")
            self.logger.debug(f"  script_target_dir: {script_target_dir}")
            self.logger.debug(f"  replace_dict: {replace_dict}")
        try:
            script_name = template_name.replace('.template', '')
            with open(os.path.join(SCRIPTS_PATH, template_name), "r") as f:
                template = f.read()
            for key, value in replace_dict.items():
                if key != None and value!= None:
                    template = template.replace(key, value)
            with open(os.path.join(script_target_dir, script_name), "w") as f:
                f.write(template)
            os.chmod(os.path.join(script_target_dir, script_name), 0o700)
            self.logger.debug(f"Create script {script_name} from template {template_name} to {script_target_dir}.")
        except Exception as e:
            self.logger.error(f"Failed to create script {script_name} from template {template_name} to {script_target_dir}: {str(e)}")
            exit(1)

    def copy_spec_cfg_and_logs_to_target_dir(self, spec_dir: str, spec_cfg: str, dest_dir: str,
                                             tune_type: TuneType, input_type: InputType):
        # 复制配置文件至目标目录
        spec_cfg_path = os.path.join(spec_dir, "config", spec_cfg)
        self.copy_file_to_target_dir(spec_cfg_path, dest_dir, "configs")

        # 复制setup log至目标目录
        spec_log_path = self.get_spec_setup_log_path(spec_cfg, tune_type, input_type)
        self.copy_file_to_target_dir(spec_log_path, dest_dir, "spec_setup log")

        # 复制spec log至目标目录
        spec_log_file_path = self.get_spec_log_file_path(spec_dir, spec_log_path)
        if spec_log_file_path != "":
            self.copy_file_to_target_dir(spec_log_file_path, dest_dir, "spec log")

        # 创建env文件至目标目录
        self.create_env_file(dest_dir, "compile")

    def commands_to_cal_score(self, script_target_dir:str, test_clock_rate: float, score_file: str=""):
        if not self.copy_script_file_to_target_dir("cal_score.py", script_target_dir):
            exit(1)
        if self.debug_mode:
            self.logger.debug(f"Commands to cal score with:")
            self.logger.debug(f"  script_target_dir: {script_target_dir}")
            self.logger.debug(f"  test_clock_rate: {test_clock_rate}")
            self.logger.debug(f"  score_file: {score_file}")
        commands = [
            "# 计算分数",
            f"chmod +x cal_score.py"
        ]
        if score_file == "":
            commands.append(f"./cal_score.py $LOG_FILE {test_clock_rate}")
        else:
            commands.append(f"./cal_score.py $LOG_FILE {test_clock_rate} | tee {score_file}")
        commands.append("")
        self.logger.debug(f"Add cal score commands.")
        return commands

    def commands_to_send_message(self, message: str):
        if self.debug_mode:
            self.logger.debug(f"Commands to send message with:")
            self.logger.debug(f"  message: {message}")
        commands = [
            "# 发送任务完成信息并at指定用户",
            f"curl -X POST \"http://172.38.8.102:8848/send-message\" \\",
            f"     -H \"api-key: {BOSC_API_KEY}\" \\",
            f"     -H \"Content-Type: application/json\" \\",
            f"     -d \"{{\\\"content\\\": \\\"{message}\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\\", \\\"at_user_ids\\\": [\\\"{BOSC_AT_USER}\\\"]}}\"",
            ""
        ]
        self.logger.debug(f"Add send message commands.")
        return commands

    def commands_to_send_md_message(self, script_target_dir:str, title_message: str, text_message: str, md_path: str):
        if not self.copy_script_file_to_target_dir("send_md_message.py", script_target_dir):
            exit(1)
        if self.debug_mode:
            self.logger.debug(f"Commands to send md message with:")
            self.logger.debug(f"  script_target_dir: {script_target_dir}")
            self.logger.debug(f"  title_message: {title_message}")
            self.logger.debug(f"  text_message: {text_message}")
            self.logger.debug(f"  md_path: {md_path}")
        commands = [
            "# 发送MarkDown格式信息并at指定用户",
            f"chmod +x send_md_message.py",
            f"./send_md_message.py --api_key {BOSC_API_KEY} \\",
            f"     --title \"{title_message}\" \\",
            f"     --text \"{text_message}\" \\",
            f"     --md_path \"{md_path}\" \\",
            f"     --at_mobiles \"{BOSC_AT_USER}\"",
            ""
        ]
        self.logger.debug(f"Add send md message commands.")
        return commands
    
    def commands_to_collect_profiles(self, script_target_dir: str):
        self.use_template_to_create_script(
            "collect_profiles.sh.template",
            script_target_dir,
            {"<your llvm-profdata abspath>": DEFAULT_LLVM_PROFDATA_PATH}
        )
        if self.debug_mode:
            self.logger.debug(f"Commands to collect profiles with:")
            self.logger.debug(f"  script_target_dir: {script_target_dir}")
        commands = [
            "# 收集profile文件",
            f"chmod +x collect_profiles.sh",
            f"./collect_profiles.sh",
            ""
        ]
        self.logger.debug(f"Add collect profiles commands.")
        return commands

    def commands_to_prepare_run(self, log_name: str, core_num: int, iterations: int):
        if self.debug_mode:
            self.logger.debug(f"Commands to prepare run with:")
            self.logger.debug(f"  log_name: {log_name}")
            self.logger.debug(f"  core_num: {core_num}")
            self.logger.debug(f"  iterations: {iterations}")
        commands = [
            "#!/bin/bash",
            "",
            "# 检查 curl 是否安装",
            "if ! command -v curl &> /dev/null",
            "then",
            "    echo \"ERROR! curl is not installed.\"",
            "    exit 1",
            "fi",
            "set -e",
            "",
            "# 解除栈限制",
            "ulimit -s unlimited",
            "# 获取脚本所在目录的绝对路径",
            "SCRIPT_DIR=$(pwd)",
            "# 定义日志文件名",
            f"LOG_FILE=\"{log_name}\"",
            "# 定义测试迭代次数",
            f"TEST_TIMES={iterations}",
        ]
        if core_num!= -1:
            commands.extend([
                "# 定义绑定核心编号",
                f"CORE_NUM={core_num}"
            ])
        return commands

    def commands_to_run_bench(self, bench_name: str, profile_gen: bool, spec_bench_map: dict, 
                              core_num: int, ref_time: float,
                              tune_type: TuneType, label: str, input_type: InputType):
        if self.debug_mode:
            self.logger.debug(f"Commands to run bench with:")
            self.logger.debug(f"  bench_name: {bench_name}")
            self.logger.debug(f"  profile_gen: {profile_gen}")
            self.logger.debug(f"  spec_bench_map: {spec_bench_map}")
            self.logger.debug(f"  core_num: {core_num}")
            self.logger.debug(f"  ref_time: {ref_time}")
            self.logger.debug(f"  tune_type: {tune_type}")
            self.logger.debug(f"  label: {label}")
            self.logger.debug(f"  input_type: {input_type}")
        commands = [
            f"echo -e '\\nRunning {bench_name}...' | tee -a \"$LOG_FILE\"",
            f"echo -e 'Reftime: {ref_time}' | tee -a \"$LOG_FILE\"",
        ]
        if profile_gen:
            commands.extend([
                "# 生成profile文件避免覆盖",
                f"export LLVM_PROFILE_FILE=\"profiles/{bench_name}-%m-%p.profraw\"",
            ])
        commands.extend([
            f"chmod +x ./{spec_bench_map[bench_name]}_{tune_type.name}.{label}",
            f"chmod +x ./run_{input_type.name}.sh",
            f"for i in $(seq 1 $TEST_TIMES); do",
            f"    echo \"Test {bench_name} #$i:\" | tee -a \"$LOG_FILE\""
        ])
        if core_num!= -1:
            commands.append(
                f"    (time -p taskset -c $CORE_NUM bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
            )
        else:
            commands.append(
                f"    (time -p bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\""
            )
        commands.extend([
            f"done",
            f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
        ])
        return commands