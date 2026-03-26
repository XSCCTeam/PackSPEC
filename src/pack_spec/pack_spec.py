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
        "pack_name": "my_test",
        "spec_cfg_path": "/path/to/config.cfg",
        "spec_config": {
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
from typing import Dict, Optional

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType, PACKMode, RunMode,
    PackSPECError, ConfigError, FileOperationError, CommandExecutionError, BenchmarkError,
    CURRENT_DATE, CURRENT_TIME, DEFAULT_ITERATIONS, DEFAULT_REBUILD,
    DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_PROFILE_GEN,
    DEFAULT_AUTO_MODE, DEFAULT_HOST_MODE, DEFAULT_LLVM_PROFDATA_PATH,
    DEFAULT_RUN_MODE, DEFAULT_REPORT_FORMAT, RESULTS_OUTPUT_PATH,
    QEMU_PATH, DEFAULT_VERIFY_MODE,
    BOSC_API_KEY, BOSC_AT_USER, P_PATH, logger, GENERATED_FILES_PATH
)
from src.pack_spec.pack_utils import PackUtils, load_pack_spec_cfg, parse_spec_results, generate_json_report, generate_markdown_report, generate_qemu_verify_script, generate_qemu_verify_all_script
from src.pack_spec.spec_2006_driver import SPEC2006Driver, SPEC2006V1P01Driver
from src.pack_spec.spec_2017_driver import SPEC2017Driver


