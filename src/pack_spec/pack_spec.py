"""
PackSPEC - SPEC CPU基准测试打包工具主模块

本模块提供SPEC CPU基准测试的自动化打包功能，支持SPEC2006和SPEC2017版本。
主要功能包括：
- 自动化打包SPEC基准测试二进制文件和运行环境
- 管理SPEC文件配置和构建参数
- 生成测试脚本和运行环境
- 支持多种输入类型(test/train/ref/all)和优化级别(base/peak/all)
- 支持配置绑核测试和Profile生成

典型用法:
    from pack_spec import PackSPEC, SPECName, TuneType, InputType, SPECMode
    
    config = {
        "task": {
            "pack_name": "my_test",
            "setup_spec": False,
            "pack_binaries": False,
            "pack_benches": False,
        },
        "spec_config": {
            "spec_cfg_path": "/path/to/config.cfg",
            "spec_name": SPECName.spec2017,
            "tune_type": TuneType.base,
            "input_type": InputType.ref,
            "spec_mode": SPECMode.speed,
            "spec_benches": "all",
            "iterations": 3,
        },
        "pack_config": {
            "test_core_num": 4,
            "test_clock_rate": 1.0,
        }
    }
    
    packer = PackSPEC(config)
    packer.setup_spec()
    packer.pack_benches()
"""

import os
import shutil
from typing import Dict

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType, PACKMode, RunMode,
    PackSPECError, ConfigError, FileOperationError, CommandExecutionError, CURRENT_DATE, CURRENT_TIME, DEFAULT_ITERATIONS, DEFAULT_REBUILD,
    DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_PROFILE_GEN,
    DEFAULT_AUTO_MODE, DEFAULT_LLVM_PROFDATA_PATH,
    DEFAULT_RUN_MODE, DEFAULT_REPORT_FORMAT, QEMU_PATH, DEFAULT_VERIFY_MODE, DEFAULT_MINIMAL_MODE, DEFAULT_ALLOW_BASEPEAK, DEFAULT_PACK_BUILDS,
    BOSC_API_KEY, BOSC_AT_USER, logger, parse_log_language, setup_logger
)
from src.pack_spec.pack_utils import PackUtils, load_pack_spec_cfg, parse_spec_results, generate_json_report, generate_markdown_report, generate_qemu_verify_script, generate_qemu_verify_all_script
from src.pack_spec.spec_driver import SPECDriver


