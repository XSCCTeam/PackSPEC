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
- _get_bench_dir_prefix(): 获取基准测试目录前缀（可选重写）
- get_binary_path_map(): 获取二进制文件路径映射
- _build_run_command(): 构建SPEC运行命令
"""

import os
import re
import subprocess

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    ConfigError, FileOperationError, CommandExecutionError,
    P_PATH, logger
)
from src.pack_spec.pack_utils import PackUtils
from typing import Dict, List, Optional


class SPECDriver:
    """
    SPEC CPU基准测试驱动基类
    
    该类是SPEC2006Driver和SPEC2017Driver的基类，定义了SPEC基准测试的通用操作接口。
    提供了配置解析、编译执行、路径获取等核心功能。
    
    支持驱动注册表模式：子类通过 _spec_name_key 类属性指定对应的 SPECName 枚举值，
    在定义时自动注册到 _registry 字典中。通过 create() 工厂方法根据 SPECName 枚举值
    查找并实例化对应的驱动类，替代 if/elif 链。
    
    Attributes:
        spec_cfg_path (str): SPEC配置文件的绝对路径
        spec_name (SPECName): SPEC版本枚举值
        tune_type (TuneType): 优化级别枚举值
        input_type (InputType): 输入数据集类型枚举值
        spec_mode (SPECMode): 运行模式枚举值(speed/rate)
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

    _registry: Dict[str, type] = {}
    """驱动注册表，键为 SPECName 枚举成员名，值为对应的驱动类"""

    _spec_name_key: Optional[str] = None
    """子类需设置此属性为对应的 SPECName 枚举成员名，用于自动注册"""

    def __init_subclass__(cls, **kwargs):
        """
        子类定义时自动注册到注册表
        
        当子类设置了 _spec_name_key 类属性时，自动将其注册到 _registry 中。
        子类必须在类体中定义 _spec_name_key 为 SPECName 枚举成员名字符串。
        
        Args:
            **kwargs: 传递给父类的关键字参数
        """
        super().__init_subclass__(**kwargs)
        if cls._spec_name_key is not None:
            SPECDriver._registry[cls._spec_name_key] = cls

    @classmethod
    def create(cls, spec_name: SPECName, spec_cfg_path: str, tune_type: TuneType,
               input_type: InputType, spec_mode: SPECMode, spec_benches: str,
               utils: PackUtils, iterations: int = 3, rebuild: bool = False,
               debug_mode: bool = False, allow_basepeak: bool = False) -> 'SPECDriver':
        """
        工厂方法：根据 SPECName 枚举值创建对应的驱动实例
        
        通过注册表查找 spec_name 对应的驱动类并实例化，
        替代 if/elif 链进行驱动选择。
        
        Args:
            spec_name (SPECName): SPEC版本枚举值(spec2006/spec2006v1p01/spec2017)
            spec_cfg_path (str): SPEC配置文件的绝对路径
            tune_type (TuneType): 优化级别枚举值(base/peak/all)
            input_type (InputType): 输入数据集类型枚举值(test/train/ref/all)
            spec_mode (SPECMode): 运行模式枚举值(speed/rate)
            spec_benches (str): 基准测试选择字符串，空格分隔
            utils (PackUtils): 工具类实例
            iterations (int, optional): 测试迭代次数，默认3
            rebuild (bool, optional): 是否重新构建，默认False
            debug_mode (bool, optional): 是否调试模式，默认False
            allow_basepeak (bool, optional): 是否允许basepeak配置，默认False
            
        Returns:
            SPECDriver: 对应的驱动实例
            
        Raises:
            ValueError: 当 spec_name 未在注册表中找到对应驱动类时抛出
        """
        driver_cls = cls._registry.get(spec_name.name)
        if driver_cls is None:
            raise ValueError(
                f"未找到 SPECName '{spec_name.name}' 对应的驱动类，"
                f"已注册的驱动: {list(cls._registry.keys())}"
            )
        return driver_cls(
            spec_cfg_path=spec_cfg_path,
            tune_type=tune_type,
            input_type=input_type,
            spec_mode=spec_mode,
            spec_benches=spec_benches,
            utils=utils,
            iterations=iterations,
            rebuild=rebuild,
            debug_mode=debug_mode,
            allow_basepeak=allow_basepeak,
        )
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
                 allow_basepeak: bool = False,
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
            allow_basepeak (bool, optional): 是否允许basepeak配置，默认False
            
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
        self.allow_basepeak = allow_basepeak
        self.utils = utils
        self.msg = utils.msg  # 使用 PackUtils 中的消息管理器
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
                    logger.debug(self.msg.get("spec_log_found", file=spec_log_file))
                    return spec_log_line.replace("The log for this run is in ", "").strip()
        except Exception as e:
            logger.debug(self.msg.get("spec_log_parse_error", file=spec_log_file, error=str(e)))
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
            ConfigError: 当无法从配置文件中提取标签时抛出
            ConfigError: 当配置文件中设置了basepeak=yes但未启用allow_basepeak时抛出
            
        Note:
            - 如果配置文件中设置了basepeak=yes，需要allow_basepeak=True才允许继续
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
                        logger.warning(self.msg.get("basepeak_set_to_yes", path=self.spec_cfg_path))
                        logger.warning(self.msg.get("basepeak_meaning"))
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
                        if self.allow_basepeak:
                            logger.warning(self.msg.get("continue_with_basepeak"))
                        else:
                            logger.error(self.msg.get("basepeak_not_allowed"))
                            raise ConfigError(self.msg.get("basepeak_not_allowed"))
                        
        except FileNotFoundError:
            logger.error(self.msg.get("config_file_not_found", path=self.spec_cfg_path))
            raise ConfigError(self.msg.get("config_file_not_found", path=self.spec_cfg_path))
        if self.spec_name in [SPECName.spec2006, SPECName.spec2006v1p01]:
            if label == "":
                raise ConfigError(f"Ext not found in file {self.spec_cfg_path}.")
        elif self.spec_name == SPECName.spec2017:
            if label == "":
                raise ConfigError(f"Label not found in file {self.spec_cfg_path}.")
        return label
    
    def _convert_benches_for_mode(self, spec_benches: str, spec_mode: SPECMode) -> str:
        """
        根据spec_mode将spec_benches中的通用名称转换为对应的benchset名称

        当spec_mode为speed时，将"all"/"int"/"fp"转换为对应的speed benchset名称；
        当spec_mode为rate时，转换为对应的rate benchset名称。
        对于具体的基准测试编号(如"600 602")则保持不变。

        Args:
            spec_benches (str): 原始基准测试选择字符串
            spec_mode (SPECMode): 运行模式枚举值(speed/rate)

        Returns:
            str: 转换后的benchset名称字符串
        """
        benches = spec_benches.split()
        converted = []
        for bench in benches:
            if self.spec_name == SPECName.spec2017:
                if bench == "all":
                    converted.extend(["intspeed", "fpspeed"] if spec_mode == SPECMode.speed else ["intrate", "fprate"])
                elif bench in ["int", "intspeed", "intrate"]:
                    converted.append("intspeed" if spec_mode == SPECMode.speed else "intrate")
                elif bench in ["fp", "fpspeed", "fprate"]:
                    converted.append("fpspeed" if spec_mode == SPECMode.speed else "fprate")
                else:
                    converted.append(bench)
            elif self.spec_name in [SPECName.spec2006, SPECName.spec2006v1p01]:
                if bench == "all":
                    converted.extend(["int", "fp"])
                else:
                    converted.append(bench)
            else:
                converted.append(bench)
        return " ".join(converted)

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
            - 会根据spec_mode自动将spec_benches转换为对应的benchset名称
        """
        output_log = []
        setup_benches = self._convert_benches_for_mode(self.spec_benches, self.spec_mode)
        spec_setup_cmd = [
            self.setup_script_path, 
            "--spec-dir", self.spec_dir,
            "--config", self.spec_cfg_path,
            "--action", "setup",
            "--tune", tune_type.name,
            "--input", input_type.name,
            "--benches", setup_benches,
            "--iterations", str(self.iterations)
        ]
        if rebuild:
            spec_setup_cmd.append(
                "--rebuild"
            )

        try:
            # 执行setup_spec脚本并实时输出
            logger.info(self.msg.get("setting_up_spec", path=self.spec_cfg_path))
            logger.debug(self.msg.get("executing_command_debug", cmd=spec_setup_cmd))
            
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
                logger.error(self.msg.get("command_failed_return_code", code=return_code))
                raise CommandExecutionError(self.msg.get("command_failed_return_code", code=return_code))

            logger.success(self.msg.get("successfully_setup_spec", path=self.spec_cfg_path, tune_type=tune_type.name, input_type=input_type.name))

            spec_log_path = self.utils.create_spec_setup_log_path(output_log, 
                self.spec_cfg_path, tune_type, input_type)
            return spec_log_path
            
        except subprocess.CalledProcessError as e:
            logger.error(self.msg.get("command_failed", error=e.stderr))
            raise CommandExecutionError(self.msg.get("command_failed", error=e.stderr))
        except Exception as e:
            logger.error(self.msg.get("command_execute_failed", error=str(e)))
            raise CommandExecutionError(self.msg.get("command_execute_failed", error=str(e)))


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
            logger.warning(self.msg.get("no_starting_run_found"))

        # 替换路径和目录名
        processed_commands = []
        for line in commands:
            # 删除cd本目录命令
            line = line.replace(f"cd {src_dir}", "")
            # 替换完整路径
            line = line.replace(src_dir, ".")
            # 替换目录名
            line = line.replace(f"../{src_dir_name}/", "./")
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

        logger.success(self.msg.get("successfully_created_file", path=output_file))
        
        return True

    def execute_specdiff(self, src_dir: str, dest_dir: str, input_type: InputType) -> bool:
        """
        执行specinvoke命令解析compare.cmd文件，生成specdiff验证脚本
        
        类似于execute_specinvoke，但解析的是compare.cmd文件，
        提取specdiff命令用于验证测试输出正确性。
        
        Args:
            src_dir (str): 源目录路径，包含compare.cmd文件
            dest_dir (str): 目标目录路径，生成的脚本将保存在此
            input_type (InputType): 输入数据集类型
            
        Returns:
            bool: 如果成功创建specdiff脚本文件则返回True
            
        Note:
            - 生成的脚本会去除cd命令和绝对路径引用
            - 参考输出文件会被复制到specdiff_output目录
            - 脚本具有可执行权限(0o755)
        """
        import shutil
        
        specinvoke = os.path.join(self.spec_dir, "bin", "specinvoke")
        specinvoke_cmd = f"{specinvoke} -nn compare.cmd"
        
        src_dir_name = os.path.basename(src_dir)
        
        commands = self.utils.execute_commands(specinvoke_cmd, dest_dir)
        start_index = -1
        
        for i, line in enumerate(commands):
            if line.strip().startswith("# Starting run"):
                start_index = i
                break
        
        if start_index != -1:
            commands = commands[start_index:]
        else:
            logger.warning(self.msg.get("no_starting_run_found"))
        
        specdiff_output_dir = os.path.join(dest_dir, "specdiff_output")
        os.makedirs(specdiff_output_dir, exist_ok=True)
        
        processed_commands = []
        for line in commands:
            line = line.replace(f"cd {src_dir}", "")
            line = line.replace(src_dir, ".")
            line = line.replace(f"../{src_dir_name}/", "./")
            line = line.replace(f"specperl {self.spec_dir}/bin/specdiff", "specdiff")
            
            if line.strip().startswith("specdiff") and ">" in line:
                parts = line.strip().split()
                for part in parts:
                    if os.path.isabs(part) and os.path.exists(part):
                        ref_output_path = part
                        ref_filename = os.path.basename(ref_output_path)
                        dest_path = os.path.join(specdiff_output_dir, ref_filename)
                        shutil.copy2(ref_output_path, dest_path)
                        line = line.replace(ref_output_path, f"specdiff_output/{ref_filename}")
                        break
            
            if not line.startswith("specinvoke") and line.strip():
                processed_commands.append(line)
        
        if not processed_commands:
            logger.warning(self.msg.get("no_specdiff_commands_found"))
            return False
        
        output_file = os.path.join(dest_dir, f"specdiff_{input_type.name}.sh")
        with open(output_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("\n".join(processed_commands))
        
        os.chmod(output_file, 0o755)
        
        logger.success(self.msg.get("successfully_created_file", path=output_file))
        
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
            raise CommandExecutionError(self.msg.get("spec_cmd_not_exist", path=spec_cmd))
        
        logger.debug(self.msg.get("spec_env_check_passed", path=self.spec_dir))
        return True

    def _get_bench_dir_prefix(self, action_type: ActionType, tune_type: TuneType,
                              input_type: InputType, spec_mode: SPECMode) -> str:
        """
        获取基准测试目录前缀

        根据动作类型、优化级别、输入类型和运行模式构建目录前缀。
        子类可重写此方法以提供版本特定的目录前缀格式。

        Args:
            action_type (ActionType): 动作类型(build/run)
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)

        Returns:
            str: 目录前缀字符串

        Note:
            默认实现适用于SPEC2006格式：
            - 构建目录前缀: build_{tune_type}_{label}
            - 运行目录前缀: run_{tune_type}_{input_type}_{label}
        """
        if action_type == ActionType.build:
            return f"{action_type.name}_{tune_type.name}_{self.label}"
        else:
            return f"{action_type.name}_{tune_type.name}_{input_type.name}_{self.label}"

    def get_bench_path(self, action_type: ActionType, tune_type: TuneType,
                       input_type: InputType, spec_mode: SPECMode) -> List[str]:
        """
        获取基准测试的构建或运行目录路径列表

        根据动作类型、优化级别、输入类型等参数，查找并返回匹配的基准测试目录。
        目录命名格式遵循SPEC规范。

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
            - 运行目录格式由子类 _get_bench_dir_prefix 方法决定
            - 如果找到多个匹配目录，选择编号最大的(最新的)
        """
        if self.debug_mode:
            logger.debug(self.msg.get("get_bench_dir_with"))
            logger.debug(self.msg.get("action_type_info", value=action_type.name))
            logger.debug(self.msg.get("tune_type_info_debug", value=tune_type.name))
            logger.debug(self.msg.get("input_type_info_debug", value=input_type.name))
            logger.debug(self.msg.get("spec_mode_info_debug", value=spec_mode.name))

        if action_type == ActionType.build:
            bench_parent_dir = self.spec_build_dir
        else:
            bench_parent_dir = self.spec_run_dir

        bench_dir_perfix = self._get_bench_dir_prefix(action_type, tune_type, input_type, spec_mode)

        selected_bench_dir = []

        for bench_dir in os.listdir(self.spec_bench_path):
            if bench_dir in self.spec_bench_list:
                bench_run_dir = os.path.join(self.spec_bench_path, bench_dir, bench_parent_dir)
                if self.debug_mode:
                    logger.debug(self.msg.get("bench_run_dir", bench=bench_dir, path=bench_run_dir))

                run_dir_path_list = []

                pattern = re.compile(rf"^{re.escape(bench_dir_perfix)}\.\d{{4}}$")

                if not os.path.isdir(bench_run_dir):
                    logger.warning(self.msg.get("directory_not_exist", path=bench_run_dir))
                    continue

                for run_dir in os.listdir(bench_run_dir):
                    if pattern.match(run_dir):
                        run_dir_path_list.append(os.path.join(bench_run_dir, run_dir))

                if len(run_dir_path_list) == 0:
                    logger.warning(self.msg.get("bench_not_found_in", bench=os.path.basename(bench_dir), prefix=bench_dir_perfix))
                elif len(run_dir_path_list) > 1:
                    logger.warning(self.msg.get("bench_found_multiple", bench=os.path.basename(bench_dir), prefix=bench_dir_perfix))
                    for run_dir_path in run_dir_path_list:
                        logger.debug(self.msg.get("found_path", path=run_dir_path))
                    max_num = 0
                    selected = run_dir_path_list[0]
                    for run_dir_perfix in run_dir_path_list:
                        if run_dir_perfix.split(".")[-1].isnumeric():
                            if int(run_dir_perfix.split(".")[-1]) > max_num:
                                max_num = int(run_dir_perfix.split(".")[-1])
                                selected = run_dir_perfix
                    selected_bench_dir.append(selected)
                    logger.warning(self.msg.get("bench_using", bench=os.path.basename(bench_dir), selected=selected))
                else:
                    selected_bench_dir.append(run_dir_path_list[0])
                    logger.debug(self.msg.get("bench_using", bench=os.path.basename(bench_dir), selected=run_dir_path_list[0]))

        return selected_bench_dir

    def _build_run_command(self) -> List[str]:
        """
        构建SPEC运行命令

        根据SPEC版本构建runspec或runcpu命令及参数。
        子类必须实现此方法以提供版本特定的命令构建逻辑。

        Returns:
            List[str]: SPEC命令及参数列表

        Raises:
            NotImplementedError: 基类未实现此方法，子类必须重写
        """
        raise NotImplementedError("子类必须实现 _build_run_command 方法")

    def run_spec_directly(self, output_dir: str) -> Dict:
        """
        直接运行SPEC测试
        
        调用runspec/runcpu命令直接执行SPEC基准测试，无需打包。
        测试完成后返回结果信息。
        
        Args:
            output_dir (str): 结果输出目录
            
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
            - 执行前会自动source SPEC安装目录下的shrc文件，初始化Perl和SPEC运行环境
        """
        self._check_spec_environment()
        
        spec_cmd = self._build_run_command()
        
        os.makedirs(output_dir, exist_ok=True)
        log_file = os.path.join(output_dir, "spec_run.log")
        
        result = {
            "success": False,
            "output_dir": output_dir,
            "log_file": log_file,
            "return_code": -1,
            "error_message": ""
        }
        
        shrc_path = os.path.join(self.spec_dir, "shrc")
        
        shell_cmd = f"source {shrc_path} && {' '.join(spec_cmd)}"
        
        logger.info(self.msg.get("start_running_spec", cmd=' '.join(spec_cmd)))
        logger.info(self.msg.get("result_output_dir", path=output_dir))
        
        process = None
        try:
            with open(log_file, 'w') as log_f:
                process = subprocess.Popen(
                    ["bash", "-c", shell_cmd],
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
                    logger.success(self.msg.get("spec_test_completed", path=output_dir))
                else:
                    result["error_message"] = self.msg.get("command_failed_return_code", code=return_code)
                    logger.error(result["error_message"])
                    
        except KeyboardInterrupt:
            if process:
                process.terminate()
                process.wait()
            result["error_message"] = self.msg.get("user_interrupted_test")
            logger.warning(self.msg.get("user_interrupted_test"))
            raise CommandExecutionError(self.msg.get("user_interrupted_test"))
        except Exception as e:
            result["error_message"] = str(e)
            logger.error(self.msg.get("spec_command_failed", error=str(e)))
            raise CommandExecutionError(self.msg.get("spec_command_failed", error=str(e)))
        
        return result

