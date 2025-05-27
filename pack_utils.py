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
        
    def copy_script_file_to_target_dir(self, script_name: str, script_target_dir: str):
        try:
            shutil.copy2(os.path.join(SCRIPTS_PATH, script_name), script_target_dir)
            logger.debug(f"Copie script {script_name} to {script_target_dir}.")
        except Exception as e:
            logger.error(f"Failed to copy script {script_name} to {script_target_dir}: {str(e)}")
            exit(1)

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

    def commands_to_cal_score(self, script_target_dir:str, test_clock_rate: float, score_file: str=""):
        self.copy_script_file_to_target_dir("cal_score.py", script_target_dir)
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
        self.copy_script_file_to_target_dir("send_md_message.py", script_target_dir)
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
        # collect_profiles_template = ""
        # with open(os.path.join(SCRIPTS_PATH, "collect_profiles.sh.template"), "r") as f:
        #     collect_profiles_template = f.read()
        # if DEFAULT_LLVM_PROFDATA_PATH != "":
        #     collect_profiles_template = collect_profiles_template.replace("<your llvm-profdata abspath>", DEFAULT_LLVM_PROFDATA_PATH)
        # with open(os.path.join(script_target_dir, "collect_profiles.sh"), 'w') as f:
        #     f.write(collect_profiles_template)
        # os.chmod(os.path.join(script_target_dir, "collect_profiles.sh"), 0o700)
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