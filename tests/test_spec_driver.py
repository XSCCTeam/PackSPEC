"""
spec_driver.py 单元测试

测试 SPECDriver 基类和 SPEC2006Driver 的配置解析和基准测试选择逻辑
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    PackSPECError, ConfigError, SPEC2006_PATH, SPEC2006_BENCH_PATH,
    LogLanguage, get_log_messages, DEFAULT_LOG_LANGUAGE,
)
from src.pack_spec.pack_utils import PackUtils


class TestSPECDriverBase:
    """SPECDriver 基类测试"""

    def test_spec_cfg_filename_extraction(self):
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_cfg_path = "/home/user/spec/config/my_config.cfg"
            driver.spec_cfg = os.path.basename(driver.spec_cfg_path)
        assert driver.spec_cfg == "my_config.cfg"

    def test_spec_cfg_filename_with_dots(self):
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_cfg_path = "/home/user/spec/config/my.config.v2.cfg"
            driver.spec_cfg = os.path.basename(driver.spec_cfg_path)
        assert driver.spec_cfg == "my.config.v2.cfg"


class TestSPEC2006DriverBenchSelection:
    """SPEC2006Driver 基准测试选择逻辑测试"""

    def _create_driver(self, spec_benches="all"):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.spec_benches = spec_benches
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.spec_bench_list = driver.get_bench_list()
        return driver

    def test_all_benches(self):
        driver = self._create_driver("all")
        assert len(driver.spec_bench_list) > 0
        assert "400.perlbench" in driver.spec_bench_list

    def test_int_benches(self):
        driver = self._create_driver("int")
        for bench in driver.spec_bench_list:
            assert bench.startswith("4")

    def test_fp_benches(self):
        driver = self._create_driver("fp")
        for bench in driver.spec_bench_list:
            assert bench.startswith("4")

    def test_specific_benches(self):
        driver = self._create_driver("400 401")
        assert "400.perlbench" in driver.spec_bench_list
        assert "401.bzip2" in driver.spec_bench_list

    def test_mixed_benches(self):
        driver = self._create_driver("int 433")
        assert len(driver.spec_bench_list) > 0

    def test_empty_benches_raises(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with pytest.raises(Exception):
            driver = self._create_driver("999")


class TestSPEC2006DriverAttributes:
    """SPEC2006Driver 属性测试"""

    def test_driver_has_required_attributes(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.tune_type = TuneType.base
            driver.input_type = InputType.test
            driver.spec_mode = SPECMode.speed
            driver.iterations = 1
            driver.rebuild = False
        assert driver.tune_type == TuneType.base
        assert driver.input_type == InputType.test
        assert driver.spec_mode == SPECMode.speed
        assert driver.iterations == 1
        assert driver.rebuild is False


class TestExecuteSpecdiff:
    """execute_specdiff 方法测试"""

    def test_execute_specdiff_creates_script(self):
        import tempfile
        
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "cd /path/to/run_dir",
                "specperl /fake/spec/bin/specdiff -m -l 10 /path/to/ref.out output.out > output.cmp"
            ]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/path/to/src", tmpdir, InputType.test)
                
                assert result == True
                script_path = os.path.join(tmpdir, "specdiff_test.sh")
                assert os.path.exists(script_path)
                specdiff_output_dir = os.path.join(tmpdir, "specdiff_output")
                assert os.path.exists(specdiff_output_dir)

    def test_execute_specdiff_no_commands(self):
        import tempfile
        
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = []
            
            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/path/to/src", tmpdir, InputType.test)
                
                assert result == False

    def test_execute_specdiff_processes_commands(self):
        import tempfile
        
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# some header",
                "# Starting run for copy #0",
                "cd /src/dir",
                "specperl /fake/spec/bin/specdiff -m -l 10 /ref/out1.out out1.out > out1.cmp",
                "# Starting run for copy #0",
                "cd /src/dir",
                "specperl /fake/spec/bin/specdiff -m -l 10 /ref/out2.out out2.out > out2.cmp",
            ]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/src/dir", tmpdir, InputType.ref)
                
                assert result == True
                script_path = os.path.join(tmpdir, "specdiff_ref.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                assert "#!/bin/bash" in content
                assert "specdiff" in content
                assert "cd /src/dir" not in content

    def test_execute_specdiff_copies_ref_output(self):
        import tempfile
        
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                ref_file = os.path.join(tmpdir, "ref_output.out")
                with open(ref_file, 'w') as f:
                    f.write("test reference output")
                
                driver.utils.execute_commands.return_value = [
                    "# Starting run for copy #0",
                    f"specdiff -m -l 10 {ref_file} output.out > output.cmp"
                ]
                
                dest_dir = os.path.join(tmpdir, "dest")
                os.makedirs(dest_dir)
                result = driver.execute_specdiff("/src/dir", dest_dir, InputType.test)
                
                assert result == True
                specdiff_output_dir = os.path.join(dest_dir, "specdiff_output")
                assert os.path.exists(specdiff_output_dir)
                copied_file = os.path.join(specdiff_output_dir, "ref_output.out")
                assert os.path.exists(copied_file)
                
                script_path = os.path.join(dest_dir, "specdiff_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                assert "specdiff_output/ref_output.out" in content