class PackSPEC:
    """
    SPEC CPU基准测试打包工具主类
    
    该类是PackSPEC工具的核心类，负责协调SPEC基准测试的编译、打包和测试脚本生成。
    支持SPEC2006和SPEC2017两个版本的基准测试套件。
    
    Attributes:
        spec_cfg_path (str): SPEC配置文件的绝对路径
        pack_name (str): 打包任务名称，用于标识和生成目录
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
        host_mode (bool): 是否HOST模式
        utils (PackUtils): 工具类实例
        spec_driver (SPECDriver): SPEC驱动实例
        
    Example:
        >>> config = {
        ...     "pack_name": "test_pack",
        ...     "spec_cfg_path": "/path/to/spec.cfg",
        ...     "spec_config": {
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
            print(config["spec_config"]["spec_benches"])
            self.init_date = config.get('date', CURRENT_DATE)
            self.init_pack_spec(config)
            
            
        elif isinstance(config, dict):
            self.init_date = CURRENT_DATE
            self.init_pack_spec(config)
            # 从配置字典中提取参数，设置默认值
            self.pack_generated_files_path = self.utils.create_generated_dir(self.auto_mode)
            config['date'] = self.init_date
            self.utils.save_pack_spec_cfg(config)
        else:
            raise ValueError("config must be a dict or a path to a config file")
        

    def init_pack_spec(self, config: dict):
        """
        初始化PackSPEC实例的内部配置
        
        从配置字典中提取参数并初始化各个组件，包括：
        - 解析SPEC配置路径和打包名称
        - 设置SPEC版本、优化级别、输入类型等参数
        - 创建对应的SPEC驱动实例(SPEC2006/SPEC2017)
        - 初始化工具类实例
        
        Args:
            config (dict): 配置字典，包含以下键：
                - spec_cfg_path: SPEC配置文件路径
                - pack_name: 打包名称
                - spec_config: SPEC相关配置子字典
                - pack_config: 打包相关配置子字典(可选)
                - test_core_num: 测试核心编号(可选)
                - test_clock_rate: 测试CPU主频(可选)
                - profile_gen: 是否生成Profile(可选)
                - auto_mode: 是否自动模式(可选)
                - host_mode: 是否HOST模式(可选)
        """
        # 从配置字典中提取参数，设置默认值
        # SPEC cfg 文件绝对路径
        self.spec_cfg_path = config["spec_cfg_path"]
        # SPEC基准测试相关配置
        self.pack_name = config["pack_name"]
        self.spec_name = config["spec_config"]['spec_name']
        self.tune_type = config["spec_config"]['tune_type']
        self.input_type = config["spec_config"]['input_type']
        self.spec_mode = config["spec_config"]['spec_mode']
        self.spec_benches = config["spec_config"]['spec_benches']
        self.iterations = config["spec_config"].get('iterations', DEFAULT_ITERATIONS)
        self.rebuild = config["pack_config"].get('rebuild', DEFAULT_REBUILD)
        # PackSPEC打包相关配置
        pack_config = config.get('pack_config', {})
        self.test_core_num = config.get('test_core_num', pack_config.get('test_core_num', DEFAULT_CORE_NUM))
        self.test_clock_rate = config.get('test_clock_rate', pack_config.get('test_clock_rate', DEFAULT_CLOCK_RATE))
        self.profile_gen = config.get('profile_gen', pack_config.get('profile_gen', DEFAULT_PROFILE_GEN))
        self.auto_mode = config.get('auto_mode', pack_config.get('auto_mode', DEFAULT_AUTO_MODE))
        self.host_mode = config.get('host_mode', pack_config.get('host_mode', DEFAULT_HOST_MODE))
        self.run_mode = config.get('run_mode', pack_config.get('run_mode', DEFAULT_RUN_MODE))
        self.report_format = config.get('report_format', pack_config.get('report_format', DEFAULT_REPORT_FORMAT))
        self.verify_mode = config.get('verify_mode', pack_config.get('verify_mode', DEFAULT_VERIFY_MODE))
        
        if self.profile_gen: # profile 生成模式只跑一次程序
            self.iterations = 1
        
        self.utils = PackUtils(config, logger)

        if self.spec_name == SPECName.spec2006:
            self.spec_driver = SPEC2006Driver(self.spec_cfg_path, self.tune_type, self.input_type,
                                              self.spec_mode, self.spec_benches, self.utils, self.iterations, self.rebuild)       
        elif self.spec_name == SPECName.spec2006v1p01:
            self.spec_driver = SPEC2006V1P01Driver(self.spec_cfg_path, self.tune_type, self.input_type,
                                              self.spec_mode, self.spec_benches, self.utils, self.iterations, self.rebuild)       
        elif self.spec_name == SPECName.spec2017:
            self.spec_driver = SPEC2017Driver(self.spec_cfg_path, self.tune_type, self.input_type,
                                              self.spec_mode, self.spec_benches, self.utils, self.iterations, self.rebuild)
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
        logger.info(f"Start Packing {self.spec_name.name}")
        logger.info(f"Current Time: {CURRENT_TIME}")
        logger.info("-"*80)
        logger.info(f"{self.spec_driver.get_spec_info()['spec_name']} Version: {self.spec_driver.get_spec_info()['spec_version']}")
        logger.info(f"Path: {self.spec_driver.get_spec_info()['spec_path']}")
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
            目标目录命名格式: {GENERATED_FILES_PATH}/{pack_name}/bin/{spec_name}_bin_{pack_name}.{tune_type}_{input_type}_{spec_mode}
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
            logger.success(f"Successfully copied {copy_num} files.")
        else:
            logger.error(f"No binary to copy.")
            raise FileOperationError("No binary to copy.")

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
                raise FileOperationError(f"Failed to copy {bench_name}: {str(e)}")

            if self.spec_driver.execute_specinvoke(src_run_dir, dest_dir, input_type):
                logger.success(f"Successfully generated run_{input_type.name}.sh in {dest_dir}")
            else:
                logger.error(f"Failed to generate run_test.sh in {dest_dir}")
                raise CommandExecutionError(f"Failed to generate run_test.sh in {dest_dir}")

            self.create_test_script(self.spec_driver.label, bench_name, self.test_core_num, dest_dir, tune_type, input_type)

        if dest_dir_list != []:
            logger.success(f"Successfully copied {len(dest_dir_list)} benches.")
        else:
            logger.error(f"No benches to copy.")
            raise FileOperationError("No benches to copy.")
        
        self.create_run_all_script(self.spec_driver.label, self.test_core_num, dest_dir_list, tune_type, input_type)

        # 复制配置文件及相关日志至目标目录
        if spec_cfg != "":
            self.spec_driver.utils.copy_spec_cfg_and_logs_to_target_dir(
                self.spec_driver.spec_dir, spec_cfg, 
                os.path.dirname(dest_dir_list[0]), 
                tune_type, input_type)

        return dest_dir_list

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
            f"$SCRIPT_DIR/test_{input_type.name}.log", core_num, iterations)

        script_content.extend(
            self.spec_driver.utils.commands_to_run_bench(bench_name, self.profile_gen, self.spec_driver.spec_bench_map,
                                             core_num, self.spec_driver.get_ref_time(bench_name, input_type),
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
            logger.warning("No benchmark directories to run")
            return
            
        if iterations == 0:
            iterations = self.iterations

        # 获取父目录
        parent_dir = os.path.dirname(buildrun_bench_dir_list[0])
        run_all_script = os.path.join(parent_dir, self.utils.get_run_script_name(self.profile_gen, input_type, "all"))
        
        script_content = self.utils.commands_to_prepare_run(
            "$SCRIPT_DIR/run_all.log", core_num, iterations)

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

    def setup_spec(self):
        """
        执行SPEC基准测试的编译和设置
        
        调用SPEC驱动执行setup操作，包括：
        - 解析SPEC配置文件
        - 编译基准测试二进制文件
        - 准备运行目录和输入数据
        
        该方法是对spec_driver.run_setup_spec的封装，
        使用实例初始化时配置的tune_type、input_type和rebuild参数。
        """
        self.spec_driver.run_setup_spec(self.tune_type, self.input_type, rebuild=self.rebuild)

    def _process_tune_input_combinations(self, func, *args, **kwargs):
        """
        处理不同tune_type和input_type组合的通用方法
        
        当tune_type或input_type设置为'all'时，自动展开为所有可能的组合，
        并对每个组合调用指定的函数。
        
        Args:
            func (callable): 要调用的函数，必须接受tune_type和input_type参数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数
            
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
        
        for tune_type in tune_types:
            for input_type in input_types:
                func(*args, tune_type=tune_type, input_type=input_type, **kwargs)

    def pack_binaries(self) -> list:
        """
        打包二进制文件
        
        根据配置的tune_type和input_type，复制所有基准测试的二进制文件。
        如果tune_type或input_type为'all'，会自动处理所有组合。
        
        Returns:
            list: 目标目录列表
            
        Note:
            该方法是对copy_binaries的封装，自动处理组合展开
        """
        self._process_tune_input_combinations(
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
            list: 目标目录列表
            
        Note:
            - 如果tune_type或input_type为'all'，会自动处理所有组合
            - 会自动生成测试运行脚本和分数计算脚本
        """
        self._process_tune_input_combinations(
            self.copy_benches,
            spec_mode=self.spec_mode, with_build=with_build, spec_cfg=spec_cfg
        )
        return []

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
            output_dir (str, optional): 结果输出目录，默认自动生成
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
        logger.info("="*80)
        logger.info("开始直接运行SPEC测试")
        logger.info("="*80)
        
        try:
            run_result = self.spec_driver.run_spec_directly(output_dir)
        except FileOperationError as e:
            logger.error(f"SPEC环境检查失败: {e}")
            raise
        except CommandExecutionError as e:
            logger.error(f"SPEC测试执行失败: {e}")
            raise
        except Exception as e:
            logger.error(f"运行SPEC测试时发生未知错误: {e}")
            raise CommandExecutionError(f"运行SPEC测试时发生未知错误: {e}")
        
        if not run_result["success"]:
            logger.error(f"SPEC测试执行失败: {run_result.get('error_message', '未知错误')}")
            return run_result
        
        if generate_report:
            logger.info("解析测试结果...")
            
            results = parse_spec_results(
                run_result["output_dir"],
                self.spec_name
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
            logger.info("测试结果摘要")
            logger.info("="*80)
            
            if results and isinstance(results, dict):
                int_score = results.get('int_score', 0)
                fp_score = results.get('fp_score', 0)
            else:
                int_score = 0
                fp_score = 0
            
            if int_score > 0:
                logger.info(f"整数测试(INT)分数: {int_score:.2f}")
            else:
                logger.warning("整数测试(INT)分数: 解析失败或无有效数据")
            if fp_score > 0:
                logger.info(f"浮点测试(FP)分数: {fp_score:.2f}")
            else:
                logger.warning("浮点测试(FP)分数: 解析失败或无有效数据")
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
            >>> # 在set_env.sh中配置: export QEMU_PATH=/path/to/qemu
            >>> config = {
            ...     "pack_name": "verify_test",
            ...     "spec_cfg_path": "/path/to/spec.cfg",
            ...     "verify_mode": True,
            ...     "spec_config": {...}
            ... }
            >>> packer = PackSPEC(config)
            >>> packer.setup_spec()
            >>> result = packer.pack_qemu_verify()
        """
        if not QEMU_PATH:
            raise ConfigError("未配置QEMU路径，请在set_env.sh中设置QEMU_PATH环境变量")
        
        if not self.verify_mode:
            raise ConfigError("未开启验证模式，请设置verify_mode=True")
        
        if not os.path.isdir(QEMU_PATH):
            raise ConfigError(f"QEMU目录不存在: {QEMU_PATH}")
        
        logger.info("="*80)
        logger.info("生成QEMU验证脚本")
        logger.info("="*80)
        logger.info(f"QEMU目录: {QEMU_PATH}")
        logger.info(f"SPEC版本: {self.spec_name.name}")
        logger.info(f"优化级别: {self.tune_type.name}")
        logger.info(f"输入类型: {self.input_type.name}")
        
        if output_dir is None:
            output_dir = self.utils.create_dest_dir(
                False, self.auto_mode, PACKMode.run,
                self.spec_name, self.tune_type, self.input_type, self.spec_mode
            )
            output_dir = f"{output_dir}_qemu_verify"
            os.makedirs(output_dir, exist_ok=True)
        
        logs_dir = os.path.join(output_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        generated_scripts = []
        
        src_run_bench_dir = self.spec_driver.get_bench_path(
            ActionType.run, self.tune_type, self.input_type, self.spec_mode
        )
        
        for bench_name in self.spec_driver.spec_bench_list:
            src_run_dir = self.utils.get_bench_dir(bench_name, src_run_bench_dir)
            if src_run_dir == "":
                logger.warning(f"无法找到基准测试目录: {bench_name}")
                continue
            
            dest_bench_dir = os.path.join(output_dir, bench_name)
            logger.info(f"复制 {bench_name}...")
            
            try:
                if os.path.exists(dest_bench_dir):
                    if self.auto_mode:
                        shutil.rmtree(dest_bench_dir)
                    else:
                        logger.warning(f"目录 {dest_bench_dir} 已存在")
                        raise FileOperationError(f"目录 {dest_bench_dir} 已存在，请设置 auto_mode=True 或手动删除")
                shutil.copytree(src_run_dir, dest_bench_dir, symlinks=True)
            except FileOperationError:
                raise
            except Exception as e:
                logger.error(f"复制 {bench_name} 失败: {str(e)}")
                raise FileOperationError(f"复制 {bench_name} 失败: {str(e)}")
            
            script_path = generate_qemu_verify_script(
                bench_name=bench_name,
                dest_dir=dest_bench_dir,
                spec_bench_map=self.spec_driver.spec_bench_map,
                tune_type=self.tune_type,
                label=self.spec_driver.label,
                input_type=self.input_type,
                data_dir=dest_bench_dir,
                output_dir=logs_dir
            )
            generated_scripts.append(script_path)
            logger.success(f"生成验证脚本: {script_path}")
        
        all_script_path = generate_qemu_verify_all_script(
            bench_list=self.spec_driver.spec_bench_list,
            dest_dir=output_dir,
            spec_bench_map=self.spec_driver.spec_bench_map,
            tune_type=self.tune_type,
            label=self.spec_driver.label,
            input_type=self.input_type,
            output_dir=logs_dir
        )
        generated_scripts.append(all_script_path)
        logger.success(f"生成批量验证脚本: {all_script_path}")
        
        self.utils.copy_spec_cfg_and_logs_to_target_dir(
            self.spec_driver.spec_dir, self.spec_cfg_path,
            output_dir, self.tune_type, self.input_type
        )
        
        logger.info("="*80)
        logger.info("QEMU验证脚本生成完成")
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"生成脚本数量: {len(generated_scripts)}")
        logger.info("="*80)
        
        return {
            "success": True,
            "output_dir": output_dir,
            "scripts": generated_scripts
        }


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

