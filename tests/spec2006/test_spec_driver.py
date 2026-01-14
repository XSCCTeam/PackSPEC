import unittest
import os
import sys
from unittest.mock import MagicMock, patch

from test_utils import SPEC_TEST_CFG_PATH, SPEC_TEST_2006_INSTALL_PATH, SPEC_TEST_SETUPLOG_PATH, SPEC_TEST_GENERATED_PATH

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pack_spec.spec_driver import SPECDriver
from src.pack_spec.pack_utils import PackUtils
from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, logger
)

P_PATH = os.path.join(os.path.dirname(__file__), '..', '..')

class TestSPECDriver(unittest.TestCase):
    """SPECDriver类的单元测试框架"""
    
    def setUp(self):
        """设置测试环境"""
        self.utils = PackUtils(logger, False)
        
        # 测试配置
        self.test_spec_cfg_path = SPEC_TEST_CFG_PATH
        self.test_spec_name = SPECName.spec2006
        self.test_tune_type = TuneType.base
        self.test_input_type = InputType.test
        self.test_spec_mode = SPECMode.speed
        self.test_spec_benches = "all"
        self.spec_dir = SPEC_TEST_2006_INSTALL_PATH
        
        # 创建SPECDriver实例
        self.spec_driver = SPECDriver(
            spec_cfg_path=self.test_spec_cfg_path,
            spec_name=self.test_spec_name,
            tune_type=self.test_tune_type,
            input_type=self.test_input_type,
            spec_mode=self.test_spec_mode,
            spec_benches=self.test_spec_benches,
            utils=self.utils
        )
    
    def tearDown(self):
        """清理测试环境"""
        pass
    
    def test_init(self):
        """测试构造函数"""
        # 验证属性是否正确设置
        self.assertEqual(self.spec_driver.spec_cfg_path, self.test_spec_cfg_path)
        self.assertEqual(self.spec_driver.spec_name, self.test_spec_name)
        self.assertEqual(self.spec_driver.tune_type, self.test_tune_type)
        self.assertEqual(self.spec_driver.input_type, self.test_input_type)
        self.assertEqual(self.spec_driver.spec_mode, self.test_spec_mode)
        self.assertEqual(self.spec_driver.spec_benches, self.test_spec_benches)
        self.assertEqual(self.spec_driver.iterations, 3)  # 默认值
        self.assertEqual(self.spec_driver.rebuild, False)  # 默认值
    
    def test_get_spec_info_spec2006(self):
        """测试get_spec_info方法 - SPEC2006"""
        self.spec_driver.spec_dir=self.spec_dir
        with patch.object(self.spec_driver, 'spec_name', SPECName.spec2006):
            info = self.spec_driver.get_spec_info()
            self.assertEqual(info['spec_name'], "SPEC CPU 2006")
            self.assertEqual(info['spec_version'], "v1.0.1")
            self.assertEqual(info['spec_path'], SPEC_TEST_2006_INSTALL_PATH)
        with patch.object(self.spec_driver, 'spec_name', SPECName.spec2006v1p2):
            info = self.spec_driver.get_spec_info()
            self.assertEqual(info['spec_name'], "SPEC CPU 2006")
            self.assertEqual(info['spec_version'], "v1.2.0")
            self.assertEqual(info['spec_path'], SPEC_TEST_2006_INSTALL_PATH)
        with patch.object(self.spec_driver, 'spec_name', SPECName.spec2017):
            info = self.spec_driver.get_spec_info()
            self.assertEqual(info['spec_name'], "SPEC CPU 2017")
            self.assertEqual(info['spec_version'], "v1.0.2")
            self.assertEqual(info['spec_path'], SPEC_TEST_2006_INSTALL_PATH)

    def test_get_spec_log(self):
        """测试get_spec_log方法"""
        self.spec_driver.spec_dir=self.spec_dir
        log = self.spec_driver.get_spec_log(SPEC_TEST_SETUPLOG_PATH)
        self.assertEqual(log, os.path.join(SPEC_TEST_2006_INSTALL_PATH, "result", "CPU2006.001.log"))

    def test_analyze_spec_config(self):
        """测试analyze_spec_config方法"""
        config = self.spec_driver.analyze_spec_config()
        self.assertEqual(config, "test_setup_gcc")

    # def test_run_setup_spec(self):
    #     """测试run_setup_spec方法"""
    #     self.spec_driver.spec_dir=self.spec_dir
    #     self.spec_driver.setup_script_path=os.path.join(P_PATH, "scripts", "setup-spec06.sh")
    #     self.spec_driver.spec_benches="473"
    #     log_path = self.spec_driver.run_setup_spec(TuneType.base, InputType.test, True)
    #     expected_log_path = os.path.join(GENERATED_FILES_PATH, "test_setup_gcc.base_test.setuplog")
    #     self.assertEqual(log_path, expected_log_path)

    def test_execute_specinvoke(self):
        """测试execute_specinvoke方法"""
        self.spec_driver.spec_dir=self.spec_dir
        with patch.object(self.spec_driver, 'spec_benches', '473'):
            self.spec_driver.utils=MagicMock()
            src_dir = "/home/wll/PackSPEC/tests/spec2006/generated_files/run_base_test_test_setup_gcc.0000"
            src_dir_name = os.path.basename(src_dir)
            self.spec_driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                f"cd {src_dir}",
                f"../{src_dir_name}/astar_base.test_setup_gcc lake.cfg > lake.out 2>> lake.err"
            ]
            dest_dir = SPEC_TEST_GENERATED_PATH
            result = self.spec_driver.execute_specinvoke(src_dir, dest_dir, InputType.test, ("astar_base.test_setup_gcc", "astar"))
            self.assertTrue(result)
            self.assertTrue(os.path.exists(os.path.join(dest_dir, "run_test.sh")))
            expected_run_test_sh = [
                "#!/bin/bash",
                "# Starting run for copy #0",
                "",
                "./astar lake.cfg > lake.out 2>> lake.err"
            ]
            with open(os.path.join(dest_dir, "run_test.sh"), "r") as f:
                run_test_sh = [line.strip() for line in f.readlines()]
            self.assertEqual(run_test_sh, expected_run_test_sh)

if __name__ == '__main__':
    unittest.main()
