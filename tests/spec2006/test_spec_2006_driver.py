import unittest
import os
import sys
from unittest.mock import MagicMock, patch

from test_utils import SPEC_TEST_CFG_PATH, SPEC_TEST_2006_INSTALL_PATH, SPEC_TEST_SETUPLOG_PATH, SPEC_TEST_GENERATED_PATH

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pack_spec.spec_2006_driver import SPEC2006Driver
from src.pack_spec.pack_utils import PackUtils
from src.pack_spec.pack_config import (
    SPECName, ActionType, TuneType, InputType, SPECMode, logger
)

P_PATH = os.path.join(os.path.dirname(__file__), '..', '..')

class TestSPEC2006Driver(unittest.TestCase):
    """SPEC2006Driver类的单元测试框架"""
    
    def setUp(self):
        """设置测试环境"""
        self.utils = PackUtils(logger, False)
        
        # 测试配置
        self.test_spec_cfg_path = SPEC_TEST_CFG_PATH
        self.test_tune_type = TuneType.base
        self.test_input_type = InputType.test
        self.test_spec_mode = SPECMode.speed
        self.test_spec_benches = "all"
        self.spec_dir = SPEC_TEST_2006_INSTALL_PATH
        
        # 创建SPEC2006Driver实例
        self.spec_driver = SPEC2006Driver(
            spec_cfg_path=self.test_spec_cfg_path,
            tune_type=self.test_tune_type,
            input_type=self.test_input_type,
            spec_mode=self.test_spec_mode,
            spec_benches=self.test_spec_benches,
            utils=self.utils
        )
        self.spec_driver.debug_mode = False
    
    def tearDown(self):
        """清理测试环境"""
        pass
    
    def test_init(self):
        """测试构造函数"""
        # 验证属性是否正确设置
        self.assertEqual(self.spec_driver.spec_cfg_path, self.test_spec_cfg_path)
        self.assertEqual(self.spec_driver.tune_type, self.test_tune_type)
        self.assertEqual(self.spec_driver.input_type, self.test_input_type)
        self.assertEqual(self.spec_driver.spec_mode, self.test_spec_mode)
        self.assertEqual(self.spec_driver.spec_benches, self.test_spec_benches)
        self.assertEqual(self.spec_driver.iterations, 3)  # 默认值
        self.assertEqual(self.spec_driver.rebuild, False)  # 默认值
    
    def test_get_bench_list(self):
        """测试获取基准列表"""
        with patch.object(self.spec_driver, 'spec_benches', 'all'):
            bench_list = self.spec_driver.get_bench_list()
            self.assertEqual(len(bench_list), 29)
        with patch.object(self.spec_driver, 'spec_benches', 'int'):
            bench_list = self.spec_driver.get_bench_list()
            self.assertEqual(len(bench_list), 12)
        with patch.object(self.spec_driver, 'spec_benches', 'fp'):
            bench_list = self.spec_driver.get_bench_list()
            self.assertEqual(len(bench_list), 17)
        with patch.object(self.spec_driver, 'spec_benches', '456'):
            bench_list = self.spec_driver.get_bench_list()
            self.assertEqual(bench_list, ['456.hmmer'])

    def test_get_ref_time(self):
        """测试获取参考时间"""
        ref_time = self.spec_driver.get_ref_time("400.perlbench", InputType.test)
        self.assertEqual(ref_time, '10.2')
        ref_time = self.spec_driver.get_ref_time("400.perlbench", InputType.train)
        self.assertEqual(ref_time, '586')
        ref_time = self.spec_driver.get_ref_time("400.perlbench", InputType.ref)
        self.assertEqual(ref_time, '9770')

    # def test_get_bench_path_perfix(self):
    #     """测试获取基准路径"""
    #     with patch.object(self.spec_driver, 'label', 'test_setup_gcc'):
    #         with patch.object(self.spec_driver, 'spec_bench_list', ['456.hmmer']):
    #             bench_path = self.spec_driver.get_bench_path_perfix(ActionType.build, self.test_tune_type, 
    #                                                          self.test_input_type, self.test_spec_mode)
    #             expected_bench_path = os.path.join(self.spec_dir, "benchspec", "CPU2006", "456.hmmer",
    #                                                "build", "build_base_test_setup_gcc")
    #             self.assertEqual(bench_path, [expected_bench_path])

if __name__ == '__main__':
    unittest.main()
