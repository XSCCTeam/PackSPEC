"""
spec_driver.py 干测试（mock-based unit tests）

测试 SPECDriver 的 get_spec_info、get_spec_log、run_setup_spec、
_check_spec_environment、run_spec_directly 方法
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, ActionType,
    ConfigError, FileOperationError, CommandExecutionError,
)


def _create_driver(spec_name=SPECName.spec2006, spec_benches="all"):
    """创建一个 mock 的 SPEC2006Driver 实例用于测试基类方法"""
    with patch('src.pack_spec.spec_2006_driver.SPEC2006_PATH', '/fake/spec2006'), \
         patch('src.pack_spec.spec_2006_driver.SPEC2006_BENCH_PATH', '/fake/spec2006/benchspec/CPU2006'), \
         patch('src.pack_spec.spec_2006_driver.SCRIPTS_PATH', '/fake/scripts'):

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write("ext = test_label\n")
            cfg_path = f.name

        try:
            from src.pack_spec.spec_2006_driver import SPEC2006Driver
            utils = MagicMock()
            utils.msg = MagicMock()
            utils.msg.get = MagicMock(return_value="mock msg")
            driver = SPEC2006Driver(
                spec_cfg_path=cfg_path,
                tune_type=TuneType.base,
                input_type=InputType.ref,
                spec_mode=SPECMode.speed,
                spec_benches=spec_benches,
                utils=utils,
            )
            return driver
        finally:
            os.unlink(cfg_path)


def _create_2017_driver():
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
                tune_type=TuneType.base,
                input_type=InputType.ref,
                spec_mode=SPECMode.speed,
                spec_benches="600",
                utils=utils,
            )
            return driver
        finally:
            os.unlink(cfg_path)


class TestGetSpecInfo:
    """SPECDriver.get_spec_info 测试"""

    def test_spec2006_info(self):
        driver = _create_driver(SPECName.spec2006)
        info = driver.get_spec_info()
        assert info["spec_name"] == "SPEC CPU 2006"
        assert info["spec_version"] == "v1.2.0"
        assert info["spec_path"] == "/fake/spec2006"

    def test_spec2006v1p01_info(self):
        with patch('src.pack_spec.spec_2006_driver.SPEC2006_PATH', '/fake/spec2006'), \
             patch('src.pack_spec.spec_2006_driver.SPEC2006_BENCH_PATH', '/fake/spec2006/benchspec/CPU2006'), \
             patch('src.pack_spec.spec_2006_driver.SCRIPTS_PATH', '/fake/scripts'):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
                f.write("ext = test_label\n")
                cfg_path = f.name
            try:
                from src.pack_spec.spec_2006_driver import SPEC2006V1P01Driver
                utils = MagicMock()
                utils.msg = MagicMock()
                utils.msg.get = MagicMock(return_value="mock msg")
                driver = SPEC2006V1P01Driver(
                    spec_cfg_path=cfg_path,
                    tune_type=TuneType.base,
                    input_type=InputType.ref,
                    spec_mode=SPECMode.speed,
                    spec_benches="400",
                    utils=utils,
                )
                # V1P01 internally uses SPECName.spec2006, so manually set to test the branch
                driver.spec_name = SPECName.spec2006v1p01
                info = driver.get_spec_info()
                assert info["spec_version"] == "v1.0.1"
            finally:
                os.unlink(cfg_path)

    def test_spec2017_info(self):
        driver = _create_2017_driver()
        info = driver.get_spec_info()
        assert info["spec_name"] == "SPEC CPU 2017"
        assert info["spec_version"] == "v1.0.2"


class TestGetSpecLog:
    """SPECDriver.get_spec_log 测试"""

    def test_found_log_path(self):
        driver = _create_driver()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(f"The log for this run is in /fake/spec2006/result/log001.log\n")
            log_path = f.name
        try:
            result = driver.get_spec_log(log_path)
            assert result == "/fake/spec2006/result/log001.log"
        finally:
            os.unlink(log_path)

    def test_not_found_returns_empty(self):
        driver = _create_driver()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("some other content\n")
            log_path = f.name
        try:
            result = driver.get_spec_log(log_path)
            assert result is None or result == ""
        finally:
            os.unlink(log_path)

    def test_file_not_exist_returns_empty(self):
        driver = _create_driver()
        result = driver.get_spec_log("/nonexistent/file.log")
        assert result == ""


class TestCheckSpecEnvironment:
    """SPECDriver._check_spec_environment 测试"""

    def test_missing_spec_dir_raises(self):
        driver = _create_driver()
        driver.spec_dir = "/nonexistent/spec"
        with pytest.raises(FileOperationError):
            driver._check_spec_environment()

    def test_missing_runspec_raises(self):
        driver = _create_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_dir = tmpdir
            # dir exists but no bin/runspec
            with pytest.raises(CommandExecutionError):
                driver._check_spec_environment()

    def test_valid_environment_passes(self):
        driver = _create_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_dir = tmpdir
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(bin_dir)
            runspec_path = os.path.join(bin_dir, "runspec")
            with open(runspec_path, 'w') as f:
                f.write("#!/bin/bash\n")
            assert driver._check_spec_environment() is True

    def test_spec2017_checks_runcpu(self):
        driver = _create_2017_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_dir = tmpdir
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(bin_dir)
            runcpu_path = os.path.join(bin_dir, "runcpu")
            with open(runcpu_path, 'w') as f:
                f.write("#!/bin/bash\n")
            assert driver._check_spec_environment() is True


class TestRunSetupSpec:
    """SPECDriver.run_setup_spec 测试"""

    def test_successful_setup(self):
        driver = _create_driver()
        driver.setup_script_path = "/bin/echo"
        driver.utils.create_spec_setup_log_path = MagicMock(return_value="/tmp/setup.log")

        result = driver.run_setup_spec(TuneType.base, InputType.ref, rebuild=True)
        assert result == "/tmp/setup.log"

    def test_failed_setup_raises(self):
        driver = _create_driver()
        driver.setup_script_path = "/bin/false"
        with pytest.raises(CommandExecutionError):
            driver.run_setup_spec(TuneType.base, InputType.ref)

    def test_nonexistent_script_raises(self):
        driver = _create_driver()
        driver.setup_script_path = "/nonexistent/setup.sh"
        with pytest.raises(CommandExecutionError):
            driver.run_setup_spec(TuneType.base, InputType.ref)


class TestRunSpecDirectly:
    """SPECDriver.run_spec_directly 测试"""

    def test_successful_run(self):
        driver = _create_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_dir = tmpdir
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(bin_dir)
            runspec_path = os.path.join(bin_dir, "runspec")
            with open(runspec_path, 'w') as f:
                f.write("#!/bin/bash\n")

            # Create shrc
            shrc_path = os.path.join(tmpdir, "shrc")
            with open(shrc_path, 'w') as f:
                f.write("# empty shrc\n")

            # Mock _build_run_command to return a simple command
            driver._build_run_command = MagicMock(return_value=["echo", "test"])

            output_dir = os.path.join(tmpdir, "output")
            result = driver.run_spec_directly(output_dir)
            assert result["success"] is True
            assert result["return_code"] == 0

    def test_failed_run(self):
        driver = _create_driver()
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_dir = tmpdir
            bin_dir = os.path.join(tmpdir, "bin")
            os.makedirs(bin_dir)
            runspec_path = os.path.join(bin_dir, "runspec")
            with open(runspec_path, 'w') as f:
                f.write("#!/bin/bash\n")

            shrc_path = os.path.join(tmpdir, "shrc")
            with open(shrc_path, 'w') as f:
                f.write("# empty shrc\n")

            driver._build_run_command = MagicMock(return_value=["false"])

            output_dir = os.path.join(tmpdir, "output")
            result = driver.run_spec_directly(output_dir)
            assert result["success"] is False
            assert result["return_code"] != 0

    def test_env_check_failure_raises(self):
        driver = _create_driver()
        driver.spec_dir = "/nonexistent"
        with pytest.raises(FileOperationError):
            driver.run_spec_directly("/tmp/output")


