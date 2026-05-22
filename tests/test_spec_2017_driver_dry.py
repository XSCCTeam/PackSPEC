"""
spec_2017_driver.py 干测试（mock-based unit tests）

测试 SPEC2017Driver 的 get_bench_list、get_ref_time、_get_bench_dir_prefix、
get_binary_path_map、_build_run_command 方法
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    ConfigError, FileOperationError, BenchmarkError,
)


def _create_2017_driver(spec_benches="all", tune_type=TuneType.base,
                        input_type=InputType.ref, spec_mode=SPECMode.speed):
    """创建一个 mock 的 SPEC2017Driver 实例"""
    with patch('src.pack_spec.spec_2017_driver.SPEC2017_PATH', '/fake/spec2017'), \
         patch('src.pack_spec.spec_2017_driver.SPEC2017_BENCH_PATH', '/fake/spec2017/benchspec/CPU'), \
         patch('src.pack_spec.spec_2017_driver.SCRIPTS_PATH', '/fake/scripts'):

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write("label = test_label\n")
            cfg_path = f.name

        try:
            from src.pack_spec.spec_2017_driver import SPEC2017Driver
            utils = MagicMock()
            utils.msg = MagicMock()
            utils.msg.get = MagicMock(return_value="mock msg")
            driver = SPEC2017Driver(
                spec_cfg_path=cfg_path,
                tune_type=tune_type,
                input_type=input_type,
                spec_mode=spec_mode,
                spec_benches=spec_benches,
                utils=utils,
            )
            return driver
        finally:
            os.unlink(cfg_path)


class TestSPEC2017DriverGetBenchList:
    """SPEC2017Driver.get_bench_list 测试"""

    def test_all_returns_20_benches(self):
        driver = _create_2017_driver("all")
        assert len(driver.spec_bench_list) == 20

    def test_int_returns_10_benches(self):
        driver = _create_2017_driver("int")
        assert len(driver.spec_bench_list) == 10
        assert all("_s" in b for b in driver.spec_bench_list)

    def test_fp_returns_10_benches(self):
        driver = _create_2017_driver("fp")
        assert len(driver.spec_bench_list) == 10

    def test_intspeed_same_as_int(self):
        driver = _create_2017_driver("intspeed")
        assert len(driver.spec_bench_list) == 10

    def test_fpspeed_same_as_fp(self):
        driver = _create_2017_driver("fpspeed")
        assert len(driver.spec_bench_list) == 10

    def test_specific_bench_by_number(self):
        driver = _create_2017_driver("600")
        assert driver.spec_bench_list == ["600.perlbench_s"]

    def test_multiple_numbers(self):
        driver = _create_2017_driver("600 602 603")
        assert len(driver.spec_bench_list) == 3

    def test_empty_raises_benchmark_error(self):
        with pytest.raises(BenchmarkError):
            _create_2017_driver("999")

    def test_mixed_int_and_number(self):
        driver = _create_2017_driver("int 603")
        assert "603.bwaves_s" in driver.spec_bench_list
        assert len(driver.spec_bench_list) == 11


class TestSPEC2017DriverGetRefTime:
    """SPEC2017Driver.get_ref_time 测试"""

    def test_ref_speed_reads_correct_line(self):
        driver = _create_2017_driver("600")
        with tempfile.TemporaryDirectory() as tmpdir:
            # 模拟 reftime 文件路径
            reftime_dir = os.path.join(tmpdir, "500.perlbench_r", "data", "refrate")
            os.makedirs(reftime_dir)
            reftime_path = os.path.join(reftime_dir, "reftime")
            with open(reftime_path, 'w') as f:
                f.write("# comment\n")
                f.write("refspeed 1 1600 perlbench_s\n")
                f.write("refrate 1 1500 perlbench_r\n")

            driver.spec_bench_path = tmpdir
            result = driver.get_ref_time("600.perlbench_s", InputType.ref)
            assert result == "1600"

    def test_test_input_reads_correct_line(self):
        driver = _create_2017_driver("600", input_type=InputType.test)
        with tempfile.TemporaryDirectory() as tmpdir:
            reftime_dir = os.path.join(tmpdir, "500.perlbench_r", "data", "test")
            os.makedirs(reftime_dir)
            reftime_path = os.path.join(reftime_dir, "reftime")
            with open(reftime_path, 'w') as f:
                f.write("# comment\n")
                f.write("test 1 100 perlbench_s\n")

            driver.spec_bench_path = tmpdir
            result = driver.get_ref_time("600.perlbench_s", InputType.test)
            assert result == "100"

    def test_missing_file_raises_error(self):
        driver = _create_2017_driver("600")
        driver.spec_bench_path = "/nonexistent"
        with pytest.raises(FileOperationError):
            driver.get_ref_time("600.perlbench_s", InputType.ref)

    def test_non_numeric_raises_error(self):
        driver = _create_2017_driver("600")
        with tempfile.TemporaryDirectory() as tmpdir:
            reftime_dir = os.path.join(tmpdir, "500.perlbench_r", "data", "refrate")
            os.makedirs(reftime_dir)
            reftime_path = os.path.join(reftime_dir, "reftime")
            with open(reftime_path, 'w') as f:
                f.write("refspeed 1 INVALID perlbench_s\n")

            driver.spec_bench_path = tmpdir
            with pytest.raises(FileOperationError):
                driver.get_ref_time("600.perlbench_s", InputType.ref)

    def test_no_matching_line_raises_error(self):
        driver = _create_2017_driver("600")
        with tempfile.TemporaryDirectory() as tmpdir:
            reftime_dir = os.path.join(tmpdir, "500.perlbench_r", "data", "refrate")
            os.makedirs(reftime_dir)
            reftime_path = os.path.join(reftime_dir, "reftime")
            with open(reftime_path, 'w') as f:
                f.write("# only comments\n")

            driver.spec_bench_path = tmpdir
            with pytest.raises(FileOperationError):
                driver.get_ref_time("600.perlbench_s", InputType.ref)


class TestSPEC2017DriverGetBenchDirPrefix:
    """SPEC2017Driver._get_bench_dir_prefix 测试"""

    def test_build_prefix(self):
        driver = _create_2017_driver("600")
        result = driver._get_bench_dir_prefix(ActionType.build, TuneType.base, InputType.ref, SPECMode.speed)
        assert result == "build_base_test_label"

    def test_run_prefix_ref_speed(self):
        driver = _create_2017_driver("600")
        result = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.ref, SPECMode.speed)
        assert result == "run_base_refspeed_test_label"

    def test_run_prefix_ref_rate(self):
        driver = _create_2017_driver("600")
        result = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.ref, SPECMode.rate)
        assert result == "run_base_refrate_test_label"

    def test_run_prefix_test_no_mode(self):
        driver = _create_2017_driver("600")
        result = driver._get_bench_dir_prefix(ActionType.run, TuneType.base, InputType.test, SPECMode.speed)
        assert result == "run_base_test_test_label"

    def test_run_prefix_peak(self):
        driver = _create_2017_driver("600")
        result = driver._get_bench_dir_prefix(ActionType.run, TuneType.peak, InputType.ref, SPECMode.speed)
        assert result == "run_peak_refspeed_test_label"


class TestSPEC2017DriverGetBinaryPathMap:
    """SPEC2017Driver.get_binary_path_map 测试"""

    def test_returns_map_from_bench_dirs(self):
        driver = _create_2017_driver("600")
        with tempfile.TemporaryDirectory() as tmpdir:
            # 模拟 build 目录结构
            bench_dir = os.path.join(tmpdir, "600.perlbench_s", "build", "build_base_test_label.0001")
            os.makedirs(bench_dir)
            driver.spec_bench_path = tmpdir
            driver.spec_bench_list = ["600.perlbench_s"]

            with patch.object(driver, 'get_bench_path', return_value=[bench_dir]):
                result = driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
                assert "600.perlbench_s" in result
                assert result["600.perlbench_s"].endswith("perlbench_s")

    def test_empty_bench_dirs_returns_empty(self):
        driver = _create_2017_driver("600")
        with patch.object(driver, 'get_bench_path', return_value=[]):
            result = driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            assert result == {}


class TestSPEC2017DriverBuildRunCommand:
    """SPEC2017Driver._build_run_command 测试"""

    def test_basic_command(self):
        driver = _create_2017_driver("600")
        cmd = driver._build_run_command()
        assert cmd[0].endswith("runcpu")
        assert "--config" in cmd
        assert "--tune" in cmd
        assert "--size" in cmd
        assert "--iterations" in cmd
        assert "--noreportable" in cmd

    def test_tune_all(self):
        driver = _create_2017_driver("600", tune_type=TuneType.all)
        cmd = driver._build_run_command()
        idx = cmd.index("--tune")
        assert cmd[idx + 1] == "base,peak"

    def test_input_all(self):
        driver = _create_2017_driver("600", input_type=InputType.all)
        cmd = driver._build_run_command()
        idx = cmd.index("--size")
        assert cmd[idx + 1] == "test,train,ref"

    def test_rate_mode(self):
        driver = _create_2017_driver("600", spec_mode=SPECMode.rate)
        cmd = driver._build_run_command()
        assert "--rate" in cmd

    def test_speed_mode_no_rate_flag(self):
        driver = _create_2017_driver("600", spec_mode=SPECMode.speed)
        cmd = driver._build_run_command()
        assert "--rate" not in cmd

    def test_config_uses_basename(self):
        driver = _create_2017_driver("600")
        cmd = driver._build_run_command()
        idx = cmd.index("--config")
        # Should be basename only, not full path
        assert "/" not in cmd[idx + 1]


class TestSPEC2017DriverInit:
    """SPEC2017Driver 初始化测试"""

    def test_none_path_raises_config_error(self):
        with patch('src.pack_spec.spec_2017_driver.SPEC2017_PATH', None), \
             patch('src.pack_spec.spec_2017_driver.SPEC2017_BENCH_PATH', None):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("label = test_label\n")
                cfg_path = f.name
            try:
                from src.pack_spec.spec_2017_driver import SPEC2017Driver
                with pytest.raises(ConfigError):
                    SPEC2017Driver(
                        spec_cfg_path=cfg_path,
                        tune_type=TuneType.base,
                        input_type=InputType.ref,
                        spec_mode=SPECMode.speed,
                        spec_benches="all",
                        utils=MagicMock(),
                    )
            finally:
                os.unlink(cfg_path)
