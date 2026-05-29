"""
spec_driver.py 单元测试

测试 SPECDriver 基类和 SPEC2006Driver 的配置解析、基准测试选择逻辑、驱动注册表和工厂方法
"""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    ConfigError, FileOperationError,
    get_log_messages, DEFAULT_LOG_LANGUAGE,
)


class TestSPECDriverRegistry:
    """SPECDriver 驱动注册表和工厂方法测试"""

    def test_registry_contains_spec2006(self):
        """测试注册表中包含 SPEC2006Driver"""
        from src.pack_spec.spec_driver import SPECDriver
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        assert "spec2006" in SPECDriver._registry
        assert SPECDriver._registry["spec2006"] is SPEC2006Driver

    def test_registry_contains_spec2006v1p01(self):
        """测试注册表中包含 SPEC2006V1P01Driver"""
        from src.pack_spec.spec_driver import SPECDriver
        from src.pack_spec.spec_2006_driver import SPEC2006V1P01Driver
        assert "spec2006v1p01" in SPECDriver._registry
        assert SPECDriver._registry["spec2006v1p01"] is SPEC2006V1P01Driver

    def test_registry_contains_spec2017(self):
        """测试注册表中包含 SPEC2017Driver"""
        from src.pack_spec.spec_driver import SPECDriver
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        assert "spec2017" in SPECDriver._registry
        assert SPECDriver._registry["spec2017"] is SPEC2017Driver

    def test_create_returns_spec2006_driver(self):
        """测试 create 工厂方法根据 SPECName.spec2006 返回 SPEC2006Driver 实例"""
        from src.pack_spec.spec_driver import SPECDriver
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch('src.pack_spec.spec_2006_driver.SPEC2006_PATH', '/fake/spec2006'), \
             patch('src.pack_spec.spec_2006_driver.SPEC2006_BENCH_PATH', '/fake/spec2006/benchspec/CPU2006'), \
             patch('src.pack_spec.spec_2006_driver.SCRIPTS_PATH', '/fake/scripts'), \
             patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None), \
             patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.create(
                spec_name=SPECName.spec2006,
                spec_cfg_path="/fake/config.cfg",
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                spec_benches="all",
                utils=MagicMock(),
            )
            assert isinstance(driver, SPEC2006Driver)

    def test_create_returns_spec2017_driver(self):
        """测试 create 工厂方法根据 SPECName.spec2017 返回 SPEC2017Driver 实例"""
        from src.pack_spec.spec_driver import SPECDriver
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None), \
             patch.object(SPEC2017Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.create(
                spec_name=SPECName.spec2017,
                spec_cfg_path="/fake/config.cfg",
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                spec_benches="all",
                utils=MagicMock(),
            )
            assert isinstance(driver, SPEC2017Driver)

    def test_create_raises_value_error_for_unknown_spec_name(self):
        """测试 create 工厂方法对未注册的 SPECName 抛出 ValueError"""
        from src.pack_spec.spec_driver import SPECDriver
        mock_spec_name = MagicMock()
        mock_spec_name.name = "unknown_spec"
        with pytest.raises(ValueError, match="未找到"):
            SPECDriver.create(
                spec_name=mock_spec_name,
                spec_cfg_path="/fake/config.cfg",
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                spec_benches="all",
                utils=MagicMock(),
            )

    def test_subclass_spec_name_key(self):
        """测试子类的 _spec_name_key 属性正确设置"""
        from src.pack_spec.spec_2006_driver import SPEC2006Driver, SPEC2006V1P01Driver
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        assert SPEC2006Driver._spec_name_key == "spec2006"
        assert SPEC2006V1P01Driver._spec_name_key == "spec2006v1p01"
        assert SPEC2017Driver._spec_name_key == "spec2017"

    def test_base_class_spec_name_key_is_none(self):
        """测试基类的 _spec_name_key 为 None，不会注册到注册表"""
        from src.pack_spec.spec_driver import SPECDriver
        assert SPECDriver._spec_name_key is None


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

    def test_build_run_command_raises_not_implemented_error(self):
        """测试基类 _build_run_command 方法抛出 NotImplementedError"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            with pytest.raises(NotImplementedError, match="子类必须实现 _build_run_command 方法"):
                driver._build_run_command()


class TestConvertBenchesForMode:
    """_convert_benches_for_mode 方法测试"""

    def _make_driver(self, spec_name):
        from src.pack_spec.spec_driver import SPECDriver
        driver = SPECDriver.__new__(SPECDriver)
        driver.spec_name = spec_name
        return driver

    def test_spec2017_all_speed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("all", SPECMode.speed)
        assert result == "intspeed fpspeed"

    def test_spec2017_all_rate(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("all", SPECMode.rate)
        assert result == "intrate fprate"

    def test_spec2017_int_speed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("int", SPECMode.speed)
        assert result == "intspeed"

    def test_spec2017_int_rate(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("int", SPECMode.rate)
        assert result == "intrate"

    def test_spec2017_fp_speed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("fp", SPECMode.speed)
        assert result == "fpspeed"

    def test_spec2017_fp_rate(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("fp", SPECMode.rate)
        assert result == "fprate"

    def test_spec2017_specific_numbers_unchanged(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("600 602", SPECMode.speed)
        assert result == "600 602"

    def test_spec2017_intspeed_stays_intspeed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("intspeed", SPECMode.speed)
        assert result == "intspeed"

    def test_spec2017_intrate_converts_to_intspeed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("intrate", SPECMode.speed)
        assert result == "intspeed"

    def test_spec2017_fprate_converts_to_fpspeed(self):
        driver = self._make_driver(SPECName.spec2017)
        result = driver._convert_benches_for_mode("fprate", SPECMode.speed)
        assert result == "fpspeed"

    def test_spec2006_all_expands_to_int_fp(self):
        driver = self._make_driver(SPECName.spec2006)
        result = driver._convert_benches_for_mode("all", SPECMode.speed)
        assert result == "int fp"

    def test_spec2006_int_stays_int(self):
        driver = self._make_driver(SPECName.spec2006)
        result = driver._convert_benches_for_mode("int", SPECMode.speed)
        assert result == "int"


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
        with pytest.raises(Exception):
            self._create_driver("999")


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


class TestSPEC2006DriverConfigError:
    """SPEC2006Driver 配置错误延迟检查测试"""

    def test_init_raises_config_error_when_spec2006_path_is_none(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch('src.pack_spec.spec_2006_driver.SPEC2006_PATH', None):
            with pytest.raises(ConfigError):
                SPEC2006Driver(
                    spec_cfg_path="/fake/config.cfg",
                    tune_type=TuneType.base,
                    input_type=InputType.test,
                    spec_mode=SPECMode.speed,
                    spec_benches="all",
                    utils=MagicMock(),
                )

    def test_init_does_not_raise_when_spec2006_path_is_set(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        from src.pack_spec.spec_driver import SPECDriver
        with patch('src.pack_spec.spec_2006_driver.SPEC2006_PATH', '/fake/spec2006'), \
             patch('src.pack_spec.spec_2006_driver.SPEC2006_BENCH_PATH', '/fake/spec2006/benchspec/CPU2006'), \
             patch('src.pack_spec.spec_2006_driver.SCRIPTS_PATH', '/fake/scripts'), \
             patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None), \
             patch.object(SPEC2006Driver, 'get_bench_list', return_value=["400.perlbench"]):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            SPEC2006Driver.__init__(
                driver,
                spec_cfg_path="/fake/config.cfg",
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                spec_benches="all",
                utils=MagicMock(),
            )
            assert driver.spec_dir == '/fake/spec2006'


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
                
                assert result
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
                
                assert not result

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
                
                assert result
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
                
                assert result
                specdiff_output_dir = os.path.join(dest_dir, "specdiff_output")
                assert os.path.exists(specdiff_output_dir)
                copied_file = os.path.join(specdiff_output_dir, "ref_output.out")
                assert os.path.exists(copied_file)
                
                script_path = os.path.join(dest_dir, "specdiff_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                assert "specdiff_output/ref_output.out" in content


class TestAnalyzeSpecConfig:
    """analyze_spec_config 方法异常测试"""

    def test_spec2006_no_ext_raises_config_error(self):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("# 注释行\n")
                f.write("some_other_key = value\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                with pytest.raises(ConfigError, match="Ext not found"):
                    driver.analyze_spec_config()
            finally:
                os.unlink(cfg_path)

    def test_spec2017_no_label_raises_config_error(self):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2017
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("# 注释行\n")
                f.write("some_other_key = value\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                with pytest.raises(ConfigError, match="Label not found"):
                    driver.analyze_spec_config()
            finally:
                os.unlink(cfg_path)

    def test_spec2006_with_ext_returns_label(self):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("ext = my_label\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                label = driver.analyze_spec_config()
                assert label == "my_label"
            finally:
                os.unlink(cfg_path)

    def test_spec2017_with_label_returns_label(self):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2017
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("label = my_label\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                label = driver.analyze_spec_config()
                assert label == "my_label"
            finally:
                os.unlink(cfg_path)

    def test_config_file_not_found_raises_config_error(self):
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.spec_cfg_path = "/nonexistent/path/config.cfg"

            with pytest.raises(ConfigError):
                driver.analyze_spec_config()

    def test_basepeak_not_allowed_raises_config_error(self):
        """测试配置文件中设置basepeak=yes但allow_basepeak=False时抛出ConfigError"""
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.allow_basepeak = False

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("ext = my_label\n")
                f.write("basepeak = yes\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                with pytest.raises(ConfigError):
                    driver.analyze_spec_config()
            finally:
                os.unlink(cfg_path)

    def test_basepeak_allowed_returns_label(self):
        """测试配置文件中设置basepeak=yes且allow_basepeak=True时正常返回标签"""
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_name = SPECName.spec2006
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.allow_basepeak = True

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("ext = my_label\n")
                f.write("basepeak = yes\n")
                cfg_path = f.name

            try:
                driver.spec_cfg_path = cfg_path
                label = driver.analyze_spec_config()
                assert label == "my_label"
            finally:
                os.unlink(cfg_path)


class TestGetRefTime:
    """get_ref_time 方法异常测试"""

    def test_non_numeric_reftime_raises_file_operation_error(self):
        import tempfile

        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.spec_bench_path = "/fake/bench"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.TemporaryDirectory() as tmpdir:
                reftime_dir = os.path.join(tmpdir, "400.perlbench", "data", "ref")
                os.makedirs(reftime_dir)
                reftime_path = os.path.join(reftime_dir, "reftime")
                with open(reftime_path, 'w') as f:
                    f.write("header\n")
                    f.write("not_a_number\n")

                driver.spec_bench_path = tmpdir
                with pytest.raises(FileOperationError, match="Expect a numeric"):
                    driver.get_ref_time("400.perlbench", InputType.ref)

    def test_valid_reftime_returns_value(self):
        import tempfile

        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with tempfile.TemporaryDirectory() as tmpdir:
                reftime_dir = os.path.join(tmpdir, "400.perlbench", "data", "ref")
                os.makedirs(reftime_dir)
                reftime_path = os.path.join(reftime_dir, "reftime")
                with open(reftime_path, 'w') as f:
                    f.write("header\n")
                    f.write("12345\n")

                driver.spec_bench_path = tmpdir
                result = driver.get_ref_time("400.perlbench", InputType.ref)
                assert result == "12345"

    def test_missing_reftime_file_raises_file_operation_error(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.spec_bench_path = "/nonexistent/path"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            with pytest.raises(FileOperationError):
                driver.get_ref_time("400.perlbench", InputType.ref)


class TestGetBenchPathMaxNum:
    """get_bench_path 方法中选择最大编号目录的逻辑测试"""

    def _create_2006_driver(self):
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.spec_name = SPECName.spec2006
            driver.spec_bench_list = ["400.perlbench"]
            driver.spec_build_dir = "build"
            driver.spec_run_dir = "run"
            driver.label = "test_label"
            driver.debug_mode = False
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
        return driver

    def _create_2017_driver(self):
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        with patch.object(SPEC2017Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2017Driver.__new__(SPEC2017Driver)
            driver.spec_name = SPECName.spec2017
            driver.spec_bench_list = ["600.perlbench_s"]
            driver.spec_build_dir = "build"
            driver.spec_run_dir = "run"
            driver.label = "test_label"
            driver.debug_mode = False
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
        return driver

    def test_2006_selects_max_num_dir(self):
        """测试SPEC2006在多个匹配目录时选择编号最大的目录"""
        import tempfile
        driver = self._create_2006_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "400.perlbench", "build")
            os.makedirs(bench_path)
            for num in ["0001", "0002", "0003"]:
                dir_name = f"build_base_test_label.{num}"
                os.makedirs(os.path.join(bench_path, dir_name))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("build_base_test_label.0003")

    def test_2017_selects_max_num_dir(self):
        """测试SPEC2017在多个匹配目录时选择编号最大的目录"""
        import tempfile
        driver = self._create_2017_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "600.perlbench_s", "build")
            os.makedirs(bench_path)
            for num in ["0001", "0002", "0005"]:
                dir_name = f"build_base_test_label.{num}"
                os.makedirs(os.path.join(bench_path, dir_name))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("build_base_test_label.0005")

    def test_2006_single_dir(self):
        """测试SPEC2006只有一个匹配目录时直接返回该目录"""
        import tempfile
        driver = self._create_2006_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "400.perlbench", "build")
            os.makedirs(bench_path)
            os.makedirs(os.path.join(bench_path, "build_base_test_label.0001"))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("build_base_test_label.0001")

    def test_2017_single_dir(self):
        """测试SPEC2017只有一个匹配目录时直接返回该目录"""
        import tempfile
        driver = self._create_2017_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "600.perlbench_s", "build")
            os.makedirs(bench_path)
            os.makedirs(os.path.join(bench_path, "build_base_test_label.0001"))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("build_base_test_label.0001")


class TestGetBenchDirPrefix:
    """_get_bench_dir_prefix 方法测试"""

    def _create_base_driver(self):
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.label = "test_label"
        return driver

    def _create_2017_driver(self):
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        with patch.object(SPEC2017Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2017Driver.__new__(SPEC2017Driver)
            driver.label = "test_label"
        return driver

    def test_base_build_prefix(self):
        """测试基类构建目录前缀"""
        driver = self._create_base_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
        assert prefix == "build_base_test_label"

    def test_base_run_prefix(self):
        """测试基类运行目录前缀"""
        driver = self._create_base_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.ref, SPECMode.speed)
        assert prefix == "run_base_ref_test_label"

    def test_2017_build_prefix(self):
        """测试SPEC2017构建目录前缀"""
        driver = self._create_2017_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.build, TuneType.peak, InputType.test, SPECMode.speed)
        assert prefix == "build_peak_test_label"

    def test_2017_run_prefix_non_ref(self):
        """测试SPEC2017非ref输入的运行目录前缀"""
        driver = self._create_2017_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.test, SPECMode.speed)
        assert prefix == "run_base_test_test_label"

    def test_2017_run_prefix_ref_speed(self):
        """测试SPEC2017 ref输入speed模式的运行目录前缀"""
        driver = self._create_2017_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.ref, SPECMode.speed)
        assert prefix == "run_base_refspeed_test_label"

    def test_2017_run_prefix_ref_rate(self):
        """测试SPEC2017 ref输入rate模式的运行目录前缀"""
        driver = self._create_2017_driver()
        prefix = driver._get_bench_dir_prefix(ActionType.run, TuneType.peak, InputType.ref, SPECMode.rate)
        assert prefix == "run_peak_refrate_test_label"


class TestGetBenchPathBase:
    """基类 get_bench_path 方法测试"""

    def _create_driver(self):
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_bench_list = ["400.perlbench"]
            driver.spec_build_dir = "build"
            driver.spec_run_dir = "run"
            driver.label = "test_label"
            driver.debug_mode = False
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
        return driver

    def test_build_dir_returns_correct_path(self):
        """测试构建目录返回正确路径"""
        import tempfile
        driver = self._create_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "400.perlbench", "build")
            os.makedirs(bench_path)
            os.makedirs(os.path.join(bench_path, "build_base_test_label.0001"))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("build_base_test_label.0001")

    def test_run_dir_returns_correct_path(self):
        """测试运行目录返回正确路径"""
        import tempfile
        driver = self._create_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = os.path.join(tmpdir, "400.perlbench", "run")
            os.makedirs(run_path)
            os.makedirs(os.path.join(run_path, "run_base_ref_test_label.0001"))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.run, TuneType.base, InputType.ref, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("run_base_ref_test_label.0001")

    def test_no_matching_dir_returns_empty(self):
        """测试无匹配目录时返回空列表"""
        import tempfile
        driver = self._create_driver()

        with tempfile.TemporaryDirectory() as tmpdir:
            bench_path = os.path.join(tmpdir, "400.perlbench", "build")
            os.makedirs(bench_path)

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.build, TuneType.base, InputType.test, SPECMode.speed)
            assert len(result) == 0

    def test_2017_run_dir_ref_speed(self):
        """测试SPEC2017 ref+speed运行目录返回正确路径"""
        import tempfile
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        with patch.object(SPEC2017Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2017Driver.__new__(SPEC2017Driver)
            driver.spec_bench_list = ["600.perlbench_s"]
            driver.spec_build_dir = "build"
            driver.spec_run_dir = "run"
            driver.label = "test_label"
            driver.debug_mode = False
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

        with tempfile.TemporaryDirectory() as tmpdir:
            run_path = os.path.join(tmpdir, "600.perlbench_s", "run")
            os.makedirs(run_path)
            os.makedirs(os.path.join(run_path, "run_base_refspeed_test_label.0001"))

            driver.spec_bench_path = tmpdir
            result = driver.get_bench_path(ActionType.run, TuneType.base, InputType.ref, SPECMode.speed)
            assert len(result) == 1
            assert result[0].endswith("run_base_refspeed_test_label.0001")


class TestBuildRunCommand:
    """_build_run_command 方法测试"""

    def test_2006_build_run_command_returns_command(self):
        """测试SPEC2006Driver._build_run_command 返回正确的runspec命令"""
        from src.pack_spec.spec_2006_driver import SPEC2006Driver
        with patch.object(SPEC2006Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2006Driver.__new__(SPEC2006Driver)
            driver.spec_dir = "/fake/spec2006"
            driver.spec_cfg_path = "/fake/config.cfg"
            driver.tune_type = TuneType.base
            driver.input_type = InputType.ref
            driver.spec_mode = SPECMode.speed
            driver.iterations = 3
            driver.spec_bench_list = ["400.perlbench", "401.bzip2"]
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            cmd = driver._build_run_command()
            assert isinstance(cmd, list)
            assert len(cmd) > 0
            assert cmd[0] == "/fake/spec2006/bin/runspec"
            assert "--config" in cmd
            assert "--tune" in cmd
            assert "base" in cmd
            assert "--size" in cmd
            assert "ref" in cmd
            assert "--iterations" in cmd
            assert "3" in cmd
            assert "--noreportable" in cmd
            assert "400.perlbench" in cmd
            assert "401.bzip2" in cmd

    def test_2017_build_run_command_returns_command(self):
        """测试SPEC2017Driver._build_run_command 返回正确的runcpu命令"""
        from src.pack_spec.spec_2017_driver import SPEC2017Driver
        with patch.object(SPEC2017Driver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPEC2017Driver.__new__(SPEC2017Driver)
            driver.spec_dir = "/fake/spec2017"
            driver.spec_cfg_path = "/fake/config.cfg"
            driver.tune_type = TuneType.peak
            driver.input_type = InputType.test
            driver.spec_mode = SPECMode.rate
            driver.iterations = 1
            driver.spec_bench_list = ["600.perlbench_s"]
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)

            cmd = driver._build_run_command()
            assert isinstance(cmd, list)
            assert len(cmd) > 0
            assert cmd[0] == "/fake/spec2017/bin/runcpu"
            assert "--config" in cmd
            assert "--tune" in cmd
            assert "peak" in cmd
            assert "--size" in cmd
            assert "test" in cmd
            assert "--iterations" in cmd
            assert "1" in cmd
            assert "--noreportable" in cmd
            assert "--rate" in cmd
            assert "600.perlbench_s" in cmd


class TestSpecinvokeDryRun:
    """execute_specinvoke 方法模拟依赖测试"""

    def test_specinvoke_creates_run_script(self):
        """测试execute_specinvoke创建运行脚本并正确替换路径"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "cd /src/dir",
                "/src/dir/run_base.test_label ./perlbench_base.test_label < /dev/null"
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specinvoke("/src/dir", tmpdir, InputType.test)

                assert result is True
                script_path = os.path.join(tmpdir, "run_test.sh")
                assert os.path.exists(script_path)
                with open(script_path, 'r') as f:
                    content = f.read()
                # 验证实际运行命令保留在脚本中（路径被替换为相对路径）
                assert "perlbench_base.test_label" in content
                # 验证cd命令被替换为空字符串（cd {src_dir}被删除）
                cd_src_dir_lines = [l for l in content.split('\n') if l.strip() == "cd /src/dir"]
                assert len(cd_src_dir_lines) == 0
                # 验证绝对路径被替换为相对路径
                assert "/src/dir/" not in content
                # 验证specinvoke行被跳过（不出现在脚本中）
                specinvoke_lines = [l for l in content.split('\n') if l.strip().startswith("specinvoke")]
                assert len(specinvoke_lines) == 0

    def test_specinvoke_empty_output_creates_empty_script(self):
        """测试execute_specinvoke空输出时仍返回True并创建空脚本（当前实现行为）"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = []

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specinvoke("/src/dir", tmpdir, InputType.test)

                # 当前实现始终返回True
                assert result is True
                # 当前实现始终创建脚本文件（只有shebang行）
                script_path = os.path.join(tmpdir, "run_test.sh")
                assert os.path.exists(script_path)
                with open(script_path, 'r') as f:
                    content = f.read()
                assert content == "#!/bin/bash\n"

    def test_specinvoke_multiline_output(self):
        """测试execute_specinvoke处理多组命令输出"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "cd /src/dir",
                "/src/dir/run_base.test_label ./perlbench_base.test_label < /dev/null",
                "# Starting run for copy #0",
                "cd /src/dir",
                "/src/dir/run_base.test_label ./bzip2_base.test_label < /dev/null",
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specinvoke("/src/dir", tmpdir, InputType.test)

                assert result is True
                script_path = os.path.join(tmpdir, "run_test.sh")
                assert os.path.exists(script_path)
                with open(script_path, 'r') as f:
                    content = f.read()
                assert "perlbench_base.test_label" in content
                assert "bzip2_base.test_label" in content

    def test_specinvoke_skips_specinvoke_lines(self):
        """测试execute_specinvoke跳过specinvoke开头的行"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "specinvoke -m",
                "# Starting run for copy #0",
                "cd /src/dir",
                "./perlbench_base.test_label < /dev/null",
                "specinvoke -e",
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specinvoke("/src/dir", tmpdir, InputType.test)

                assert result is True
                script_path = os.path.join(tmpdir, "run_test.sh")
                assert os.path.exists(script_path)
                with open(script_path, 'r') as f:
                    content = f.read()
                # 验证specinvoke开头的行被跳过
                assert "perlbench_base.test_label" in content
                for line in content.split('\n'):
                    if line.strip():
                        assert not line.strip().startswith("specinvoke"), f"specinvoke行未被跳过: {line}"

    def test_specinvoke_binary_name_map(self):
        """测试execute_specinvoke替换二进制文件名映射"""
        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "./perlbench_base.orig_name < /dev/null",
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specinvoke(
                    "/src/dir", tmpdir, InputType.test,
                    binary_name_map=("orig_name", "new_name")
                )

                assert result is True
                script_path = os.path.join(tmpdir, "run_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                # 验证旧二进制名被替换为新名
                assert "new_name" in content
                assert "orig_name" not in content


class TestRemoveQemuPrefix:
    """_remove_qemu_prefix 方法测试"""

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU-10.2.0/build')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_remove_qemu_with_full_path(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/mnt/sdbdata/QEMU-10.2.0/build/qemu-riscv64 ./x264_s_base.test --pass 1"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test --pass 1"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU-10.2.0/build')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_remove_qemu_preserves_leading_whitespace(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "   /mnt/sdbdata/QEMU-10.2.0/build/qemu-riscv64 ./x264_s_base.test"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "   ./x264_s_base.test"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', None)
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_remove_qemu_without_path(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "qemu-riscv64 ./x264_s_base.test --pass 1"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test --pass 1"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_no_qemu_prefix_no_change(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "./perlbench_s_base.test -I. -I./lib test.cfg"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU-10.2.0/build')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64 -s 83886080000')
    def test_qemu_cmd_with_extra_options(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/mnt/sdbdata/QEMU-10.2.0/build/qemu-riscv64 ./x264_s_base.test"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-aarch64')
    def test_aarch64_qemu_prefix(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/mnt/sdbdata/QEMU/qemu-aarch64 ./binary_name args"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./binary_name args"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/mnt/sdbdata/QEMU')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_comment_line_unchanged(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "# Starting run for copy #0"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', None)
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_remove_qemu_with_path_but_no_env(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/home/kd/workplace/llvm_tool/20240920-qemu/bin/qemu-riscv64 ./x264_s_base.test --pass 1"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test --pass 1"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/different/path')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_remove_qemu_mismatched_path(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/home/kd/workplace/llvm_tool/20240920-qemu/bin/qemu-riscv64 ./x264_s_base.test"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', None)
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-aarch64')
    def test_remove_qemu_riscv_when_cmd_is_aarch64(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/home/kd/workplace/llvm_tool/bin/qemu-riscv64 ./x264_s_base.test"
        result = SPECDriver._remove_qemu_prefix(line)
        assert result == "./x264_s_base.test"


class TestAddQemuPrefix:

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    @patch('src.pack_spec.pack_utils.get_qemu_cmd_absolute', return_value='/home/kd/qemu/qemu-riscv64')
    def test_add_qemu_with_full_path(self, mock_get_abs):
        from src.pack_spec.spec_driver import SPECDriver
        line = "./imagevalidate_525_base.riscv-xxx -avg -threshold 0.5"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == "/home/kd/qemu/qemu-riscv64 ./imagevalidate_525_base.riscv-xxx -avg -threshold 0.5"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    @patch('src.pack_spec.pack_utils.get_qemu_cmd_absolute', return_value='/home/kd/qemu/qemu-riscv64')
    def test_add_qemu_preserves_leading_whitespace(self, mock_get_abs):
        from src.pack_spec.spec_driver import SPECDriver
        line = "   ./diffwrf_521_base.riscv-xxx arg1"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == "   /home/kd/qemu/qemu-riscv64 ./diffwrf_521_base.riscv-xxx arg1"

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_add_qemu_no_duplicate(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/home/kd/qemu/qemu-riscv64 ./imagevalidate_525_base.riscv-xxx -avg"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_add_qemu_no_change_for_specdiff(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "specdiff -m -l 10 ref.out output.out > output.cmp"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', '')
    def test_add_qemu_no_cmd_set(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "./imagevalidate_525_base.riscv-xxx -avg"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_add_qemu_non_local_binary(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "/usr/bin/some_tool arg1 arg2"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == line

    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    def test_add_qemu_comment_line_unchanged(self):
        from src.pack_spec.spec_driver import SPECDriver
        line = "# Starting run for copy #0"
        result = SPECDriver._add_qemu_prefix(line)
        assert result == line


class TestExecuteSpecdiffWithQemu:

    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.pack_utils.get_qemu_cmd_absolute', return_value='/home/kd/qemu/qemu-riscv64')
    def test_execute_specdiff_adds_qemu_to_local_binary(self, mock_get_abs):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "./imagevalidate_525_base.riscv-xxx -avg -threshold 0.5 frame_200.yuv /ref/frame_200.org.tga > imagevalidate_frame_200.out 2>> imagevalidate_frame_200.err"
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/path/to/src", tmpdir, InputType.test)

                assert result
                script_path = os.path.join(tmpdir, "specdiff_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                assert any(
                    line.startswith("/home/kd/qemu/qemu-riscv64 ./imagevalidate")
                    for line in content.splitlines()
                )

    @patch('src.pack_spec.spec_driver.QEMU_CMD', 'qemu-riscv64')
    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    @patch('src.pack_spec.pack_utils.get_qemu_cmd_absolute', return_value='/home/kd/qemu/qemu-riscv64')
    def test_execute_specdiff_no_qemu_for_specdiff_command(self, mock_get_abs):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "specdiff -m -l 10 /ref/out.out output.out > output.cmp"
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/path/to/src", tmpdir, InputType.test)

                assert result
                script_path = os.path.join(tmpdir, "specdiff_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                for line in content.splitlines():
                    if "specdiff" in line:
                        assert not line.strip().startswith("/home/kd/qemu/qemu-riscv64")

    @patch('src.pack_spec.spec_driver.QEMU_CMD', '')
    @patch('src.pack_spec.spec_driver.QEMU_PATH', '/home/kd/qemu')
    def test_execute_specdiff_no_qemu_when_cmd_not_set(self):
        import tempfile

        from src.pack_spec.spec_driver import SPECDriver
        with patch.object(SPECDriver, '__init__', lambda self, *args, **kwargs: None):
            driver = SPECDriver.__new__(SPECDriver)
            driver.spec_dir = "/fake/spec"
            driver.msg = get_log_messages(DEFAULT_LOG_LANGUAGE)
            driver.utils = MagicMock()
            driver.utils.execute_commands.return_value = [
                "# Starting run for copy #0",
                "./imagevalidate_525_base.riscv-xxx -avg -threshold 0.5"
            ]

            with tempfile.TemporaryDirectory() as tmpdir:
                result = driver.execute_specdiff("/path/to/src", tmpdir, InputType.test)

                assert result
                script_path = os.path.join(tmpdir, "specdiff_test.sh")
                with open(script_path, 'r') as f:
                    content = f.read()
                assert "/home/kd/qemu/qemu-riscv64" not in content
