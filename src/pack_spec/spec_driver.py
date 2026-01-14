import sys
import os
import subprocess

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pack_spec.pack_config import *
from src.pack_spec.pack_utils import PackUtils

class SPECDriver:
    def __init__(self, 
                 spec_cfg_path: str,
                 spec_name: SPECName, 
                 tune_type: TuneType, 
                 input_type: InputType, 
                 spec_mode: SPECMode,
                 spec_benches: str,
                 utils: PackUtils,
                 iterations: int = 3,
                 rebuild: bool = False,
                 debug_mode: bool = False,
                 ):
        self.spec_cfg_path = spec_cfg_path
        self.spec_name = spec_name
        self.tune_type = tune_type
        self.input_type = input_type
        self.spec_mode = spec_mode
        self.spec_benches = spec_benches
        self.iterations = iterations
        self.rebuild = rebuild
        self.debug_mode = debug_mode
        self.utils = utils
        self.label = self.analyze_spec_config()
    
    def get_spec_info(self):
        """
        获取SPEC CPU 的基本信息
        """
        # TODO: 应该能够自动获取SPEC CPU的版本信息
        if self.spec_name == SPECName.spec2006:
            return {
                "spec_name": "SPEC CPU 2006",
                "spec_version": "v1.2.0",
                "spec_path": self.spec_dir,
            }
        elif self.spec_name == SPECName.spec2006v1p01:
            return {
                "spec_name": "SPEC CPU 2006",
                "spec_version": "v1.0.1",
                "spec_path": self.spec_dir,
            }
        elif self.spec_name == SPECName.spec2017:
            return {
                "spec_name": "SPEC CPU 2017",
                "spec_version": "v1.0.2",
                "spec_path": self.spec_dir,
            }
        else:
            raise ValueError(f"Unknown SPEC name: {self.spec_name}")

    def get_spec_log(self, spec_log_file: str) -> str:
        """
        从SPEC日志文件中获取日志路径
        
        Args:
            spec_log_file (str): SPEC日志文件路径
            
        Returns:
            str: 找到的日志路径，如果未找到则返回空字符串
        """
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

    def analyze_spec_config(self) -> str:
        """
        分析SPEC配置文件，提取标签信息
        
        Args:
            spec_cfg (str): SPEC配置文件名
            
        Returns:
            str: 从配置文件中提取的标签
            
        Raises:
            ConfigError: 当配置文件不存在时抛出
            PackSPECError: 当用户取消操作时抛出
            AssertionError: 当无法从配置文件中提取标签时抛出
        """
        label = ""
        try:
            with open(self.spec_cfg_path, 'r') as file:
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
                        logger.warning(f"'basepeak' is set to yes in {self.spec_cfg_path}.")
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
                            raise PackSPECError("Aborted by user.")
                        
        except FileNotFoundError:
            logger.error(f"File {self.spec_cfg_path} not found.")
            raise ConfigError(f"File {self.spec_cfg_path} not found.")
        if self.spec_name in [SPECName.spec2006, SPECName.spec2006v1p01]:
            assert label != "", f"Ext not found in file {self.spec_cfg_path}."
        elif self.spec_name == SPECName.spec2017:
            assert label!= "", f"Label not found in file {self.spec_cfg_path}."
        return label
    
    def run_setup_spec(self, tune_type: TuneType, input_type: InputType, rebuild: bool = True) -> str:
        """
        运行SPEC setup脚本
        
        Args:
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            rebuild (bool, optional): 是否重新构建，默认为True
            
        Returns:
            str: SPEC日志文件路径
            
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
        """
        output_log = []
        spec_setup_cmd = [
            self.setup_script_path, 
            "--spec-dir", self.spec_dir,
            "--config", self.spec_cfg_path,
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
            logger.info(f"Setting up spec from config: {self.spec_cfg_path}")
            logger.debug(f"Executing command: {spec_setup_cmd}")
            
            process = subprocess.Popen(
                spec_setup_cmd,
                cwd=P_PATH,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                text=True,
                bufsize=1  # 行缓冲
            )

            # 实时读取输出
            try:
                while True:
                    output = process.stdout
                    if output is not None:
                        output = output.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            logger.info(output.strip())
                            output_log.append(output.strip())
            finally:
                # 确保关闭stdout流
                if process.stdout is not None:
                    process.stdout.close()
            
            # 检查返回码
            return_code = process.wait()
            if return_code != 0:
                logger.error(f"Command failed with return code: {return_code}")
                raise CommandExecutionError(f"Command failed with return code: {return_code}")

            logger.success(f"Successfully setup spec with {tune_type}_{input_type} from config: {self.spec_cfg_path}")

            spec_log_path = self.utils.create_spec_setup_log_path(output_log, 
                self.spec_cfg_path, tune_type, input_type)
            return spec_log_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with error: {e.stderr}")
            raise CommandExecutionError(f"Command failed with error: {e.stderr}")
        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            raise CommandExecutionError(f"Failed to execute command: {str(e)}")


    def execute_specinvoke(self, src_dir: str, dest_dir: str, input_type: InputType, binary_name_map: tuple = ("", "")) -> bool:
        """
        执行specinvoke命令
        
        Args:
            src_dir (str): 源目录路径
            dest_dir (str): 目标目录路径
            input_type (InputType): 输入数据集类型
            binary_name_map (tuple, optional): 二进制文件名映射，默认为("", "")
            
        Returns:
            bool: 如果成功创建run.sh文件则返回True，否则返回False
            
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
        """

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
            if binary_name_map[0] != "":
                line = line.replace(binary_name_map[0], binary_name_map[1])
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

