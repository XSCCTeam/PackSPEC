"""
SPEC CPU基准测试驱动基类模块

本模块定义了SPEC CPU基准测试驱动的基类SPECDriver，提供了SPEC基准测试的通用操作接口。
SPEC2006和SPEC2017的具体实现继承自该基类。

主要功能：
- 解析SPEC配置文件，提取标签信息
- 执行SPEC setup脚本进行编译和环境准备
- 获取基准测试的构建和运行目录路径
- 执行specinvoke命令生成运行脚本
- 获取基准测试的参考时间

子类需要实现：
- get_bench_list(): 获取基准测试列表
- get_ref_time(): 获取参考时间
- get_bench_path(): 获取基准测试目录路径
- get_binary_path_map(): 获取二进制文件路径映射
"""

import sys
import os
import subprocess

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    PackSPECError, ConfigError, FileOperationError, CommandExecutionError,
    P_PATH, logger
)
from src.pack_spec.pack_utils import PackUtils
from typing import Dict, List, Optional


class SPECDriver:
    """
    SPEC CPU基准测试驱动基类
    
    该类是SPEC2006Driver和SPEC2017Driver的基类，定义了SPEC基准测试的通用操作接口。
    提供了配置解析、编译执行、路径获取等核心功能。
    
    Attributes:
        spec_cfg_path (str): SPEC配置文件的绝对路径
        spec_name (SPECName): SPEC版本枚举值
        tune_type (TuneType): 优化级别枚举值
        input_type (InputType): 输入数据集类型枚举值
        spec_mode (SPECMode): 运行模式枚举值
        spec_benches (str): 基准测试选择字符串
        iterations (int): 测试迭代次数
        rebuild (bool): 是否重新构建
        debug_mode (bool): 是否调试模式
        utils (PackUtils): 工具类实例
        label (str): 从配置文件中提取的标签
        spec_dir (str): SPEC安装目录路径
        spec_bench_path (str): SPEC基准测试目录路径
        spec_bench_map (dict): 基准测试名称到二进制文件名的映射
        spec_build_dir (str): 构建目录名称
        spec_run_dir (str): 运行目录名称
        setup_script_path (str): setup脚本路径
        spec_bench_list (list): 选中的基准测试列表
        
    Note:
        该类不应直接实例化，应使用SPEC2006Driver或SPEC2017Driver
    """
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
        """
        初始化SPECDriver实例
        
        Args:
            spec_cfg_path (str): SPEC配置文件的绝对路径
            spec_name (SPECName): SPEC版本枚举值(spec2006/spec2006v1p01/spec2017)
            tune_type (TuneType): 优化级别枚举值(base/peak/all)
            input_type (InputType): 输入数据集类型枚举值(test/train/ref/all)
            spec_mode (SPECMode): 运行模式枚举值(speed/rate)
            spec_benches (str): 基准测试选择字符串，空格分隔
            utils (PackUtils): 工具类实例
            iterations (int, optional): 测试迭代次数，默认3
            rebuild (bool, optional): 是否重新构建，默认False
            debug_mode (bool, optional): 是否调试模式，默认False
            
        Note:
            初始化时会自动调用analyze_spec_config()解析配置文件获取标签
        """
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
    
    def get_spec_info(self) -> Dict[str, str]:
        """
        获取SPEC CPU的基本信息
        
        返回当前SPEC版本的名称、版本号和安装路径。
        
        Returns:
            dict: 包含以下键的字典：
                - spec_name (str): SPEC名称，如"SPEC CPU 2006"
                - spec_version (str): SPEC版本号，如"v1.2.0"
                - spec_path (str): SPEC安装目录路径
                
        Raises:
            ValueError: 当spec_name不是已知的SPEC版本时抛出
            
        Note:
            子类可以重写此方法以提供更准确的版本信息
        """
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
        从SPEC日志文件中获取实际的日志文件路径
        
        SPEC setup执行后会输出日志路径信息，此方法用于解析并提取该路径。
        
        Args:
            spec_log_file (str): SPEC日志文件路径
            
        Returns:
            str: 找到的日志文件绝对路径，如果未找到则返回空字符串
            
        Note:
            日志文件中包含形如"The log for this run is in /path/to/log"的行
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
        
        从SPEC配置文件中解析出标签(label)，用于标识编译配置。
        SPEC2006使用'ext'字段，SPEC2017使用'label'字段。
        
        Returns:
            str: 从配置文件中提取的标签字符串
            
        Raises:
            ConfigError: 当配置文件不存在时抛出
            PackSPECError: 当用户取消basepeak确认时抛出
            AssertionError: 当无法从配置文件中提取标签时抛出
            
        Note:
            - 如果配置文件中设置了basepeak=yes，会提示用户确认
            - SPEC2006配置文件格式: ext = label_name
            - SPEC2017配置文件格式: label = label_name
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
        运行SPEC setup脚本进行编译和环境准备
        
        调用外部setup脚本执行SPEC基准测试的编译和运行目录准备。
        脚本会实时输出执行过程，并记录日志。
        
        Args:
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            rebuild (bool, optional): 是否重新构建，默认True
            
        Returns:
            str: SPEC setup日志文件路径
            
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
            
        Note:
            - 脚本路径由setup_script_path属性指定
            - 执行的命令格式: setup_script --spec-dir ... --config ... --action setup ...
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
        执行specinvoke命令生成运行脚本
        
        specinvoke是SPEC工具提供的命令，用于解析speccmds.cmd文件并生成可执行的运行命令。
        此方法调用specinvoke，处理输出并生成run_{input_type}.sh脚本。
        
        Args:
            src_dir (str): 源目录路径，包含speccmds.cmd文件
            dest_dir (str): 目标目录路径，生成的脚本将保存在此
            input_type (InputType): 输入数据集类型
            binary_name_map (tuple, optional): 二进制文件名映射(旧名, 新名)，默认为("", "")
            
        Returns:
            bool: 如果成功创建run.sh文件则返回True
            
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
            
        Note:
            - 生成的脚本会去除cd命令和绝对路径引用
            - 脚本具有可执行权限(0o755)
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

    def _check_spec_environment(self) -> bool:
        """
        检查SPEC环境是否正确配置
        
        检查SPEC安装目录是否存在，以及runspec/runcpu命令是否可用。
        
        Returns:
            bool: 如果环境检查通过返回True
            
        Raises:
            FileOperationError: 当SPEC安装目录不存在时抛出
            CommandExecutionError: 当SPEC命令不可用时抛出
        """
        if not os.path.isdir(self.spec_dir):
            raise FileOperationError(f"SPEC安装目录不存在: {self.spec_dir}")
        
        if self.spec_name in [SPECName.spec2006, SPECName.spec2006v1p01]:
            spec_cmd = os.path.join(self.spec_dir, "bin", "runspec")
        else:
            spec_cmd = os.path.join(self.spec_dir, "bin", "runcpu")
        
        if not os.path.isfile(spec_cmd):
            raise CommandExecutionError(f"SPEC命令不存在: {spec_cmd}")
        
        logger.debug(f"SPEC环境检查通过: {self.spec_dir}")
        return True

    def _build_run_command(self) -> List[str]:
        """
        构建SPEC运行命令
        
        根据SPEC版本构建runspec或runcpu命令及参数。
        子类需要重写此方法以提供版本特定的命令构建逻辑。
        
        Returns:
            List[str]: SPEC命令及参数列表
            
        Note:
            此方法应由子类重写，基类返回空列表
        """
        logger.warning("_build_run_command() 应由子类重写")
        return []

    def run_spec_directly(self, output_dir: Optional[str] = None) -> Dict:
        """
        直接运行SPEC测试
        
        调用runspec/runcpu命令直接执行SPEC基准测试，无需打包。
        测试完成后返回结果信息。
        
        Args:
            output_dir (str, optional): 结果输出目录，默认为spec_results/{timestamp}
            
        Returns:
            Dict: 包含以下键的结果字典：
                - success (bool): 是否成功完成
                - output_dir (str): 结果输出目录
                - log_file (str): 日志文件路径
                - return_code (int): 命令返回码
                - error_message (str): 错误信息（如果有）
                
        Raises:
            FileOperationError: 当SPEC环境检查失败时抛出
            CommandExecutionError: 当命令执行失败时抛出
            
        Note:
            - 测试过程中会实时输出日志
            - 支持Ctrl+C中断测试
        """
        self._check_spec_environment()
        
        spec_cmd = self._build_run_command()
        if not spec_cmd:
            raise CommandExecutionError("无法构建SPEC命令")
        
        if output_dir is None:
            from src.pack_spec.pack_config import RESULTS_OUTPUT_PATH, CURRENT_TIME
            output_dir = os.path.join(RESULTS_OUTPUT_PATH, f"run_{CURRENT_TIME}")
        
        os.makedirs(output_dir, exist_ok=True)
        log_file = os.path.join(output_dir, "spec_run.log")
        
        result = {
            "success": False,
            "output_dir": output_dir,
            "log_file": log_file,
            "return_code": -1,
            "error_message": ""
        }
        
        logger.info(f"开始运行SPEC测试: {' '.join(spec_cmd)}")
        logger.info(f"结果输出目录: {output_dir}")
        
        process = None
        try:
            with open(log_file, 'w') as log_f:
                process = subprocess.Popen(
                    spec_cmd,
                    cwd=self.spec_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                while True:
                    output = process.stdout
                    if output is not None:
                        line = output.readline()
                        if line == '' and process.poll() is not None:
                            break
                        if line:
                            logger.info(line.strip())
                            log_f.write(line)
                            log_f.flush()
                
                return_code = process.wait()
                result["return_code"] = return_code
                
                if return_code == 0:
                    result["success"] = True
                    logger.success(f"SPEC测试完成: {output_dir}")
                else:
                    result["error_message"] = f"命令返回非零退出码: {return_code}"
                    logger.error(result["error_message"])
                    
        except KeyboardInterrupt:
            if process:
                process.terminate()
                process.wait()
            result["error_message"] = "用户中断测试"
            logger.warning("用户中断测试")
            raise CommandExecutionError("用户中断测试")
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(f"执行SPEC命令失败: {e}")
            raise CommandExecutionError(f"执行SPEC命令失败: {e}")
        
        return result