class PackSPEC:
    """
    SPEC CPU基准测试打包工具主类
    
    该类是PackSPEC工具的核心类，负责协调SPEC基准测试的编译、打包和测试脚本生成。
    支持SPEC2006和SPEC2017两个版本的基准测试套件。
    
    Attributes:
        pack_name (str): 打包任务名称，用于标识和生成目录
        setup_spec_enabled (bool): 是否执行SPEC编译
        pack_binaries_enabled (bool): 是否打包二进制文件
        pack_benches_enabled (bool): 是否打包完整测试环境
        spec_cfg_path (str): SPEC配置文件的绝对路径
        spec_name (SPECName): SPEC版本枚举值
        tune_type (TuneType): 优化级别枚举值
        input_type (InputType): 输入数据集类型枚举值
        spec_mode (SPECMode): 运行模式枚举值(speed/rate)
        spec_benches (str): 基准测试选择字符串
        iterations (int): 测试迭代次数
        rebuild (bool): 是否重新构建
        test_core_num (int): 测试绑定的核心编号
        test_clock_rate (float): 测试CPU主频(GHz)
        profile_gen (bool): 是否生成Profile模式
        auto_mode (bool): 是否自动模式
        verify_mode (bool): 是否开启QEMU验证模式
        minimal_mode (bool): 是否开启极简模式
        msg_enabled (bool): 是否开启消息发送
        utils (PackUtils): 工具类实例
        spec_driver (SPECDriver): SPEC驱动实例
        
    Example:
        >>> config = {
        ...     "task": {
        ...         "pack_name": "test_pack",
        ...         "setup_spec": False,
        ...         "pack_binaries": False,
        ...         "pack_benches": False,
        ...     },
        ...     "spec_config": {
        ...         "spec_cfg_path": "/path/to/spec.cfg",
        ...         "spec_name": SPECName.spec2017,
        ...         "tune_type": TuneType.base,
        ...         "input_type": InputType.ref,
        ...         "spec_mode": SPECMode.speed,
        ...         "spec_benches": "int",
        ...         "iterations": 3,
        ...     }
        ... }
        >>> packer = PackSPEC(config)
        >>> packer.setup_spec()
        >>> packer.pack_benches()
    """
    def __init__(self, config):
        """
        初始化PackSPEC实例
        
        支持两种初始化方式：
        1. 从配置文件路径加载配置
        2. 从配置字典直接初始化
        
        Args:
            config (str | dict): 配置信息，可以是配置文件路径字符串或配置字典
            
        Raises:
            ValueError: 当config参数类型不正确时抛出
            
        Example:
            >>> # 从字典初始化
            >>> packer = PackSPEC({"pack_name": "test", "spec_cfg_path": "...", ...})
            >>> # 从配置文件初始化
            >>> packer = PackSPEC("/path/to/pack_spec.cfg")
        """
        if isinstance(config, str):
            # 从配置文件路径加载配置
            config = load_pack_spec_cfg(config)
            logger.debug(f"spec_benches: {config['spec_config']['spec_benches']}")
            self.init_date = config.get('date', CURRENT_DATE)
            self.init_pack_spec(config)
            self.log_path = setup_logger(self.utils.get_pack_generated_dir_path())
            
            
        elif isinstance(config, dict):
            self.init_date = CURRENT_DATE
            self.init_pack_spec(config)
            # 从配置字典中提取参数，设置默认值
            self.pack_generated_files_path = self.utils.create_generated_dir(self.auto_mode)
            self.log_path = setup_logger(self.utils.get_pack_generated_dir_path())
            config['date'] = self.init_date
            self.utils.save_pack_spec_cfg(config)
        else:
            raise ValueError("config must be a dict or a path to a config file")
        

    def init_pack_spec(self, config: dict):
        """
        初始化PackSPEC实例的内部配置
        
        从配置字典中提取参数并初始化各个组件，包括：
        - 解析任务配置和SPEC配置路径
        - 设置SPEC版本、优化级别、输入类型等参数
        - 创建对应的SPEC驱动实例(SPEC2006/SPEC2017)
        - 初始化工具类实例
        
        Args:
            config (dict): 配置字典，包含以下键：
                - task: 任务配置子字典
                - spec_config: SPEC相关配置子字典
                - pack_config: 打包相关配置子字典(可选)
                - msg_config: 消息发送配置子字典(可选)
        """
        # 任务配置
        task_config = config.get('task', {})
        self.pack_name = task_config.get('pack_name', '')
        self.setup_spec_enabled = task_config.get('setup_spec', False)
        self.pack_binaries_enabled = task_config.get('pack_binaries', False)
        self.pack_benches_enabled = task_config.get('pack_benches', False)
        self.pack_builds_enabled = task_config.get('pack_builds', DEFAULT_PACK_BUILDS)
        self.run_mode = task_config.get('run_mode', DEFAULT_RUN_MODE)
        
        # SPEC基准测试相关配置
        spec_config = config.get('spec_config', {})
        self.spec_cfg_path = spec_config.get('spec_cfg_path', '')
        self.spec_name = spec_config.get('spec_name', SPECName.spec2006)
        self.tune_type = spec_config.get('tune_type', TuneType.base)
        self.input_type = spec_config.get('input_type', InputType.ref)
        self.spec_mode = spec_config.get('spec_mode', SPECMode.speed)
        self.spec_benches = spec_config.get('spec_benches', 'all')
        self.iterations = spec_config.get('iterations', DEFAULT_ITERATIONS)
        self.rebuild = spec_config.get('rebuild', DEFAULT_REBUILD)
        
        # PackSPEC打包相关配置
        pack_config = config.get('pack_config', {})
        self.test_core_num = pack_config.get('test_core_num', DEFAULT_CORE_NUM)
        self.test_clock_rate = pack_config.get('test_clock_rate', DEFAULT_CLOCK_RATE)
        self.profile_gen = pack_config.get('profile_gen', DEFAULT_PROFILE_GEN)
        self.auto_mode = pack_config.get('auto_mode', DEFAULT_AUTO_MODE)
        self.report_format = pack_config.get('report_format', DEFAULT_REPORT_FORMAT)
        self.verify_mode = pack_config.get('verify_mode', DEFAULT_VERIFY_MODE)
        self.minimal_mode = pack_config.get('minimal_mode', DEFAULT_MINIMAL_MODE)
        self.qemu_verify_parallel_jobs = pack_config.get('qemu_verify_parallel_jobs', 0)
        self.allow_basepeak = pack_config.get('allow_basepeak', DEFAULT_ALLOW_BASEPEAK)

        # 消息发送配置
        msg_config = config.get('msg_config', {})
        self.msg_enabled = msg_config.get('enable_dingtalk_message', False)
        
        # 日志语言配置
        self.log_language, self.msg = parse_log_language(
            msg_config.get('log_language', 'zh')
        )
        
        if self.profile_gen:
            self.iterations = 1
        
        self.utils = PackUtils(config, logger)

        self.spec_driver = SPECDriver.create(
            self.spec_name, self.spec_cfg_path, self.tune_type, self.input_type,
            self.spec_mode, self.spec_benches, self.utils, self.iterations, self.rebuild,
            allow_basepeak=self.allow_basepeak
        )
        if not self.pack_name:
            self.pack_name = self.spec_driver.label if self.spec_driver.label else 'packspec'
        elif self.pack_name != self.spec_driver.label:
            self.spec_driver.label = self.pack_name
            
        self.utils.pack_name = self.pack_name
        self.print_info()


    def print_info(self):
        """
        打印PackSPEC实例的基本信息
        
        输出当前打包任务的配置摘要，包括：
        - 当前时间戳
        - SPEC版本名称和版本号
        - SPEC安装路径
        
        该方法在初始化完成后自动调用，用于确认配置正确性。
        """
        logger.info(" ")
        logger.info("="*80)
        logger.info(self.msg.get("start_packing", name=self.spec_name.name))
        logger.info(self.msg.get("current_time", time=CURRENT_TIME))
        logger.info("-"*80)
        spec_info = self.spec_driver.get_spec_info()
        logger.info(self.msg.get("spec_version", name=spec_info['spec_name'], version=spec_info['spec_version']))
        logger.info(self.msg.get("spec_path", path=spec_info['spec_path']))
        logger.info("="*80)
        logger.info(" ")
        

    def copy_binaries(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode, 
                     dest_binary_dir: str = "") -> str:
        """
        复制SPEC基准测试二进制文件到目标目录
        
        从SPEC安装目录中提取已编译的二进制文件，复制到指定的打包目录。
        二进制文件路径由SPEC驱动根据配置标签自动定位。
        
        Args:
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            dest_binary_dir (str, optional): 目标目录路径，为空则自动生成
            
        Returns:
            str: 二进制文件的目标目录路径
            
        Raises:
            FileOperationError: 当没有二进制文件可复制时抛出
            
        Note:
            目标目录命名格式: {GENERATED_FILES_PATH}/{date}_{pack_name}/bin/{spec_name}_bin_{pack_name}.{tune_type}_{input_type}_{spec_mode}
        """
        src_bench_map = self.spec_driver.get_binary_path_map(tune_type, input_type, spec_mode)

        if dest_binary_dir == "":
            dest_binary_dir = self.utils.create_dest_dir(self.profile_gen, 
                                                         self.auto_mode, 
                                                         PACKMode.bin,
                                                         self.spec_name, 
                                                         tune_type, 
                                                         input_type, 
                                                         spec_mode)

        # 复制二进制文件至目标目录
        copy_num = 0
        for bench_item in src_bench_map.items():
            # 获取基准测试名称（目录的最后两级：如 500.perlbench_r/run_base_test_llvm19-m64）
            bench_name = bench_item[0]
            binary_path = bench_item[1]
            dest_path = os.path.join(dest_binary_dir, bench_name)
            self.utils.copy_file_to_target_dir(binary_path, dest_path, f"{bench_name} binary")
            copy_num += 1
        if copy_num != 0:
            logger.success(self.msg.get("successfully_copied_files", count=copy_num))
        else:
            logger.error(self.msg.get("no_binary_to_copy"))
            raise FileOperationError(self.msg.get("no_binary_to_copy"))

        # 复制配置文件及相关日志至目标目录
        self.utils.copy_spec_cfg_and_logs_to_target_dir(
            self.spec_driver.spec_dir, self.spec_cfg_path, 
            dest_binary_dir, tune_type, input_type)

        return dest_binary_dir


    def copy_benches(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode,
                     with_build: bool = False, dest_bench_dir: str = "", spec_cfg: str = "") -> list:
        """
        复制完整的SPEC基准测试运行环境到目标目录
        
        复制基准测试的运行目录，包括二进制文件、输入数据、配置文件等。
        可选择是否包含构建目录(build目录)。
        同时会生成测试运行脚本和计算分数的脚本。
        
        Args:
            tune_type (TuneType): 优化级别(base/peak)
            input_type (InputType): 输入数据集类型(test/train/ref)
            spec_mode (SPECMode): 运行模式(speed/rate)
            with_build (bool, optional): 是否包含构建目录，默认False
            dest_bench_dir (str, optional): 目标目录路径，为空则自动生成
            spec_cfg (str, optional): SPEC配置文件名，用于复制配置文件
            
        Returns:
            list: 各基准测试的目标目录路径列表
            
        Raises:
            FileOperationError: 当复制失败或没有基准测试可复制时抛出
            
        Note:
            - 目标目录命名格式取决于with_build参数
            - 会自动生成run_{input_type}.sh测试脚本
            - 会自动生成test_{input_type}.sh或profile_gen_{input_type}.sh运行脚本
        """
        # 初始化构建目录路径，当with_build为False时为None
        src_build_bench_dir = None
        if with_build:
            src_build_bench_dir = self.spec_driver.get_bench_path(ActionType.build, tune_type, input_type, spec_mode)
        src_run_bench_dir = self.spec_driver.get_bench_path(ActionType.run, tune_type, input_type, spec_mode)

        if dest_bench_dir == "":
            if with_build:
                dest_bench_dir = self.utils.create_dest_dir(self.profile_gen, self.auto_mode, PACKMode.buildrun,
                                                            self.spec_name, tune_type, input_type, spec_mode)
            else:
                dest_bench_dir = self.utils.create_dest_dir(self.profile_gen, self.auto_mode, PACKMode.run,
                                                            self.spec_name, tune_type, input_type, spec_mode)
 
        dest_dir_list = []
        for bench_name in self.spec_driver.spec_bench_list:
            if with_build:
                src_build_dir = self.utils.get_bench_dir(bench_name, src_build_bench_dir)
                if src_build_dir == "":
                    logger.warning(self.msg.get("cannot_match_bench", bench=bench_name, dir=src_build_bench_dir))
                    continue

            src_run_dir = self.utils.get_bench_dir(bench_name, src_run_bench_dir)
            if src_run_dir == "":
                logger.warning(self.msg.get("cannot_match_bench", bench=bench_name, dir=src_run_bench_dir))
                continue

            dest_dir = os.path.join(dest_bench_dir, bench_name)
            logger.info(self.msg.get("copying_bench", bench=bench_name))
            try:
                if with_build:
                    logger.info(self.msg.get("copy_from_to", from_path=src_build_dir, to_path=dest_dir))
                    shutil.copytree(src_build_dir, dest_dir, symlinks=True)
                    logger.debug(self.msg.get("copy_bench_done", bench=bench_name))
                logger.info(self.msg.get("copy_from_to", from_path=src_run_dir, to_path=dest_dir))
                shutil.copytree(src_run_dir, dest_dir, symlinks=True, dirs_exist_ok=True)
                logger.debug(self.msg.get("copy_bench_done", bench=bench_name))
                dest_dir_list.append(dest_dir)
            except Exception as e:
                logger.error(self.msg.get("copy_bench_failed", bench=bench_name, error=str(e)))
                raise FileOperationError(self.msg.get("copy_bench_failed", bench=bench_name, error=str(e)))

            if self.spec_driver.execute_specinvoke(src_run_dir, dest_dir, input_type):
                logger.success(self.msg.get("run_script_created", path=dest_dir, name=f"run_{input_type.name}.sh"))
            else:
                logger.error(self.msg.get("run_test_script_failed", dir=dest_dir))
                raise CommandExecutionError(self.msg.get("run_test_script_failed", dir=dest_dir))

            self.spec_driver.execute_specdiff(src_run_dir, dest_dir, input_type)

            self.create_test_script(self.spec_driver.label, bench_name, self.test_core_num, dest_dir, tune_type, input_type)

        if dest_dir_list != []:
            logger.success(self.msg.get("successfully_copied_benches", count=len(dest_dir_list)))
        else:
            logger.error(self.msg.get("no_benches_to_copy"))
            raise FileOperationError(self.msg.get("no_benches_to_copy"))
        
        self.create_run_all_script(self.spec_driver.label, self.test_core_num, dest_dir_list, tune_type, input_type)
        self.create_specdiff_all_script(dest_dir_list, input_type)

        # 复制配置文件及相关日志至目标目录
        if spec_cfg != "":
            self.spec_driver.utils.copy_spec_cfg_and_logs_to_target_dir(
                self.spec_driver.spec_dir, spec_cfg, 
                os.path.dirname(dest_dir_list[0]), 
                tune_type, input_type)

        return dest_dir_list

    def _add_score_and_message_commands(self, script_content: list, score_dir: str,
                                         label: str, tune_type: TuneType, input_type: InputType,
                                         name_prefix: str = ""):
        """
        向脚本内容中添加分数计算和消息通知命令
        
        根据是否配置了钉钉机器人和是否为Profile生成模式，
        添加不同的消息通知和分数计算命令。该方法是create_test_script和
        create_run_all_script的公共逻辑提取。
        
        Args:
            script_content (list): 脚本命令列表，会被原地修改
            score_dir (str): 分数计算的目标目录
            label (str): 配置标签
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            name_prefix (str, optional): 消息中的名称前缀，如基准测试名称，默认为空
            
        Note:
            - 当配置了BOSC_API_KEY和BOSC_AT_USER且非极简模式时，会发送钉钉消息
            - Profile生成模式只发送完成消息，不计算分数
            - 非Profile模式会计算分数并发送分数消息
        """
        full_name = f"{name_prefix}.{label}.{tune_type.name}_{input_type.name}" if name_prefix else f"{label}.{tune_type.name}_{input_type.name}"

        if BOSC_API_KEY is not None and BOSC_AT_USER is not None and not self.minimal_mode:
            if self.profile_gen:
                message = f"在 $HOST_NAME 上的 {full_name} Profile 生成完成喵！"
                script_content.append("HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
            else:
                message = f"在 $HOST_NAME 上的 {full_name} 测试完成喵！"
                script_content.append("HOST_NAME=$(hostname)")
                script_content.extend(self.utils.commands_to_send_message(message))
                script_content.extend(self.utils.commands_to_cal_score(score_dir, self.test_clock_rate, "score.txt", self.minimal_mode))
                title_message = f"{full_name} 测试结果"
                text_message = f"在 $HOST_NAME 上的 {full_name} 测试结果喵："
                script_content.extend(self.utils.commands_to_send_md_message(score_dir, title_message, text_message, "score.txt"))
        else:
            script_content.extend(self.utils.commands_to_cal_score(score_dir, self.test_clock_rate, minimal_mode=self.minimal_mode))

    def _write_script_file(self, script_path: str, script_content: list):
        """
        将脚本内容写入文件并设置执行权限
        
        Args:
            script_path (str): 脚本文件路径
            script_content (list): 脚本命令列表
        """
        with open(script_path, 'w') as f:
            f.write("\n".join(script_content))
        os.chmod(script_path, 0o700)

    def create_test_script(self, label: str, bench_name: str, core_num: int, 
                            dest_dir: str, tune_type: TuneType, input_type: InputType, iterations: int = 0):
        """
        为单个基准测试创建运行脚本
        
        生成一个完整的bash脚本，包含：
        - 环境准备命令(解除栈限制等)
        - 基准测试运行命令
        - 分数计算命令
        - 可选的消息通知命令
        
        Args:
            label (str): 配置标签，用于标识二进制文件
            bench_name (str): 基准测试名称，如"600.perlbench_s"
            core_num (int): 绑定的CPU核心编号，DEFAULT_CORE_NUM表示不绑定
            dest_dir (str): 脚本输出目录
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            iterations (int, optional): 迭代次数，为0则使用实例默认值
            
        Note:
            - 脚本名称格式: test_{input_type}.sh 或 profile_gen_{input_type}.sh
            - 如果配置了钉钉机器人，会添加消息通知功能
            - Profile生成模式会额外生成merge_profile.sh脚本
        """

        if iterations == 0:
            iterations = self.iterations
        
        run_test_script = os.path.join(dest_dir, self.utils.get_run_script_name(self.profile_gen, input_type))

        script_content = self.utils.commands_to_prepare_run(
            f"$SCRIPT_DIR/test_{input_type.name}.log", core_num, iterations, self.minimal_mode)

        script_content.extend(
            self.spec_driver.utils.commands_to_run_bench(bench_name, self.profile_gen, self.spec_driver.spec_bench_map,
                                             core_num, self.spec_driver.get_ref_time(bench_name, input_type),
                                             tune_type, label, input_type, self.minimal_mode)
        )

        if self.profile_gen:
            self.utils.use_template_to_create_script(
                "merge_profile.sh.template", 
                dest_dir, 
                {"<your llvm-profdata abspath>": DEFAULT_LLVM_PROFDATA_PATH}
            )

        self._add_score_and_message_commands(script_content, dest_dir, label, tune_type, input_type, name_prefix=bench_name)

        self._write_script_file(run_test_script, script_content)
        logger.info(self.msg.get("created_script_at", path=run_test_script, name=self.utils.get_run_script_name(self.profile_gen, input_type)))
        

    def create_run_all_script(self, label: str, core_num: int, buildrun_bench_dir_list: list, 
                              tune_type: TuneType, input_type: InputType, iterations: int = 0):
        """
        创建批量运行所有基准测试的脚本
        
        生成一个统一的脚本，可以依次运行所有基准测试，并汇总结果。
        该脚本会遍历所有基准测试目录，执行各自的测试脚本。
        
        Args:
            label (str): 配置标签
            core_num (int): 绑定的CPU核心编号
            buildrun_bench_dir_list (list): 基准测试目录路径列表
            tune_type (TuneType): 优化级别
            input_type (InputType): 输入数据集类型
            iterations (int, optional): 迭代次数，为0则使用实例默认值
            
        Note:
            - 脚本名称格式: test_{input_type}_all.sh 或 profile_gen_{input_type}_all.sh
            - Profile生成模式会添加profile收集命令
            - 会计算并输出所有基准测试的总分
        """
        if not buildrun_bench_dir_list:
            logger.warning(self.msg.get("no_benchmark_dirs_to_run"))
            return
            
        if iterations == 0:
            iterations = self.iterations

        # 获取父目录
        parent_dir = os.path.dirname(buildrun_bench_dir_list[0])
        run_all_script = os.path.join(parent_dir, self.utils.get_run_script_name(self.profile_gen, input_type, "all"))
        
        script_content = self.utils.commands_to_prepare_run(
            "$SCRIPT_DIR/run_all.log", core_num, iterations, self.minimal_mode)

        if self.minimal_mode:
            script_content.extend([
                "",
                "# 运行所有基准测试并记录时间",
                "printf \"Starting benchmarks run at $(date)\\n\" | tee -a \"$LOG_FILE\"",
                "",
                "# 依次运行每个基准测试",
                ""
            ])
        else:
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
                self.spec_driver.utils.commands_to_run_bench(bench_name, self.profile_gen, self.spec_driver.spec_bench_map, 
                                                 core_num, self.spec_driver.get_ref_time(bench_name, input_type),
                                                 tune_type, label, input_type, self.minimal_mode)
            )
            script_content.extend([
                "cd $SCRIPT_DIR",
                ""
            ])
        
        if self.minimal_mode:
            script_content.extend([
                "printf '\\nAll benchmarks completed\\n' | tee -a \"$LOG_FILE\"",
                "printf \"Finished at $(date)\\n\" | tee -a \"$LOG_FILE\"",
                ""
            ])
        else:
            script_content.extend([
                "echo -e '\\nAll benchmarks completed' | tee -a \"$LOG_FILE\"",
                "echo \"Finished at $(date)\" | tee -a \"$LOG_FILE\"",
                ""
            ])

        if self.profile_gen:
            # 收集profile
            script_content.extend(self.utils.commands_to_collect_profiles(parent_dir))

        self._add_score_and_message_commands(script_content, parent_dir, label, tune_type, input_type)

        self._write_script_file(run_all_script, script_content)
        logger.success(f"Successfully created {self.utils.get_run_script_name(self.profile_gen, input_type, 'all')} script at {run_all_script}")

    def create_specdiff_all_script(self, buildrun_bench_dir_list: list, input_type: InputType):
        """
        创建批量执行所有基准测试 specdiff 的脚本

        生成一个统一的脚本，依次进入每个基准测试目录并执行其
        specdiff_{input_type}.sh，用于验证整套测试输出。

        Args:
            buildrun_bench_dir_list (list): 基准测试目录路径列表
            input_type (InputType): 输入数据集类型

        Note:
            - 脚本名称格式: specdiff_{input_type}_all.sh
            - 汇总日志名称格式: specdiff_{input_type}_all.log
            - 单个基准测试失败不会中断后续验证，最后统一返回失败状态
        """
        if not buildrun_bench_dir_list:
            logger.warning(self.msg.get("no_benchmark_dirs_to_run"))
            return

        parent_dir = os.path.dirname(buildrun_bench_dir_list[0])
        specdiff_script_name = f"specdiff_{input_type.name}.sh"
        specdiff_all_script = os.path.join(parent_dir, f"specdiff_{input_type.name}_all.sh")
        log_file_name = f"specdiff_{input_type.name}_all.log"

        script_content = [
            "#!/bin/bash",
            "",
            "# 批量执行所有基准测试的 specdiff 验证",
            "SCRIPT_DIR=$(cd \"$(dirname \"$0\")\" && pwd)",
            f"LOG_FILE=\"$SCRIPT_DIR/{log_file_name}\"",
            "",
            "TOTAL_COUNT=0",
            "SUCCESS_COUNT=0",
            "FAIL_COUNT=0",
            "FAILED_BENCHES=\"\"",
            "",
            "echo \"Starting specdiff validation at $(date)\" | tee \"$LOG_FILE\"",
            "",
        ]

        for bench_dir in buildrun_bench_dir_list:
            bench_name = os.path.basename(bench_dir)
            script_content.extend([
                f"TOTAL_COUNT=$((TOTAL_COUNT + 1))",
                f"echo \"\" | tee -a \"$LOG_FILE\"",
                f"echo \"Running specdiff for {bench_name}...\" | tee -a \"$LOG_FILE\"",
                f"if [ ! -f \"$SCRIPT_DIR/{bench_name}/{specdiff_script_name}\" ]; then",
                f"    echo \"ERROR: {bench_name}/{specdiff_script_name} not found\" | tee -a \"$LOG_FILE\"",
                "    FAIL_COUNT=$((FAIL_COUNT + 1))",
                f"    FAILED_BENCHES=\"$FAILED_BENCHES {bench_name}\"",
                "else",
                f"    cd \"$SCRIPT_DIR/{bench_name}\"",
                f"    bash ./{specdiff_script_name} >> \"$LOG_FILE\" 2>&1",
                "    STATUS=$?",
                "    cd \"$SCRIPT_DIR\"",
                "    if [ $STATUS -eq 0 ]; then",
                f"        echo \"{bench_name} specdiff passed\" | tee -a \"$LOG_FILE\"",
                "        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))",
                "    else",
                f"        echo \"{bench_name} specdiff failed with status $STATUS\" | tee -a \"$LOG_FILE\"",
                "        FAIL_COUNT=$((FAIL_COUNT + 1))",
                f"        FAILED_BENCHES=\"$FAILED_BENCHES {bench_name}\"",
                "    fi",
                "fi",
                "",
            ])

        script_content.extend([
            "echo \"\" | tee -a \"$LOG_FILE\"",
            "echo \"Specdiff validation completed at $(date)\" | tee -a \"$LOG_FILE\"",
            "echo \"Total: $TOTAL_COUNT\" | tee -a \"$LOG_FILE\"",
            "echo \"Success: $SUCCESS_COUNT\" | tee -a \"$LOG_FILE\"",
            "echo \"Failed: $FAIL_COUNT\" | tee -a \"$LOG_FILE\"",
            "if [ $FAIL_COUNT -gt 0 ]; then",
            "    echo \"Failed benchmarks:$FAILED_BENCHES\" | tee -a \"$LOG_FILE\"",
            "    exit 1",
            "fi",
            "",
            "exit 0",
        ])

        self._write_script_file(specdiff_all_script, script_content)
        logger.success(f"Successfully created specdiff_{input_type.name}_all.sh script at {specdiff_all_script}")

    def setup_spec(self):
        """
        执行SPEC基准测试的编译和设置
        
        调用SPEC驱动执行setup操作，包括：
        - 将cfg文件复制到generated_files目录（保护源文件）
        - 解析SPEC配置文件
        - 编译基准测试二进制文件
        - 准备运行目录和输入数据
        
        该方法是对spec_driver.run_setup_spec的封装，
        使用实例初始化时配置的tune_type、input_type和rebuild参数。
        
        Note:
            为保护源cfg文件不被修改，setup前会将cfg文件复制到
            generated_files目录，然后使用复制后的文件进行setup操作。
        """
        src_cfg_path = self.spec_cfg_path
        cfg_filename = os.path.basename(src_cfg_path)
        
        dest_cfg_dir = os.path.join(self.utils.get_pack_generated_dir_path(), "cfg")
        os.makedirs(dest_cfg_dir, exist_ok=True)
        dest_cfg_path = os.path.join(dest_cfg_dir, cfg_filename)
        
        shutil.copy2(src_cfg_path, dest_cfg_path)
        logger.info(self.msg.get("cfg_copied_to", src=src_cfg_path, dest=dest_cfg_path))
        
        if self.pack_name and self.pack_name != self.spec_driver.label:
            self.utils.update_cfg_label(dest_cfg_path, self.pack_name, self.spec_name)
            self.spec_driver.label = self.pack_name
        
        self.utils.inject_riscv_x264_submit(dest_cfg_path)
        
        self.spec_driver.spec_cfg_path = dest_cfg_path
        spec_setup_log_path = self.spec_driver.run_setup_spec(self.tune_type, self.input_type, rebuild=self.rebuild)
        
        self.utils.copy_spec_detail_log_to_generated_dir(
            self.spec_driver.spec_dir, spec_setup_log_path, 
            self.utils.get_pack_generated_dir_path())

    def _process_tune_input_combinations(self, func, *args, **kwargs):
        """
        处理不同tune_type和input_type组合的通用方法
        
        当tune_type或input_type设置为'all'时，自动展开为所有可能的组合，
        并对每个组合调用指定的函数，收集并返回所有调用的结果。
        
        Args:
            func (callable): 要调用的函数，必须接受tune_type和input_type参数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数
            
        Returns:
            list: 所有函数调用返回值的列表，每个元素为一次调用的返回值
            
        Note:
            - TuneType.all 会展开为 [base, peak]
            - InputType.all 会展开为 [test, train, ref]
            - 组合顺序：先遍历tune_type，再遍历input_type
        """
        tune_types = [self.tune_type]
        if self.tune_type == TuneType.all:
            tune_types = [TuneType.base, TuneType.peak]
        
        input_types = [self.input_type]
        if self.input_type == InputType.all:
            input_types = [InputType.test, InputType.train, InputType.ref]
        
        results = []
        for tune_type in tune_types:
            for input_type in input_types:
                result = func(*args, tune_type=tune_type, input_type=input_type, **kwargs)
                results.append(result)
        return results

    def pack_binaries(self) -> list:
        """
        打包二进制文件
        
        根据配置的tune_type和input_type，复制所有基准测试的二进制文件。
        如果tune_type或input_type为'all'，会自动处理所有组合。
        
        Returns:
            list: 所有组合的目标目录列表，每个元素为一次copy_binaries调用的返回值
            
        Note:
            该方法是对copy_binaries的封装，自动处理组合展开
        """
        return self._process_tune_input_combinations(
            self.copy_binaries,
            spec_mode=self.spec_mode
        )
    
    def pack_binaries_cfg(self):
        """
        打包二进制文件(使用配置文件路径)
        
        该方法是pack_binaries的别名，用于保持API兼容性。
        直接使用实例初始化时配置的spec_cfg_path。
        """
        self.pack_binaries()
    
    def pack_benches(self, with_build:bool = False, spec_cfg: str = "") -> list:
        """
        打包完整的基准测试运行环境
        
        根据配置的tune_type和input_type，复制所有基准测试的完整运行环境，
        包括二进制文件、输入数据、配置文件等。同时生成测试脚本。
        
        Args:
            with_build (bool, optional): 是否包含构建目录，默认False
            spec_cfg (str, optional): SPEC配置文件名，为空则不复制配置文件
            
        Returns:
            list: 所有组合的目标目录列表，每个元素为一次copy_benches调用的返回值（目录路径列表）
            
        Note:
            - 如果tune_type或input_type为'all'，会自动处理所有组合
            - 会自动生成测试运行脚本和分数计算脚本
        """
        return self._process_tune_input_combinations(
            self.copy_benches,
            spec_mode=self.spec_mode, with_build=with_build, spec_cfg=spec_cfg
        )

    def pack_benches_cfg(self, with_build=False):
        """
        打包完整测试环境(使用配置文件路径)
        
        该方法是pack_benches的封装，使用实例初始化时配置的spec_cfg_path。
        
        Args:
            with_build (bool, optional): 是否包含构建目录，默认False
        """
        self.pack_benches(with_build, self.spec_cfg_path)

    def run_spec(self, output_dir: str = None, generate_report: bool = True) -> Dict:
        """
        直接运行SPEC测试
        
        调用runspec/runcpu命令直接执行SPEC基准测试，无需打包。
        测试完成后可选择生成测试报告。
        
        Args:
            output_dir (str, optional): 结果输出目录，默认为
                generated_files/{date}_{pack_name}/spec_results/run_{timestamp}，
                如果指定则使用指定目录
            generate_report (bool, optional): 是否生成测试报告，默认True
            
        Returns:
            Dict: 包含以下键的结果字典：
                - success (bool): 是否成功完成
                - output_dir (str): 结果输出目录
                - log_file (str): 日志文件路径
                - results (Dict): 解析后的测试结果（如果解析成功）
                - report_path (str): 报告文件路径（如果生成）
                
        Raises:
            CommandExecutionError: 当命令执行失败时抛出
            
        Note:
            - 测试过程中会实时输出日志
            - 支持Ctrl+C中断测试
            - 测试完成后自动解析结果并生成报告
            
        Example:
            >>> packer = PackSPEC(config)
            >>> result = packer.run_spec()
            >>> print(f"INT分数: {result['results']['int_score']}")
        """
        if output_dir is None:
            output_dir = os.path.join(self.utils.get_pack_generated_dir_path(), "spec_results", f"run_{CURRENT_TIME}")

        logger.info("="*80)
        logger.info(self.msg.get("start_direct_run"))
        logger.info("="*80)
        
        try:
            run_result = self.spec_driver.run_spec_directly(output_dir)
        except FileOperationError as e:
            logger.error(self.msg.get("spec_env_check_failed", error=str(e)))
            raise
        except CommandExecutionError as e:
            logger.error(self.msg.get("spec_test_failed", error=str(e)))
            raise
        except Exception as e:
            logger.error(self.msg.get("spec_test_unknown_error", error=str(e)))
            raise CommandExecutionError(self.msg.get("spec_test_unknown_error", error=str(e)))
        
        if not run_result["success"]:
            logger.error(self.msg.get("spec_test_execution_failed", error=run_result.get('error_message', 'Unknown error')))
            return run_result
        
        if generate_report:
            logger.info(self.msg.get("parsing_results"))
            
            results = parse_spec_results(
                run_result["output_dir"],
                self.spec_name,
                self.log_language
            )
            run_result["results"] = results
            
            config_info = {
                "spec_name": self.spec_name.name,
                "tune_type": self.tune_type.name,
                "input_type": self.input_type.name,
                "spec_mode": self.spec_mode.name,
                "iterations": self.iterations,
            }
            
            if self.report_format == "markdown":
                report_path = os.path.join(
                    run_result["output_dir"], 
                    "spec_report.md"
                )
                generate_markdown_report(results, config_info, report_path)
            else:
                report_path = os.path.join(
                    run_result["output_dir"], 
                    "spec_report.json"
                )
                generate_json_report(results, config_info, report_path)
            
            run_result["report_path"] = report_path
            logger.success(f"测试报告已生成: {report_path}")
            
            logger.info("="*80)
            logger.info(self.msg.get("test_result_summary"))
            logger.info("="*80)
            
            if results and isinstance(results, dict):
                int_score = results.get('int_score', 0)
                fp_score = results.get('fp_score', 0)
            else:
                int_score = 0
                fp_score = 0
            
            if int_score > 0:
                logger.info(self.msg.get("int_score", score=int_score))
            else:
                logger.warning(self.msg.get("int_score_failed"))
            if fp_score > 0:
                logger.info(self.msg.get("fp_score", score=fp_score))
            else:
                logger.warning(self.msg.get("fp_score_failed"))
            logger.info("="*80)
        
        return run_result

    def pack_qemu_verify(self, output_dir: str = None) -> Dict:
        """
        生成QEMU验证脚本
        
        当用户配置QEMU_PATH环境变量并开启验证模式时，生成用QEMU运行测试的脚本，
        用于验证编译出的SPEC CPU 2006/2017二进制文件是否正确。
        此时不统计运行时间，只通过QEMU运行测试，保留程序输出。
        
        Args:
            output_dir (str, optional): 验证脚本输出目录，默认自动生成
            
        Returns:
            Dict: 包含以下键的结果字典：
                - success (bool): 是否成功生成
                - output_dir (str): 输出目录路径
                - scripts (List[str]): 生成的脚本路径列表
                
        Raises:
            ConfigError: 当未配置QEMU_PATH环境变量或未开启verify_mode时抛出
            FileOperationError: 当复制文件失败时抛出
            
        Note:
            - 需要先调用setup_spec()编译二进制文件
            - QEMU路径通过环境变量QEMU_PATH配置
            - 生成的脚本包括单个验证脚本和批量验证脚本
            - 验证输出保存在输出目录的logs子目录中
            
        Example:
            >>> # 在.env中配置: QEMU_PATH=/path/to/qemu
            >>> config = {
            ...     "task": {"pack_name": "verify_test", ...},
            ...     "spec_config": {"spec_cfg_path": "/path/to/spec.cfg", ...},
            ...     "pack_config": {"verify_mode": True, ...}
            ... }
            >>> packer = PackSPEC(config)
            >>> packer.setup_spec()
            >>> result = packer.pack_qemu_verify()
        """
        if not QEMU_PATH:
            raise ConfigError(self.msg.get("qemu_path_not_configured"))
        
        if not self.verify_mode:
            raise ConfigError(self.msg.get("verify_mode_not_enabled"))
        
        if not os.path.isdir(QEMU_PATH):
            raise ConfigError(self.msg.get("qemu_dir_not_exist", path=QEMU_PATH))
        
        logger.info("="*80)
        logger.info(self.msg.get("generating_qemu_verify_script"))
        logger.info("="*80)
        logger.info(self.msg.get("qemu_dir", path=QEMU_PATH))
        logger.info(self.msg.get("spec_version_info", version=self.spec_name.name))
        logger.info(self.msg.get("tune_type_info", type=self.tune_type.name))
        logger.info(self.msg.get("input_type_info", type=self.input_type.name))
        
        if output_dir is None:
            # 直接获取目录路径，添加 _qemu_verify 后缀
            output_dir = self.utils.get_dest_dir(
                False, self.auto_mode, PACKMode.run,
                self.spec_name, self.tune_type, self.input_type, self.spec_mode
            )
            output_dir = f"{output_dir}_qemu_verify"
            
            # 检查 _qemu_verify 目录是否存在
            if os.path.exists(output_dir):
                if self.auto_mode:
                    logger.info(self.msg.get("dir_exists_auto_overwrite", path=output_dir))
                    shutil.rmtree(output_dir)
                else:
                    logger.warning(self.msg.get("dir_exists", path=output_dir))
                    logger.error(self.msg.get("dir_exists_not_auto_mode", path=output_dir))
                    raise PackSPECError(self.msg.get("dir_exists_not_auto_mode", path=output_dir))
            
            os.makedirs(output_dir, exist_ok=False)
        
        logs_dir = os.path.join(output_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        generated_scripts = []
        
        src_run_bench_dir = self.utils.get_dest_dir(
            False, self.auto_mode, PACKMode.run,
            self.spec_name, self.tune_type, self.input_type, self.spec_mode
        )
        
        if not os.path.exists(src_run_bench_dir):
            raise FileOperationError(self.msg.get("run_dir_not_found_for_qemu", path=src_run_bench_dir))
        
        for bench_name in self.spec_driver.spec_bench_list:
            src_run_dir = os.path.join(src_run_bench_dir, bench_name)
            if not os.path.exists(src_run_dir):
                logger.warning(self.msg.get("bench_dir_not_found_qemu", bench=bench_name))
                continue
            
            dest_bench_dir = os.path.join(output_dir, bench_name)
            logger.info(self.msg.get("copying_bench_qemu", bench=bench_name))
            
            try:
                if os.path.exists(dest_bench_dir):
                    # 用户已确认覆盖整个 _qemu_verify 目录，直接删除子目录
                    shutil.rmtree(dest_bench_dir)
                shutil.copytree(src_run_dir, dest_bench_dir, symlinks=True)
            except Exception as e:
                logger.error(self.msg.get("copy_bench_qemu_failed", bench=bench_name, error=str(e)))
                raise FileOperationError(self.msg.get("copy_bench_qemu_failed", bench=bench_name, error=str(e)))
            
            script_path = generate_qemu_verify_script(
                bench_name=bench_name,
                dest_dir=dest_bench_dir,
                spec_bench_map=self.spec_driver.spec_bench_map,
                tune_type=self.tune_type,
                label=self.spec_driver.label,
                input_type=self.input_type,
                data_dir=dest_bench_dir,
                output_dir=logs_dir,
                minimal_mode=self.minimal_mode
            )
            generated_scripts.append(script_path)
            logger.success(self.msg.get("verify_script_generated", path=script_path))
        
        all_script_path = generate_qemu_verify_all_script(
            bench_list=self.spec_driver.spec_bench_list,
            dest_dir=output_dir,
            spec_bench_map=self.spec_driver.spec_bench_map,
            tune_type=self.tune_type,
            label=self.spec_driver.label,
            input_type=self.input_type,
            output_dir=logs_dir,
            minimal_mode=self.minimal_mode,
            parallel_jobs=self.qemu_verify_parallel_jobs
        )
        generated_scripts.append(all_script_path)
        logger.success(self.msg.get("batch_verify_script_generated", path=all_script_path))
        
        self.utils.copy_spec_cfg_and_logs_to_target_dir(
            self.spec_driver.spec_dir, self.spec_cfg_path,
            output_dir, self.tune_type, self.input_type
        )
        
        logger.info("="*80)
        logger.info(self.msg.get("qemu_verify_script_done"))
        logger.info(self.msg.get("output_dir", path=output_dir))
        logger.info(self.msg.get("scripts_generated", count=len(generated_scripts)))
        logger.info("="*80)
        
        return {
            "success": True,
            "output_dir": output_dir,
            "scripts": generated_scripts
        }

    def run(self) -> Dict:
        """
        统一入口方法，根据配置自动执行相应操作
        
        根据 task 配置和 run_mode 配置自动调用相应方法：
        - 当 run_mode == RunMode.direct 时，调用 run_spec() 直接运行 SPEC 测试
        - 当 run_mode == RunMode.pack（默认）时，根据 task 配置执行打包操作
        
        Returns:
            Dict: 包含执行结果的字典，包括各步骤的执行状态
            
        Example:
            >>> config = {
            ...     "task": {
            ...         "pack_name": "my_test",
            ...         "setup_spec": False,
            ...         "pack_binaries": False,
            ...         "pack_benches": False,
            ...     },
            ...     "spec_config": {...},
            ...     "pack_config": {"verify_mode": True, ...},
            ... }
            >>> packer = PackSPEC(config)
            >>> result = packer.run()
        """
        result = {
            "success": True,
            "steps": []
        }
        
        # 根据 run_mode 决定执行模式
        if self.run_mode == RunMode.direct:
            # 直接运行模式：调用 run_spec() 直接运行 SPEC 测试
            logger.info(self.msg.get("run_mode_direct"))
            logger.info(self.msg.get("executing_run_spec"))
            run_result = self.run_spec()
            result["steps"].append("run_spec")
            result["run_spec_result"] = run_result
        else:
            # 打包模式（默认）：根据 task 配置执行打包操作
            logger.info(self.msg.get("run_mode_pack"))
            
            # 根据 setup_spec 配置执行编译
            if self.setup_spec_enabled:
                logger.info(self.msg.get("executing_setup_spec"))
                self.setup_spec()
                result["steps"].append("setup_spec")
            
            # 根据 pack_binaries 配置打包二进制文件
            if self.pack_binaries_enabled:
                logger.info(self.msg.get("executing_pack_binaries"))
                self.pack_binaries()
                result["steps"].append("pack_binaries")
            
            # 根据 pack_benches 配置打包完整测试环境
            if self.pack_benches_enabled:
                logger.info(self.msg.get("executing_pack_benches_cfg"))
                self.pack_benches_cfg()
                result["steps"].append("pack_benches_cfg")
            
            # 根据 pack_builds 配置打包 build 和 run 目录
            if self.pack_builds_enabled:
                logger.info(self.msg.get("executing_pack_builds"))
                self.pack_benches_cfg(with_build=True)
                result["steps"].append("pack_builds")
            
            # 根据 verify_mode 配置生成 QEMU 验证脚本
            if self.verify_mode:
                logger.info(self.msg.get("executing_pack_qemu_verify"))
                self.pack_qemu_verify()
                result["steps"].append("pack_qemu_verify")
        
        logger.info("="*80)
        logger.info(self.msg.get("all_tasks_completed"))
        logger.info(self.msg.get("executed_steps", steps=', '.join(result['steps'])))
        logger.info("="*80)
        
        return result


if __name__ == "__main__":
    packer = PackSPEC({
        "spec_name": SPECName.spec2017,
        "spec_benches": "625",
        "tune_type": TuneType.base,
        "input_type": InputType.ref,
        "spec_mode": SPECMode.speed,
        "iterations": 3,
        "test_core_num": 4,
    })
