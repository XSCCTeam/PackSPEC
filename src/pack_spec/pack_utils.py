"""
PackSPEC工具类模块

本模块提供了PackSPEC工具的辅助功能，包括：
1. 配置文件读写：支持JSON格式的配置文件，自动处理枚举类型序列化/反序列化
2. 文件操作：复制文件、创建目录、处理路径等
3. 脚本生成：生成测试运行脚本、计算分数脚本、消息通知脚本等
4. 命令执行：执行外部命令并捕获输出

主要类：
- EnumEncoder: 自定义JSON编码器，支持枚举类型序列化
- EnumDecoder: 自定义JSON解码器，支持枚举类型反序列化
- PackUtils: 工具类，提供各种辅助方法

主要函数：
- str_to_enum(): 字符串转枚举
- convert_dict_enums(): 字典字段枚举转换
- save_pack_spec_cfg(): 保存配置文件
- load_pack_spec_cfg(): 加载配置文件
"""

import os
import sys
import json
import shlex
from enum import Enum
from typing import Any, Union, Optional

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode,
    PackSPECError, FileOperationError, CommandExecutionError,
    CURRENT_DATE, DEFAULT_CORE_NUM, DEFAULT_LLVM_PROFDATA_PATH,
    DEFAULT_AUTO_MODE,
    SCRIPTS_PATH, GENERATED_FILES_PATH, logger, QEMU_CMD, QEMU_PATH,
    LogLanguage, LogMessages, get_log_messages, DEFAULT_LOG_LANGUAGE
)
import subprocess
import shutil
from typing import List, Dict, Type


def is_numeric(s: str) -> bool:
    """
    检查字符串是否为有效数字
    
    Args:
        s (str): 要检查的字符串
        
    Returns:
        bool: 如果字符串可以转换为浮点数则返回True，否则返回False
        
    Example:
        >>> is_numeric("123.45")
        True
        >>> is_numeric("abc")
        False
    """
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


class EnumEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，支持枚举类型序列化
    
    将枚举类型转换为其名称字符串进行存储。
    
    Example:
        >>> import json
        >>> data = {"tune_type": TuneType.base}
        >>> json.dumps(data, cls=EnumEncoder)
        '{"tune_type": "base"}'
    """
    def default(self, obj: Any) -> Union[str, Any]:
        """
        重写default方法，处理枚举类型的序列化
        
        Args:
            obj (Any): 要序列化的对象
            
        Returns:
            Union[str, Any]: 枚举类型返回其名称字符串，其他类型调用父类方法
        """
        if isinstance(obj, Enum):
            return obj.name
        return super().default(obj)


class EnumDecoder(json.JSONDecoder):
    """
    自定义JSON解码器，支持将字符串转换为枚举类型
    
    根据配置字段名智能判断应该使用哪个枚举类进行转换。
    
    Attributes:
        FIELD_TO_ENUM (dict): 字段名到枚举类的映射字典
        
    Example:
        >>> import json
        >>> json_str = '{"tune_type": "base"}'
        >>> data = json.loads(json_str, cls=EnumDecoder)
        >>> data["tune_type"]
        <TuneType.base: 1>
    """
    
    FIELD_TO_ENUM = {
        'spec_name': SPECName,
        'tune_type': TuneType,
        'input_type': InputType,
        'spec_mode': SPECMode,
    }
    """字段名到枚举类的映射，用于自动转换"""

    def __init__(self, *args, **kwargs):
        """初始化解码器，设置object_hook"""
        super().__init__(*args, object_hook=self._object_hook, **kwargs)
    
    def _object_hook(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """对象钩子，处理字典对象"""
        return self._convert_enums(obj)
    
    def _convert_enums(self, obj: Any, parent_key: str = None) -> Any:
        """
        递归转换对象中的枚举字段
        
        Args:
            obj (Any): 要转换的对象
            parent_key (str, optional): 父级键名
            
        Returns:
            Any: 转换后的对象
        """
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = self._convert_field(key, value)
            return result
        elif isinstance(obj, list):
            return [self._convert_enums(item) for item in obj]
        return obj
    
    def _convert_field(self, key: str, value: Any) -> Any:
        """
        根据字段名和值进行枚举转换
        
        Args:
            key (str): 字段名
            value (Any): 字段值
            
        Returns:
            Any: 转换后的值
        """
        if not isinstance(value, str):
            return self._convert_enums(value, key)
        
        if key in self.FIELD_TO_ENUM:
            enum_class = self.FIELD_TO_ENUM[key]
            converted = self._str_to_enum(value, enum_class)
            if converted is not None:
                return converted
        
        return self._convert_enums(value, key)
    
    def _str_to_enum(self, value: str, enum_class: Type[Enum]) -> Optional[Enum]:
        """
        将字符串转换为指定枚举类
        
        Args:
            value (str): 字符串值
            enum_class (Type[Enum]): 枚举类
            
        Returns:
            Optional[Enum]: 枚举值，转换失败返回None
        """
        try:
            return enum_class[value]
        except KeyError:
            return None


def str_to_enum(value: str, enum_class: type) -> Enum:
    """
    将字符串转换为枚举类型
    
    Args:
        value (str): 字符串值
        enum_class (type): 枚举类
        
    Returns:
        Enum: 枚举值，如果转换失败则返回原始字符串
    """
    try:
        return enum_class[value]
    except (KeyError, AttributeError):
        return value


def convert_dict_enums(data: Dict[str, Any], enum_fields: Dict[str, type]) -> Dict[str, Any]:
    """
    将字典中的指定字段转换为枚举类型
    
    Args:
        data (Dict[str, Any]): 原始字典数据
        enum_fields (Dict[str, type]): 字段名到枚举类的映射
        
    Returns:
        Dict[str, Any]: 转换后的字典
    """
    result = {}
    for key, value in data.items():
        if key in enum_fields and isinstance(value, str):
            result[key] = str_to_enum(value, enum_fields[key])
        else:
            result[key] = value
    return result


def save_pack_spec_cfg(pack_spec_cfg: dict, pack_generated_files_path: str):
    """
    保存PackSPEC配置文件
    
    Args:
        pack_spec_cfg (dict): 配置字典
        pack_generated_files_path (str): 配置文件保存路径
        
    Returns:
        str: 配置文件的完整路径
    """
    pack_spec_cfg_path = os.path.join(pack_generated_files_path, "pack_spec.cfg")
    with open(pack_spec_cfg_path, "w") as f:
        json.dump(pack_spec_cfg, f, indent=4, cls=EnumEncoder)
    return pack_spec_cfg_path


def load_pack_spec_cfg(pack_spec_cfg_path: str) -> dict:
    """
    加载PackSPEC配置文件
    
    Args:
        pack_spec_cfg_path (str): 配置文件路径
        
    Returns:
        dict: 加载的配置字典，枚举字段已自动转换
    """
    with open(pack_spec_cfg_path, "r") as f:
        pack_spec_cfg = json.load(f, cls=EnumDecoder)
    return pack_spec_cfg


class PackUtils:
    """
    PackSPEC工具类
    
    提供文件操作、脚本生成、命令执行等辅助功能。
    
    Attributes:
        pack_name (str): 打包任务名称
        logger (Any): 日志记录器实例
        init_date (str): 初始化日期
        overwrite_confirmed (bool): 用户是否已确认覆盖
        
    Example:
        >>> utils = PackUtils(config, logger)
        >>> utils.copy_file_to_target_dir(src, dest)
    """
    logger: Any

    def __init__(self, config: dict, logger: Any):
        """
        初始化PackUtils实例
        
        Args:
            config (dict): 配置字典，需要包含task配置块或pack_name字段
            logger (Any): 日志记录器实例
        """
        # 支持新的配置结构（task配置块）和旧的配置结构（顶层pack_name）
        task_config = config.get('task', {})
        pack_config = config.get('pack_config', {})
        msg_config = config.get('msg_config', {})
        self.pack_name = task_config.get('pack_name', config.get('pack_name', 'packspec'))
        self.auto_mode = pack_config.get('auto_mode', DEFAULT_AUTO_MODE)
        self.logger = logger
        self.init_date = config.get('date', CURRENT_DATE)
        self.overwrite_confirmed = False
        
        # 日志语言配置
        language_str = msg_config.get('log_language', 'zh').lower()
        if language_str in ('zh', 'chinese', 'cn'):
            self.log_language = LogLanguage.zh
        elif language_str in ('en', 'english'):
            self.log_language = LogLanguage.en
        else:
            self.log_language = DEFAULT_LOG_LANGUAGE
        self.msg = get_log_messages(self.log_language)

    def save_pack_spec_cfg(self, pack_spec_cfg: dict):
        """
        保存PackSPEC配置文件
        """
        pack_spec_cfg_path = self.get_pack_generated_file_path()
        pack_spec_cfg["date"] = self.init_date
        with open(pack_spec_cfg_path, "w") as f:
            json.dump(pack_spec_cfg, f, indent=4, cls=EnumEncoder)
        self.logger.info(self.msg.get("config_saved", path=pack_spec_cfg_path))


    def get_bench_dir(self, bench_name: str, bench_dirs: List[str]) -> str:
        """
        从基准测试目录列表中查找指定名称的基准测试目录
        
        Args:
            bench_name (str): 基准测试名称
            bench_dirs (List[str]): 基准测试目录列表
            
        Returns:
            str: 找到的基准测试目录路径，如果未找到则返回空字符串
        """
        for bench_dir in bench_dirs:
            dir_bench_name = os.path.basename(
                os.path.dirname(
                    os.path.dirname(bench_dir)))
            if dir_bench_name == bench_name:
                return bench_dir
        self.logger.warning(self.msg.get("bench_dir_not_found", bench_name=bench_name))
        return ""

    def get_dest_dir(self, profile_gen: bool, auto_mode: bool, pack_mode: PACKMode,
                     spec_name: SPECName, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> str:
        """
        获取基准测试打包的目标目录路径
        
        Args:
            profile_gen (bool): 是否生成profile
            auto_mode (bool): 是否自动模式
            pack_mode (PACKMode): 打包模式
            spec_name (SPECName): SPEC基准测试版本
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            spec_mode (SPECMode): 运行模式
            
        Returns:
            str: 目标目录路径
            
        Note:
            输出目录格式:
            - auto_mode=True: {GENERATED_FILES_PATH}/{pack_name}/{bin|run}/{spec_name}_{pack_mode}_{pack_name}.{tune_type}_{input_type}_{spec_mode}
            - auto_mode=False: {GENERATED_FILES_PATH}/{date}_{pack_name}/{bin|run}/{date}_{spec_name}_{pack_mode}_{pack_name}.{tune_type}_{input_type}_{spec_mode}
        """
        test_name = f"{self.pack_name}.{tune_type.name}_{input_type.name}_{spec_mode.name}"
        dest_bench_name = f"{spec_name.name}_{pack_mode.name}_{test_name}"
        
        if not auto_mode:
            dest_bench_name = f"{self.init_date}_{dest_bench_name}"
        
        if profile_gen:
            dest_bench_name = f"{dest_bench_name}_profilegen"

        if pack_mode == PACKMode.bin:
            subdir = "bin"
        else:
            subdir = "run"

        dest_bench_dir = os.path.join(self.get_pack_generated_dir_path(), subdir, dest_bench_name)
        return dest_bench_dir

    def get_spec_log_file_path(self, spec_dir: str, spec_log_file: str) -> str:
        """
        从SPEC日志文件中获取实际的日志文件路径
        
        Args:
            spec_dir (str): SPEC目录路径
            spec_log_file (str): SPEC日志文件路径
            
        Returns:
            str: 实际的日志文件路径，如果未找到则返回空字符串
        """
        marked_line = f"The log for this run is in {spec_dir}"
        try:
            with open(spec_log_file, "r") as f:
                spec_log = f.readlines()
            for spec_log_line in spec_log:
                if spec_log_line.startswith(marked_line):
                    self.logger.debug(self.msg.get("spec_log_found", file=spec_log_file))
                    return spec_log_line.replace("The log for this run is in ", "").strip()
            self.logger.debug(self.msg.get("spec_log_marked_line_not_found", file=spec_log_file))
            return ""
        except Exception as e:
            self.logger.debug(self.msg.get("spec_log_parse_error", file=spec_log_file, error=str(e)))
            return ""
    
    def get_run_script_name(self, profile_gen: bool, input_type: InputType, suffix: str = "") -> str:
        """
        获取运行脚本的名称
        
        Args:
            profile_gen (bool): 是否生成profile
            input_type (InputType): 输入数据集类型
            suffix (str, optional): 脚本名称后缀，默认为空
            
        Returns:
            str: 运行脚本的完整名称
        """
        script_name = ""
        if profile_gen:
            script_name = f"profile_gen_{input_type.name}"
        else:
            script_name = f"test_{input_type.name}"
        if suffix:
            script_name = f"{script_name}_{suffix}"
        return f"{script_name}.sh"

    #
    # 打包生成的配置文件目录
    #
    def get_pack_generated_dir_path(self) -> str:
        """
        获取打包生成的目录路径
        
        目录名称格式:
        - auto_mode=True: {pack_name}（不包含日期，便于自动化脚本预测路径）
        - auto_mode=False: {date}_{pack_name}（包含日期，避免不同日期的生成互相覆盖）
        
        例如:
        - auto_mode=True: x86_llvm19_novec_wll
        - auto_mode=False: 260408_x86_llvm19_novec_wll
        
        Returns:
            str: 目录的完整路径
        """
        if self.auto_mode:
            return os.path.join(GENERATED_FILES_PATH, self.pack_name)
        else:
            return os.path.join(GENERATED_FILES_PATH, f"{self.init_date}_{self.pack_name}")

    def get_pack_generated_file_path(self) -> str:
        """
        获取打包生成的配置文件路径
        
        文件名称格式:
        - auto_mode=True: {pack_name}.json（不包含日期，便于自动化脚本预测路径）
        - auto_mode=False: {date}_{pack_name}.json（包含日期）
        
        Returns:
            str: 配置文件的完整路径
        """
        if self.auto_mode:
            return os.path.join(self.get_pack_generated_dir_path(), f"{self.pack_name}.json")
        else:
            return os.path.join(self.get_pack_generated_dir_path(), f"{self.init_date}_{self.pack_name}.json")
    
    def create_generated_dir(self, auto_mode: bool = False):
        """
        创建生成的文件目录
        """
        os.makedirs(GENERATED_FILES_PATH, exist_ok=True)
        self.logger.info(self.msg.get("generated_dir_created", path=GENERATED_FILES_PATH))
        pack_generated_dir_path = self.get_pack_generated_dir_path()
        # 检查目录是否已存在
        if os.path.exists(pack_generated_dir_path):
            self.logger.warning(self.msg.get("pack_dir_exists", path=pack_generated_dir_path))
            if not auto_mode and not self.overwrite_confirmed:
                self.logger.debug(self.msg.get("continue_prompt"))
                choice = input(self.msg.get("continue_prompt"))
            if auto_mode == True or self.overwrite_confirmed or choice.lower() == 'y':
                self.overwrite_confirmed = True
                os.makedirs(pack_generated_dir_path, exist_ok=True)
                self.logger.info(self.msg.get("pack_dir_created", path=pack_generated_dir_path))
            else:
                self.logger.error(self.msg.get("operation_canceled"))
                raise PackSPECError(self.msg.get("operation_canceled"))
        else:
            os.makedirs(pack_generated_dir_path, exist_ok=False)
            self.logger.info(self.msg.get("pack_dir_created", path=pack_generated_dir_path))
        
        return pack_generated_dir_path

    #
    # 打包生成的SPEC setup日志文件目录
    #
    def get_spec_setup_log_path(self, spec_cfg: str, tune_type: TuneType, input_type: InputType) -> str:
        """
        获取SPEC setup日志文件的路径
        
        Args:
            spec_cfg (str): SPEC配置文件名
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            
        Returns:
            str: SPEC setup日志文件的完整路径
        """
        spec_cfg_filename = os.path.basename(spec_cfg).replace('.cfg', '')
        spec_log_file = f"{spec_cfg_filename}.{tune_type.name}_{input_type.name}.setuplog"
        spec_log_path = os.path.join(self.get_pack_generated_dir_path(), spec_log_file)
        return spec_log_path

    def create_spec_setup_log_path(self, log_content: str, 
                                   spec_cfg: str, tune_type: TuneType, input_type: InputType) -> str:
        """
        创建SPEC setup日志文件
        
        Args:
            log_content (str): 日志内容列表
            spec_cfg (str): SPEC配置文件名
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            
        Returns:
            str: 创建的日志文件路径
        """
        spec_log_path = self.get_spec_setup_log_path(spec_cfg, tune_type, input_type)
        with open(spec_log_path, "w") as f:
            f.write("\n".join(log_content))
        return spec_log_path
    
    def create_dest_dir(self, profile_gen: bool, auto_mode: bool, pack_mode: PACKMode,
                        spec_name: SPECName, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode) -> str:
        """
        创建基准测试打包的目标目录
        
        Args:
            profile_gen (bool): 是否生成profile
            auto_mode (bool): 是否自动模式
            pack_mode (PACKMode): 打包模式
            spec_name (SPECName): SPEC基准测试版本
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            spec_mode (SPECMode): 运行模式
            
        Returns:
            str: 创建的目标目录路径
            
        Raises:
            PackSPECError: 当用户取消目录覆盖操作时抛出
        """
        dest_bench_dir = self.get_dest_dir(profile_gen, auto_mode, pack_mode,
                                           spec_name, tune_type, input_type, spec_mode)
        if os.path.exists(dest_bench_dir):
            self.logger.warning(self.msg.get("dest_dir_exists", path=dest_bench_dir))
            if not auto_mode and not self.overwrite_confirmed:
                self.logger.debug(self.msg.get("overwrite_prompt"))
                choice = input(self.msg.get("overwrite_prompt"))
            if auto_mode == True or self.overwrite_confirmed or choice.lower() == 'y':
                self.overwrite_confirmed = True
                self.logger.debug(self.msg.get("overwriting_dir", path=dest_bench_dir))
                shutil.rmtree(dest_bench_dir)
                os.makedirs(dest_bench_dir, exist_ok=False)
            else:
                self.logger.error(self.msg.get("operation_canceled_not_overwritten"))
                raise PackSPECError(self.msg.get("operation_canceled_not_overwritten"))
        else:
            self.logger.debug(self.msg.get("creating_dir", path=dest_bench_dir))
            os.makedirs(dest_bench_dir, exist_ok=False)
        return dest_bench_dir

    def create_env_file(self, dest_dir: str, env_name: str) -> None:
        """
        创建环境变量文件
        
        Args:
            dest_dir (str): 目标目录路径
            env_name (str): 环境文件名称（不带后缀）
        """
        try:
            self.logger.info(self.msg.get("env_file_created", name=env_name))
            with open(os.path.join(dest_dir, f"{env_name}.env"), 'w') as f:
                # 将当前环境变量写入文件
                for key, value in os.environ.items():
                    if key not in ["BOSC_API_KEY", "BOSC_AT_USER"]:
                        f.write(f"{key}={value}\n")
        except Exception as e:
            self.logger.error(self.msg.get("env_file_failed", error=str(e)))


    def execute_commands(self, command: str, work_dir: str) -> List[str]:
        """
        执行命令并捕获输出
        
        Args:
            command (str): 要执行的命令字符串
            work_dir (str): 命令执行的工作目录
            
        Returns:
            List[str]: 命令输出的行列表
            
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
        """
        try:
            # 执行命令并捕获输出
            self.logger.debug(self.msg.get("executing_command", command=command))
            result = subprocess.run(
                command.split(),
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            # 处理命令输出
            bash_result = result.stdout.split("\n")
            return bash_result
        except subprocess.CalledProcessError as e:
            self.logger.error(self.msg.get("command_failed", error=e.stderr))
            raise CommandExecutionError(self.msg.get("command_failed", error=e.stderr))
        except Exception as e:
            self.logger.error(self.msg.get("command_execute_failed", error=str(e)))
            raise CommandExecutionError(self.msg.get("command_execute_failed", error=str(e)))
        
    def copy_file_to_target_dir(self, src_path: str, dest_path: str, file_info: str="", error_info: str="") -> bool:
        """
        复制文件到目标目录
        
        Args:
            src_path (str): 源文件路径
            dest_path (str): 目标文件路径
            file_info (str, optional): 文件描述信息，默认为空
            
        Returns:
            bool: 复制成功返回True，失败返回False
        """
        try:
            src_file_name = os.path.basename(src_path)
            dest_file_name = os.path.basename(dest_path)
            shutil.copy2(src_path, dest_path)
            self.logger.debug(self.msg.get("file_copied", info=file_info, src=src_file_name, dest=dest_file_name))
            self.logger.debug(self.msg.get("copying_file", src=src_file_name, from_path=src_path, to_path=dest_path))
            return True
        except Exception as e:
            self.logger.warning(self.msg.get("copy_failed", info=file_info, src=src_path, dest=dest_path, error=str(e)))
            if error_info != "":
                self.logger.warning(f"{error_info}")
            return False

    def copy_script_file_to_target_dir(self, script_name: str, script_target_path: str) -> bool:
        """
        复制脚本文件到目标目录
        
        Args:
            script_name (str): 脚本名称
            script_target_path (str): 目标目录路径
            
        Returns:
            bool: 复制成功返回True，失败返回False
            
        Raises:
            FileOperationError: 当脚本文件不存在时抛出
        """
        src_path = os.path.join(SCRIPTS_PATH, script_name)
        if not os.path.exists(src_path):
            raise FileOperationError(f"脚本文件不存在: {src_path}")
        return self.copy_file_to_target_dir(src_path, script_target_path, f"script {script_name}")

    def copy_pack_log_file_to_target_dir(self, log_target_dir: str) -> bool:
        """
        复制打包日志文件到目标目录
        
        Args:
            log_file_name (str): 日志文件名
            log_target_dir (str): 目标目录路径
            
        Returns:
            bool: 复制成功返回True，失败返回False
        """
        pack_log_file_name = self.get_pack_generated_file_path()
        return self.copy_file_to_target_dir(pack_log_file_name, log_target_dir, f"log file {pack_log_file_name}")

    def use_template_to_create_script(self, template_name: str, script_target_dir: str, replace_dict: Dict[str, str]) -> None:
        """
        使用模板创建脚本文件
        
        Args:
            template_name (str): 模板文件名（带.template后缀）
            script_target_dir (str): 目标目录路径
            replace_dict (Dict[str, str]): 替换字典，key为模板中的占位符，value为替换值
            
        Raises:
            CommandExecutionError: 当创建脚本失败时抛出
        """
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
            self.logger.debug(self.msg.get("script_created", template=template_name, name=script_name, dir=script_target_dir))
        except Exception as e:
            self.logger.error(self.msg.get("script_create_failed", template=template_name, name=script_name, dir=script_target_dir, error=str(e)))
            raise CommandExecutionError(self.msg.get("script_create_failed", template=template_name, name=script_name, dir=script_target_dir, error=str(e)))

    def copy_spec_cfg_and_logs_to_target_dir(self, spec_dir: str, spec_cfg: str, dest_dir: str,
                                             tune_type: TuneType, input_type: InputType) -> None:
        """
        复制SPEC配置文件和日志到目标目录
        
        Args:
            spec_dir (str): SPEC目录路径
            spec_cfg (str): SPEC配置文件名
            dest_dir (str): 目标目录路径
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
        """
        # 复制配置文件至目标目录
        spec_cfg_path = os.path.join(spec_dir, "config", spec_cfg)
        self.copy_file_to_target_dir(spec_cfg_path, dest_dir, "configs")

        # 复制setup log至目标目录
        spec_log_path = self.get_spec_setup_log_path(spec_cfg, tune_type, input_type)
        self.copy_file_to_target_dir(spec_log_path, dest_dir, "spec_setup log", 
                                    self.msg.get("spec_setup_log_warning"))

        # 复制spec log至目标目录
        spec_log_file_path = self.get_spec_log_file_path(spec_dir, spec_log_path)
        if spec_log_file_path != "":
            self.copy_file_to_target_dir(spec_log_file_path, dest_dir, "spec log")

        # 创建env文件至目标目录
        self.create_env_file(dest_dir, "compile")

        self.copy_pack_log_file_to_target_dir(dest_dir)

    def commands_to_cal_score(self, script_target_dir: str, test_clock_rate: float, 
                               score_file: str = "", minimal_mode: bool = False) -> List[str]:
        """
        生成计算分数的命令列表
        
        Args:
            script_target_dir (str): 脚本目标目录
            test_clock_rate (float): 测试CPU主频，用于算分，单位GHz
            score_file (str, optional): 分数输出文件，默认为空
            minimal_mode (bool, optional): 是否启用极简模式，默认为False
            
        Returns:
            List[str]: 计算分数的命令列表
            
        Raises:
            FileOperationError: 当复制算分脚本失败时抛出
        """
        script_name = "cal_score_minimal.sh" if minimal_mode else "cal_score.py"
        if not self.copy_script_file_to_target_dir(script_name, script_target_dir):
            raise FileOperationError(f"Failed to copy {script_name} to target directory.")
        commands = [
            f"# 计算分数{'（极简模式）' if minimal_mode else ''}",
            f"chmod +x {script_name}"
        ]
        if score_file == "":
            commands.append(f"./{script_name} $LOG_FILE {test_clock_rate}")
        else:
            commands.append(f"./{script_name} $LOG_FILE {test_clock_rate} | tee {score_file}")
        commands.append("")
        self.logger.debug(self.msg.get("add_cal_score_commands"))
        return commands

    def commands_to_send_message(self, message: str) -> List[str]:
        """
        生成发送消息的命令列表
        
        Args:
            message (str): 要发送的消息内容
            
        Returns:
            List[str]: 发送消息的命令列表
            
        Note:
            使用环境变量 BOSC_API_KEY 和 BOSC_AT_USER 来保护敏感信息
        """
        commands = [
            "# 发送任务完成信息并at指定用户",
            "# 从环境变量获取敏感信息",
            'BOSC_API_KEY="${BOSC_API_KEY}"',
            'BOSC_AT_USER="${BOSC_AT_USER}"',
            'curl -X POST "http://172.38.8.102:8848/send-message" \\',
            '     -H "api-key: $BOSC_API_KEY" \\',
            '     -H "Content-Type: application/json" \\',
            f'     -d "{{\\"content\\": \\"{message}\\\\n【来自李扬的 HUAWEI Pure 70 Pro Max】\\", \\"at_user_ids\\": [\\"$BOSC_AT_USER\\"]}}"',
            ""
        ]
        self.logger.debug(self.msg.get("add_send_message_commands"))
        return commands

    def commands_to_send_md_message(self, script_target_dir:str, title_message: str, text_message: str, md_path: str) -> List[str]:
        """
        生成发送Markdown格式消息的命令列表
        
        Args:
            script_target_dir (str): 脚本目标目录
            title_message (str): 消息标题
            text_message (str): 消息文本内容
            md_path (str): Markdown文件路径
            
        Returns:
            List[str]: 发送Markdown格式消息的命令列表
            
        Raises:
            FileOperationError: 当复制send_md_message.py失败时抛出
        """
        if not self.copy_script_file_to_target_dir("send_md_message.py", script_target_dir):
            raise FileOperationError("Failed to copy send_md_message.py to target directory.")
        commands = [
            "# 发送MarkDown格式信息并at指定用户",
            "# 从环境变量获取敏感信息",
            'BOSC_API_KEY="${BOSC_API_KEY}"',
            'BOSC_AT_USER="${BOSC_AT_USER}"',
            f"chmod +x send_md_message.py",
            './send_md_message.py --api_key "$BOSC_API_KEY" \\',
            f'     --title "{title_message}" \\',
            f'     --text "{text_message}" \\',
            f'     --md_path "{md_path}" \\',
            '     --at_mobiles "$BOSC_AT_USER"',
            ""
        ]
        self.logger.debug(self.msg.get("add_send_md_message_commands"))
        return commands
    
    def commands_to_collect_profiles(self, script_target_dir: str) -> List[str]:
        """
        生成收集profile文件的命令列表
        
        Args:
            script_target_dir (str): 脚本目标目录
            
        Returns:
            List[str]: 收集profile文件的命令列表
        """
        self.use_template_to_create_script(
            "collect_profiles.sh.template",
            script_target_dir,
            {"<your llvm-profdata abspath>": DEFAULT_LLVM_PROFDATA_PATH}
        )

        commands = [
            "# 收集profile文件",
            f"chmod +x collect_profiles.sh",
            f"./collect_profiles.sh",
            ""
        ]
        self.logger.debug(self.msg.get("add_collect_profiles_commands"))
        return commands

    def commands_to_prepare_run(self, log_name: str, core_num: int, iterations: int, 
                                minimal_mode: bool = False) -> List[str]:
        """
        生成准备运行的命令列表
        
        Args:
            log_name (str): 日志文件名
            core_num (int): 绑定的核心编号，DEFAULT_CORE_NUM表示不绑定
            iterations (int): 测试迭代次数
            minimal_mode (bool): 是否启用极简模式，默认为False
            
        Returns:
            List[str]: 准备运行的命令列表
        """
        if minimal_mode:
            commands = [
                "#!/bin/sh",
                "",
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
        else:
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
        if core_num != DEFAULT_CORE_NUM:
            commands.extend([
                "# 定义绑定核心编号",
                f"CORE_NUM={core_num}"
            ])
        return commands

    def commands_to_run_bench(self, bench_name: str, profile_gen: bool, spec_bench_map: dict, 
                              core_num: int, ref_time: float,
                              tune_type: TuneType, label: str, input_type: InputType,
                              minimal_mode: bool = False) -> List[str]:
        """
        生成运行基准测试的命令列表
        
        Args:
            bench_name (str): 基准测试名称
            profile_gen (bool): 是否生成profile
            spec_bench_map (dict): 基准测试二进制文件映射字典
            core_num (int): 绑定的核心编号，DEFAULT_CORE_NUM表示不绑定
            ref_time (float): 参考时间
            tune_type (TuneType): 优化级别
            label (str): 基准测试标签
            input_type (InputType): 输入数据集类型
            minimal_mode (bool): 是否启用极简模式，默认为False
            
        Returns:
            List[str]: 运行基准测试的命令列表
        """
        if minimal_mode:
            commands = [
                f"printf '\\nRunning {bench_name}...\\n' | tee -a \"$LOG_FILE\"",
                f"printf 'Reftime: {ref_time}\\n' | tee -a \"$LOG_FILE\"",
            ]
        else:
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
        ])
        
        if minimal_mode:
            commands.extend([
                "i=1",
                f"while [ $i -le $TEST_TIMES ]; do",
                f"    printf \"Test {bench_name} #$i:\\n\" | tee -a \"$LOG_FILE\""
            ])
            if core_num != DEFAULT_CORE_NUM:
                commands.append(
                    f"    (time -p taskset -c $CORE_NUM ./run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"")
            else:
                commands.append(
                    f"    (time -p ./run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"")
            commands.extend([
                "    i=$((i + 1))",
                "done",
                f"printf '{bench_name} completed\\n' | tee -a \"$LOG_FILE\"",
            ])
        else:
            commands.extend([
                f"for i in $(seq 1 $TEST_TIMES); do",
                f"    echo \"Test {bench_name} #$i:\" | tee -a \"$LOG_FILE\""
            ])
            if core_num != DEFAULT_CORE_NUM:
                commands.append(
                    f"    (time -p taskset -c $CORE_NUM bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"")
            else:
                commands.append(
                    f"    (time -p bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"")
            commands.extend([
                "done",
                f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
            ])
        return commands


def parse_spec_results(result_dir: str, spec_name: 'SPECName', language: LogLanguage = DEFAULT_LOG_LANGUAGE) -> Dict:
    """
    解析SPEC测试结果
    
    从SPEC测试输出目录中解析测试结果，提取各基准测试的运行时间和分数。
    
    Args:
        result_dir (str): SPEC测试结果目录路径
        spec_name (SPECName): SPEC版本枚举值
        language (LogLanguage): 日志语言配置，默认为中文
        
    Returns:
        Dict: 包含以下键的结果字典：
            - benchmarks (Dict): 各基准测试的结果
            - int_score (float): 整数测试综合分数
            - fp_score (float): 浮点测试综合分数
            - raw_data (List): 原始数据行列表
            
    Note:
        SPEC结果通常保存在 result 目录下的 .sum 文件中
    """
    from src.pack_spec.pack_config import logger
    
    msg = get_log_messages(language)
    
    results = {
        "benchmarks": {},
        "int_score": 0.0,
        "fp_score": 0.0,
        "raw_data": []
    }
    
    result_path = os.path.join(result_dir, "result")
    if not os.path.isdir(result_path):
        logger.warning(msg.get("result_dir_not_found", path=result_path))
        return results
    
    sum_files = [f for f in os.listdir(result_path) if f.endswith('.sum')]
    if not sum_files:
        logger.warning(msg.get("sum_file_not_found", path=result_path))
        return results
    
    for sum_file in sum_files:
        sum_path = os.path.join(result_path, sum_file)
        try:
            with open(sum_path, 'r') as f:
                lines = f.readlines()
            results["raw_data"].extend(lines)
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 4:
                    bench_name = parts[0]
                    if bench_name.startswith(('4', '6')):
                        try:
                            runtime = float(parts[2])
                            score = float(parts[3]) if len(parts) > 3 else 0.0
                            results["benchmarks"][bench_name] = {
                                "runtime": runtime,
                                "score": score
                            }
                        except (ValueError, IndexError):
                            continue
        except Exception as e:
            logger.warning(msg.get("sum_parse_failed", path=sum_path, error=str(e)))
    
    results["int_score"] = calculate_spec_score(
        results["benchmarks"], "int", spec_name
    )
    results["fp_score"] = calculate_spec_score(
        results["benchmarks"], "fp", spec_name
    )
    
    return results


def calculate_spec_score(benchmarks: Dict, bench_type: str, spec_name: 'SPECName') -> float:
    """
    计算SPEC综合分数
    
    根据各基准测试的分数计算综合分数。
    SPEC分数计算使用几何平均数。
    
    Args:
        benchmarks (Dict): 各基准测试的结果字典
        bench_type (str): 基准测试类型，"int" 或 "fp"
        spec_name (SPECName): SPEC版本枚举值
        
    Returns:
        float: 综合分数，如果无法计算则返回0.0
        
    Note:
        SPEC分数 = geometric_mean(reference_time / runtime) * 100
    """
    from src.pack_spec.pack_config import SPECName
    
    int_benches_2006 = [
        "400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk",
        "456.hmmer", "458.sjeng", "462.libquantum", "464.h264ref",
        "471.omnetpp", "473.astar", "483.xalancbmk"
    ]
    fp_benches_2006 = [
        "410.bwaves", "416.gamess", "433.milc", "434.zeusmp", "435.gromacs",
        "436.cactusADM", "437.leslie3d", "444.namd", "447.dealII", "450.soplex",
        "453.povray", "454.calculix", "459.GemsFDTD", "465.tonto", "470.lbm",
        "481.wrf", "482.sphinx3"
    ]
    
    int_benches_2017 = [
        "600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s",
        "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s",
        "648.exchange2_s", "657.xz_s"
    ]
    fp_benches_2017 = [
        "603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s",
        "627.cam4_s", "628.pop2_s", "638.imagick_s", "644.nab_s",
        "649.fotonik3d_s", "654.roms_s"
    ]
    
    if spec_name in [SPECName.spec2006, SPECName.spec2006v1p01]:
        target_benches = int_benches_2006 if bench_type == "int" else fp_benches_2006
    else:
        target_benches = int_benches_2017 if bench_type == "int" else fp_benches_2017
    
    scores = []
    for bench in target_benches:
        if bench in benchmarks and benchmarks[bench]["score"] > 0:
            scores.append(benchmarks[bench]["score"])
    
    if not scores:
        return 0.0
    
    import math
    geometric_mean = math.exp(sum(math.log(s) for s in scores) / len(scores))
    return round(geometric_mean, 2)


def generate_json_report(results: Dict, config: Dict, output_path: str) -> str:
    """
    生成JSON格式的测试报告
    
    Args:
        results (Dict): 测试结果字典
        config (Dict): 测试配置字典
        output_path (str): 输出文件路径
        
    Returns:
        str: 生成的报告文件路径
    """
    from datetime import datetime
    from src.pack_spec.pack_config import CURRENT_DATE, CURRENT_TIME
    
    report = {
        "report_info": {
            "generated_at": datetime.now().isoformat(),
            "date": CURRENT_DATE,
            "time": CURRENT_TIME
        },
        "config": {
            "spec_name": str(config.get("spec_config", {}).get("spec_name", "")),
            "tune_type": str(config.get("spec_config", {}).get("tune_type", "")),
            "input_type": str(config.get("spec_config", {}).get("input_type", "")),
            "spec_mode": str(config.get("spec_config", {}).get("spec_mode", "")),
            "iterations": config.get("spec_config", {}).get("iterations", 0),
        },
        "results": {
            "benchmarks": results.get("benchmarks", {}),
            "int_score": results.get("int_score", 0.0),
            "fp_score": results.get("fp_score", 0.0)
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return output_path


def generate_markdown_report(results: Dict, config: Dict, output_path: str) -> str:
    """
    生成Markdown格式的测试报告
    
    Args:
        results (Dict): 测试结果字典
        config (Dict): 测试配置字典
        output_path (str): 输出文件路径
        
    Returns:
        str: 生成的报告文件路径
    """
    from datetime import datetime
    from src.pack_spec.pack_config import CURRENT_DATE, CURRENT_TIME
    
    lines = [
        "# SPEC CPU 测试报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 测试配置",
        "",
        f"- **SPEC版本**: {config.get('spec_config', {}).get('spec_name', '')}",
        f"- **优化级别**: {config.get('spec_config', {}).get('tune_type', '')}",
        f"- **输入类型**: {config.get('spec_config', {}).get('input_type', '')}",
        f"- **运行模式**: {config.get('spec_config', {}).get('spec_mode', '')}",
        f"- **迭代次数**: {config.get('spec_config', {}).get('iterations', 0)}",
        "",
        "## 测试结果",
        "",
        "### 综合分数",
        "",
        f"| 类型 | 分数 |",
        f"|------|------|",
        f"| 整数测试 (INT) | {results.get('int_score', 0.0):.2f} |",
        f"| 浮点测试 (FP) | {results.get('fp_score', 0.0):.2f} |",
        "",
        "### 各基准测试结果",
        "",
        "| 基准测试 | 运行时间 | 分数 |",
        "|----------|----------|------|",
    ]
    
    benchmarks = results.get("benchmarks", {})
    for bench_name, bench_data in sorted(benchmarks.items()):
        lines.append(
            f"| {bench_name} | {bench_data.get('runtime', 0):.2f} | {bench_data.get('score', 0):.2f} |"
        )
    
    lines.extend([
        "",
        "---",
        f"*报告由 PackSPEC 自动生成*"
    ])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return output_path


def get_qemu_cmd_absolute() -> str:
    """
    获取QEMU命令的绝对路径
    
    将QEMU_CMD环境变量转换为绝对路径，确保生成的脚本可以在任何目录执行。
    如果设置了QEMU_PATH，则使用QEMU_PATH作为QEMU命令的前缀目录。
    
    Returns:
        str: QEMU命令的绝对路径
        
    Note:
        如果设置了QEMU_PATH，则使用 {QEMU_PATH}/{qemu_binary} 作为命令路径
        如果QEMU_CMD已经是绝对路径，则直接返回
        如果QEMU_CMD是相对路径或命令名，则使用which查找绝对路径
    """
    if not QEMU_CMD:
        return ""
    
    qemu_cmd_parts = shlex.split(QEMU_CMD)
    qemu_binary = qemu_cmd_parts[0]
    
    if QEMU_PATH:
        qemu_absolute = os.path.join(QEMU_PATH, qemu_binary)
        if os.path.isfile(qemu_absolute):
            qemu_cmd_parts[0] = qemu_absolute
            return ' '.join(qemu_cmd_parts)
    
    if os.path.isabs(qemu_binary):
        return QEMU_CMD
    
    try:
        absolute_path = shutil.which(qemu_binary)
        if absolute_path:
            qemu_cmd_parts[0] = absolute_path
            return ' '.join(qemu_cmd_parts)
    except Exception:
        pass
    
    return QEMU_CMD


def build_qemu_command(input_type: InputType, 
                       bench_name: str, spec_bench_map: dict, tune_type: TuneType, 
                       label: str, minimal_mode: bool = False) -> List[str]:
    """
    构建QEMU运行命令
    
    使用环境变量QEMU_CMD构建QEMU运行命令。
    
    Args:
        input_type (InputType): 输入数据集类型
        bench_name (str): 基准测试名称
        spec_bench_map (dict): 基准测试二进制文件映射字典
        tune_type (TuneType): 优化级别
        label (str): 配置标签
        minimal_mode (bool): 是否启用极简模式，默认为False
        
    Returns:
        List[str]: QEMU命令列表
        
    Raises:
        ConfigError: 当QEMU_CMD未配置或格式无效时抛出
        
    Note:
        QEMU命令格式: {qemu_cmd} {binary} {args}
    """
    from src.pack_spec.pack_config import ConfigError
    
    if not QEMU_CMD:
        raise ConfigError("未配置QEMU_CMD环境变量，请在.env中设置")
    
    try:
        qemu_cmd_parts = shlex.split(QEMU_CMD)
    except ValueError as e:
        raise ConfigError(f"QEMU_CMD环境变量格式无效: {e}")
    
    if not qemu_cmd_parts:
        raise ConfigError("QEMU_CMD环境变量格式无效")
    
    qemu_binary = qemu_cmd_parts[0]
    if not qemu_binary.startswith("qemu-"):
        logger.warning(f"QEMU命令 '{qemu_binary}' 可能不是有效的QEMU模拟器")
    
    commands = []
    
    commands.append(f"# QEMU模拟器配置")
    commands.append(f"QEMU_PATH=\"{QEMU_PATH if QEMU_PATH else ''}\"")
    commands.append(f"QEMU_CMD=\"{QEMU_CMD if QEMU_CMD else ''}\"")
    
    commands.extend([
        "",
        "# 运行二进制文件",
        f"$QEMU_PATH/$QEMU_CMD ./{spec_bench_map[bench_name]}_{tune_type.name}.{label} < /dev/null"
    ])
    
    return commands


def generate_qemu_verify_script(bench_name: str, dest_dir: str,
                                spec_bench_map: dict, tune_type: TuneType, 
                                label: str, input_type: InputType,
                                data_dir: str, output_dir: str,
                                minimal_mode: bool = False) -> str:
    """
    生成单个基准测试的QEMU验证脚本
    
    读取现有的 run_{input_type}.sh 脚本，将二进制执行命令替换为使用 QEMU 运行，
    用于验证二进制文件的正确性，不统计运行时间。
    
    Args:
        bench_name (str): 基准测试名称
        dest_dir (str): 脚本输出目录
        spec_bench_map (dict): 基准测试二进制文件映射字典
        tune_type (TuneType): 优化级别
        label (str): 配置标签
        input_type (InputType): 输入数据集类型
        data_dir (str): 输入数据目录
        output_dir (str): 输出日志目录
        minimal_mode (bool): 是否启用极简模式，默认为False
        
    Returns:
        str: 生成的脚本文件路径
        
    Note:
        脚本名称格式: verify_{input_type}.sh
        输出日志格式: {output_dir}/{bench_name}_verify.log
    """
    script_path = os.path.join(dest_dir, f"verify_{input_type.name}.sh")
    run_script_path = os.path.join(dest_dir, f"run_{input_type.name}.sh")
    
    script_header = [
        "#!/bin/bash",
        "",
        "# QEMU验证脚本 - 用于验证编译出的二进制文件是否正确",
        "# 注意: 此脚本不统计运行时间，仅验证程序能否正确执行",
        "",
        "set -e",
        "",
        "# 获取脚本所在目录",
        "SCRIPT_DIR=$(cd \"$(dirname \"$0\")\" && pwd)",
        "cd \"$SCRIPT_DIR\"",
        "",
        "# 定义日志文件（使用相对路径）",
        "LOG_FILE=\"$SCRIPT_DIR/logs/{}_verify.log\"".format(bench_name),
        "",
        "echo \"========================================\" | tee \"$LOG_FILE\"",
        f"echo \"QEMU验证测试: {bench_name}\" | tee -a \"$LOG_FILE\"",
        f"echo \"输入类型: {input_type.name}\" | tee -a \"$LOG_FILE\"",
        f"echo \"优化级别: {tune_type.name}\" | tee -a \"$LOG_FILE\"",
        "echo \"========================================\" | tee -a \"$LOG_FILE\"",
        "",
        "# 解除栈限制",
        "ulimit -s unlimited",
        "",
        "# 创建输出目录",
        "mkdir -p \"$SCRIPT_DIR/logs\"",
        "",
        "# QEMU模拟器配置",
        f"QEMU_PATH=\"{QEMU_PATH if QEMU_PATH else ''}\"",
        f"QEMU_CMD=\"{QEMU_CMD if QEMU_CMD else ''}\"",
        "",
    ]
    
    script_footer = [
        "",
        "echo \"\" | tee -a \"$LOG_FILE\"",
        f"echo \"验证完成: {bench_name}\" | tee -a \"$LOG_FILE\"",
        "echo \"日志已保存到: $LOG_FILE\"",
    ]
    
    if os.path.exists(run_script_path):
        with open(run_script_path, 'r', encoding='utf-8') as f:
            run_script_lines = f.readlines()
        
        script_content = script_header.copy()
        script_content.append("# 以下命令从 run_{}.sh 转换而来，使用 QEMU 运行二进制文件".format(input_type.name))
        script_content.append("")
        
        for line in run_script_lines:
            stripped = line.strip()
            if stripped.startswith("#!") or stripped == "":
                continue
            if stripped.startswith("./"):
                qemu_line = "$QEMU_PATH/$QEMU_CMD " + stripped
                script_content.append(qemu_line)
            else:
                script_content.append(stripped)
        
        script_content.extend(script_footer)
    else:
        script_content = script_header.copy()
        script_content.append(f"# 警告: 未找到 run_{input_type.name}.sh，使用简化命令")
        script_content.append("")
        
        qemu_commands = build_qemu_command(
            input_type, bench_name, spec_bench_map, tune_type, label, minimal_mode
        )
        for cmd in qemu_commands:
            if cmd.startswith("#") or cmd == "":
                script_content.append(cmd)
            else:
                script_content.append(cmd)
        script_content.extend(script_footer)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(script_content))
    
    os.chmod(script_path, 0o755)
    
    return script_path


def generate_qemu_verify_all_script(bench_list: List[str], 
                                    dest_dir: str, spec_bench_map: dict,
                                    tune_type: TuneType, label: str, 
                                    input_type: InputType, output_dir: str,
                                    minimal_mode: bool = False,
                                    parallel_jobs: int = 0) -> str:
    """
    生成批量QEMU验证脚本（支持并行执行）
    
    读取每个基准测试的 run_{input_type}.sh 脚本，将二进制执行命令替换为使用 QEMU 运行，
    用于验证所有编译出的二进制文件是否正确。
    
    Args:
        bench_list (List[str]): 基准测试名称列表
        dest_dir (str): 脚本输出目录
        spec_bench_map (dict): 基准测试二进制文件映射字典
        tune_type (TuneType): 优化级别
        label (str): 配置标签
        input_type (InputType): 输入数据集类型
        output_dir (str): 输出日志目录
        minimal_mode (bool): 是否启用极简模式，默认为False
        parallel_jobs (int): 并行任务数，0表示使用CPU核心数，默认为0
        
    Returns:
        str: 生成的脚本文件路径
        
    Note:
        脚本名称格式: verify_{input_type}_all.sh
        每个基准测试的输出保存在各自的日志文件中
        并行执行可大幅提高验证效率
    """
    script_path = os.path.join(dest_dir, f"verify_{input_type.name}_all.sh")
    
    if parallel_jobs <= 0:
        parallel_jobs_str = '$(($(nproc) - 2))'
    else:
        parallel_jobs_str = str(parallel_jobs)
    
    script_content = [
        "#!/bin/bash",
        "",
        "# QEMU批量验证脚本 - 用于验证所有编译出的二进制文件是否正确",
        "# 注意: 此脚本不统计运行时间，仅验证程序能否正确执行",
        "# 支持并行执行以提高验证效率",
        "",
        "set -e",
        "",
        "# 获取脚本所在目录",
        "SCRIPT_DIR=$(cd \"$(dirname \"$0\")\" && pwd)",
        "cd \"$SCRIPT_DIR\"",
        "",
        "# 定义总日志文件（使用相对路径）",
        "TOTAL_LOG=\"$SCRIPT_DIR/logs/verify_all.log\"",
        "",
        "echo \"========================================\" | tee \"$TOTAL_LOG\"",
        f"echo \"QEMU批量验证测试\" | tee -a \"$TOTAL_LOG\"",
        f"echo \"输入类型: {input_type.name}\" | tee -a \"$TOTAL_LOG\"",
        f"echo \"优化级别: {tune_type.name}\" | tee -a \"$TOTAL_LOG\"",
        f"echo \"基准测试数量: {len(bench_list)}\" | tee -a \"$TOTAL_LOG\"",
        f"echo \"并行任务数: {parallel_jobs_str}\" | tee -a \"$TOTAL_LOG\"",
        "echo \"========================================\" | tee -a \"$TOTAL_LOG\"",
        "",
        "# 解除栈限制",
        "ulimit -s unlimited",
        "",
        "# 创建输出目录",
        "mkdir -p \"$SCRIPT_DIR/logs\"",
        "",
        "# QEMU模拟器配置",
        f"QEMU_PATH=\"{QEMU_PATH if QEMU_PATH else ''}\"",
        f"QEMU_CMD=\"{QEMU_CMD if QEMU_CMD else ''}\"",
        "",
        "# 并行任务数（可通过环境变量覆盖）",
        f"PARALLEL_JOBS=${{PARALLEL_JOBS:-{parallel_jobs_str}}}",
        "",
        "# 记录开始时间",
        "START_TIME=$(date +%s)",
        "",
        "# 验证结果统计",
        "TOTAL_COUNT=0",
        "SUCCESS_COUNT=0",
        "FAIL_COUNT=0",
        "",
        "# 当前运行任务数",
        "RUNNING_JOBS=0",
        "",
        "# 结果目录",
        "RESULT_DIR=\"$SCRIPT_DIR/logs/results\"",
        "mkdir -p \"$RESULT_DIR\"",
        "",
        "# 运行单个基准测试的函数",
        "run_bench() {",
        "    local bench_name=\"$1\"",
        "    local bench_log=\"$RESULT_DIR/${bench_name}.log\"",
        "    local bench_status=\"$RESULT_DIR/${bench_name}.status\"",
        "    ",
        "    echo \"[$(date '+%H:%M:%S')] 开始验证: $bench_name\" | tee -a \"$TOTAL_LOG\"",
        "    ",
        "    cd \"$SCRIPT_DIR/$bench_name\"",
        "    ",
        "    if $QEMU_PATH/$QEMU_CMD ./{binary} > \"$bench_log\" 2>&1; then",
        "        echo \"success\" > \"$bench_status\"",
        "        echo \"[$(date '+%H:%M:%S')] ✓ 完成: $bench_name\" | tee -a \"$TOTAL_LOG\"",
        "    else",
        "        echo \"failed\" > \"$bench_status\"",
        "        echo \"[$(date '+%H:%M:%S')] ✗ 失败: $bench_name\" | tee -a \"$TOTAL_LOG\"",
        "    fi",
        "    ",
        "    cd \"$SCRIPT_DIR\"",
        "}",
        "",
        "# 等待任务槽位可用",
        "wait_for_slot() {",
        "    while [ $RUNNING_JOBS -ge $PARALLEL_JOBS ]; do",
        "        wait -n 2>/dev/null || true",
        "        RUNNING_JOBS=$((RUNNING_JOBS - 1))",
        "    done",
        "}",
        "",
        "# 收集所有后台任务",
        "collect_results() {",
        "    wait",
        "    RUNNING_JOBS=0",
        "}",
        "",
    ]
    
    for bench_name in bench_list:
        run_script_path = os.path.join(dest_dir, bench_name, f"run_{input_type.name}.sh")
        binary_name = f"{spec_bench_map.get(bench_name, bench_name)}_{tune_type.name}.{label}"
        
        script_content.extend([
            f"# 验证 {bench_name}",
            "wait_for_slot",
            f"(",
            f"    bench_name=\"{bench_name}\"",
            f"    bench_log=\"$RESULT_DIR/{bench_name}.log\"",
            f"    bench_status=\"$RESULT_DIR/{bench_name}.status\"",
            f"    ",
            f"    echo \"[$(date '+%H:%M:%S')] 开始验证: $bench_name\" | tee -a \"$TOTAL_LOG\"",
            f"    ",
            f"    cd \"$SCRIPT_DIR/{bench_name}\"",
        ])
        
        if os.path.exists(run_script_path):
            with open(run_script_path, 'r', encoding='utf-8') as f:
                run_script_lines = f.readlines()
            
            script_content.append(f"    if (")
            for line in run_script_lines:
                stripped = line.strip()
                if stripped.startswith("#!") or stripped == "":
                    continue
                if stripped.startswith("./"):
                    qemu_line = "        $QEMU_PATH/$QEMU_CMD " + stripped[2:]
                    script_content.append(qemu_line)
                else:
                    script_content.append(f"    {stripped}")
            script_content.append(f"    ) > \"$bench_log\" 2>&1; then")
        else:
            script_content.append(f"    # 警告: 未找到 run_{input_type.name}.sh，使用简化命令")
            script_content.append(f"    if $QEMU_PATH/$QEMU_CMD ./{binary_name} > \"$bench_log\" 2>&1; then")
        
        script_content.extend([
            f"        echo \"success\" > \"$bench_status\"",
            f"        echo \"[$(date '+%H:%M:%S')] ✓ 完成: $bench_name\" | tee -a \"$TOTAL_LOG\"",
            f"    else",
            f"        echo \"failed\" > \"$bench_status\"",
            f"        echo \"[$(date '+%H:%M:%S')] ✗ 失败: $bench_name\" | tee -a \"$TOTAL_LOG\"",
            f"    fi",
            f"    ",
            f"    cd \"$SCRIPT_DIR\"",
            f") &",
            f"RUNNING_JOBS=$((RUNNING_JOBS + 1))",
            f"TOTAL_COUNT=$((TOTAL_COUNT + 1))",
            f"echo \"进度: $TOTAL_COUNT/{len(bench_list)} (运行中: $RUNNING_JOBS)\"",
            f"",
        ])
    
    script_content.extend([
        "# 等待所有任务完成",
        "echo \"\"",
        "echo \"等待所有任务完成...\"",
        "wait",
        "",
        "# 统计结果",
        "for status_file in \"$RESULT_DIR\"/*.status; do",
        "    if [ -f \"$status_file\" ]; then",
        "        status=$(cat \"$status_file\")",
        "        if [ \"$status\" = \"success\" ]; then",
        "            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))",
        "        else",
        "            FAIL_COUNT=$((FAIL_COUNT + 1))",
        "        fi",
        "    fi",
        "done",
        "",
        "# 记录结束时间",
        "END_TIME=$(date +%s)",
        "ELAPSED_TIME=$((END_TIME - START_TIME))",
        "",
        "echo \"\" | tee -a \"$TOTAL_LOG\"",
        "echo \"========================================\" | tee -a \"$TOTAL_LOG\"",
        "echo \"验证完成\" | tee -a \"$TOTAL_LOG\"",
        "echo \"总测试数: $TOTAL_COUNT\" | tee -a \"$TOTAL_LOG\"",
        "echo \"成功: $SUCCESS_COUNT\" | tee -a \"$TOTAL_LOG\"",
        "echo \"失败: $FAIL_COUNT\" | tee -a \"$TOTAL_LOG\"",
        "echo \"总耗时: $ELAPSED_TIME 秒\" | tee -a \"$TOTAL_LOG\"",
        "echo \"========================================\" | tee -a \"$TOTAL_LOG\"",
        "",
        "# 显示失败的测试",
        "if [ $FAIL_COUNT -gt 0 ]; then",
        "    echo \"\"",
        "    echo \"失败的测试:\" | tee -a \"$TOTAL_LOG\"",
        "    for status_file in \"$RESULT_DIR\"/*.status; do",
        "        status=$(cat \"$status_file\")",
        "        if [ \"$status\" = \"failed\" ]; then",
        "            bench_name=$(basename \"$status_file\" .status)",
        "            echo \"  - $bench_name\" | tee -a \"$TOTAL_LOG\"",
        "        fi",
        "    done",
        "fi",
    ])
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(script_content))
    
    os.chmod(script_path, 0o755)
    
    return script_path