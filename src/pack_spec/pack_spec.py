import os
import shutil

from src.pack_spec.pack_config import *
from src.pack_spec.pack_utils import PackUtils, load_pack_spec_cfg
from src.pack_spec.spec_2006_driver import SPEC2006Driver, SPEC2006V1P01Driver
from src.pack_spec.spec_2017_driver import SPEC2017Driver


class PackSPEC:
    def __init__(self, config):
        """
        初始化PackSPEC实例
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
        初始化PackSPEC实例
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
        self.test_core_num = config.get('test_core_num', DEFAULT_CORE_NUM)
        self.test_clock_rate = config.get('test_clock_rate', DEFAULT_CLOCK_RATE)
        self.profile_gen = config.get('profile_gen', DEFAULT_PROFILE_GEN)
        self.auto_mode = config.get('auto_mode', DEFAULT_AUTO_MODE)
        self.host_mode = config.get('host_mode', DEFAULT_HOST_MODE)
        
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
        
        包括当前时间、SPEC版本、SPEC路径等基本信息
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
        src_bench_map = self.spec_driver.get_binary_path_map(tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
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

        # # 复制配置文件及相关日志至目标目录
        # self.utils.copy_spec_cfg_and_logs_to_target_dir(
        #     self.spec_dir, spec_cfg, dest_binary_dir, tune_type, input_type)

        return dest_binary_dir


    def copy_benches(self, tune_type: TuneType, input_type: InputType, spec_mode: SPECMode,
                     with_build: bool = False, dest_bench_dir: str = "", spec_cfg: str = "") -> list:
        if with_build:
            src_build_bench_dir = self.spec_driver.get_bench_path(ActionType.build, tune_type, input_type, spec_mode)
        src_run_bench_dir = self.spec_driver.get_bench_path(ActionType.run, tune_type, input_type, spec_mode)

        os.makedirs(PACK_PATH, exist_ok=True)
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
        self.spec_driver.run_setup_spec(self.tune_type, self.input_type, rebuild=self.rebuild)

    def _process_tune_input_combinations(self, func, *args, **kwargs):
        """
        处理不同tune_type和input_type组合的通用方法
        
        Args:
            func: 要调用的函数
            *args: 传递给函数的位置参数
            **kwargs: 传递给函数的关键字参数
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
        
        Args:
            label (str): 标签
            spec_cfg (str, optional): SPEC配置文件名，默认为""
            
        Returns:
            list: 目标目录列表
        """
        self._process_tune_input_combinations(
            self.copy_binaries,
            spec_mode=self.spec_mode
        )
    
    def pack_binaries_cfg(self):
        self.pack_binaries()
    
    def pack_benches(self, with_build:bool = False, spec_cfg: str = "") -> list:
        """
        打包基准测试
        
        Args:
            with_build (bool, optional): 是否包含构建目录，默认为False
            spec_cfg (str, optional): SPEC配置文件名，默认为""
            
        Returns:
            list: 目标目录列表
        """
        self._process_tune_input_combinations(
            self.copy_benches,
            spec_mode=self.spec_mode, with_build=with_build, spec_cfg=spec_cfg
        )
        return []

    def pack_benches_cfg(self, with_build=False):
        self.pack_benches(with_build, self.spec_cfg_path)

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

