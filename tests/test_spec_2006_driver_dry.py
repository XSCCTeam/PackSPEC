"""
spec_2006_driver.py 干测试（mock-based unit tests）

测试 SPEC2006Driver 的 get_binary_path_map 和 _build_run_command 方法
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode,
)


def _create_driver(spec_benches="400", tune_type=TuneType.base,
                   input_type=InputType.ref, spec_mode=SPECMode.speed):
    """创建一个 mock 的 SPEC2006Driver 实例"""
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
                tune_type=tune_type,
                input_type=input_type,
                spec_mode=spec_mode,
                spec_benches=spec_benches,
                utils=utils,
            )
            return driver
        finally:
            os.unlink(cfg_path)


class TestSPEC2006GetBinaryPathMap:
    """SPEC2006Driver.get_binary_path_map 测试"""

    def test_finds_binary(self):
        driver = _create_driver("400")
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_bench_path = tmpdir
            # Create exe dir with binary
            exe_dir = os.path.join(tmpdir, "400.perlbench", "exe")
            os.makedirs(exe_dir)
            binary_path = os.path.join(exe_dir, "perlbench_base.test_label")
            with open(binary_path, 'w') as f:
                f.write("")

            result = driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            assert "400.perlbench" in result
            assert result["400.perlbench"] == binary_path

    def test_missing_exe_dir_skips(self):
        driver = _create_driver("400")
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_bench_path = tmpdir
            # No exe dir
            os.makedirs(os.path.join(tmpdir, "400.perlbench"))
            result = driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            assert result == {}

    def test_missing_binary_skips(self):
        driver = _create_driver("400")
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_bench_path = tmpdir
            exe_dir = os.path.join(tmpdir, "400.perlbench", "exe")
            os.makedirs(exe_dir)
            # No binary file
            result = driver.get_binary_path_map(TuneType.base, InputType.ref, SPECMode.speed)
            assert result == {}

    def test_peak_tune_type(self):
        driver = _create_driver("400")
        with tempfile.TemporaryDirectory() as tmpdir:
            driver.spec_bench_path = tmpdir
            exe_dir = os.path.join(tmpdir, "400.perlbench", "exe")
            os.makedirs(exe_dir)
            binary_path = os.path.join(exe_dir, "perlbench_peak.test_label")
            with open(binary_path, 'w') as f:
                f.write("")

            result = driver.get_binary_path_map(TuneType.peak, InputType.ref, SPECMode.speed)
            assert "400.perlbench" in result


class TestSPEC2006BuildRunCommand:
    """SPEC2006Driver._build_run_command 测试"""

    def test_basic_command(self):
        driver = _create_driver("400")
        cmd = driver._build_run_command()
        assert cmd[0].endswith("runspec")
        assert "--config" in cmd
        assert "--tune" in cmd
        assert "--size" in cmd
        assert "--iterations" in cmd
        assert "--noreportable" in cmd

    def test_tune_all(self):
        driver = _create_driver("400", tune_type=TuneType.all)
        cmd = driver._build_run_command()
        idx = cmd.index("--tune")
        assert cmd[idx + 1] == "base,peak"

    def test_input_all(self):
        driver = _create_driver("400", input_type=InputType.all)
        cmd = driver._build_run_command()
        idx = cmd.index("--size")
        assert cmd[idx + 1] == "test,train,ref"

    def test_rate_mode(self):
        driver = _create_driver("400", spec_mode=SPECMode.rate)
        cmd = driver._build_run_command()
        assert "--rate" in cmd

    def test_speed_mode_no_rate(self):
        driver = _create_driver("400", spec_mode=SPECMode.speed)
        cmd = driver._build_run_command()
        assert "--rate" not in cmd

    def test_bench_list_in_command(self):
        driver = _create_driver("400")
        cmd = driver._build_run_command()
        assert "400.perlbench" in cmd
