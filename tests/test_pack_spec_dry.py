"""
pack_spec.py 干测试（mock-based unit tests）

测试 PackSPEC 的 copy_binaries、copy_benches、setup_spec、run_spec、
pack_qemu_verify、run 方法中未覆盖的分支
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
import shutil

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode, RunMode,
    ConfigError, FileOperationError, CommandExecutionError,
    PackSPECError,
    DEFAULT_CORE_NUM,
)
from src.pack_spec.pack_spec import PackSPEC


def _create_packer(**overrides):
    """创建一个 mock 的 PackSPEC 实例"""
    config = {
        "task": {"pack_name": "test", "setup_spec": False, "pack_binaries": False,
                 "pack_benches": False, "pack_builds": False},
        "spec_config": {
            "spec_cfg_path": "/tmp/test.cfg",
            "spec_name": SPECName.spec2017,
            "tune_type": TuneType.base,
            "input_type": InputType.ref,
            "spec_mode": SPECMode.speed,
            "spec_benches": "all",
        },
        "pack_config": {"auto_mode": True, "verify_mode": False},
        "msg_config": {},
    }
    # Apply overrides
    for key, val in overrides.items():
        if "." in key:
            section, field = key.split(".", 1)
            config[section][field] = val
        else:
            config[key] = val

    with patch('src.pack_spec.pack_spec.setup_logger', return_value="/tmp/log"), \
         patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
         patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls:
        mock_utils = MagicMock()
        mock_utils.create_generated_dir.return_value = "/tmp/gen"
        mock_utils.get_pack_generated_dir_path.return_value = "/tmp/gen"
        mock_utils.save_pack_spec_cfg = MagicMock()
        mock_utils.msg = MagicMock()
        mock_utils.msg.get = MagicMock(return_value="mock")
        mock_utils_cls.return_value = mock_utils

        mock_driver = MagicMock()
        mock_driver.get_spec_info.return_value = {
            "spec_name": "SPEC CPU 2017", "spec_version": "v1.0.2", "spec_path": "/fake"
        }
        mock_driver.spec_bench_list = ["600.perlbench_s", "602.gcc_s"]
        mock_driver.spec_bench_map = {"600.perlbench_s": "perlbench_s", "602.gcc_s": "sgcc"}
        mock_driver.label = "test_label"
        mock_driver.spec_dir = "/fake/spec2017"
        mock_driver.utils = mock_utils
        mock_create.return_value = mock_driver

        packer = PackSPEC(config)
        return packer


class TestPackSPECInitFromFile:
    """PackSPEC 从文件路径初始化测试"""

    def test_init_from_file_path(self):
        config_data = {
            "task": {"pack_name": "file_test"},
            "spec_config": {
                "spec_cfg_path": "/tmp/test.cfg",
                "spec_name": SPECName.spec2017,
                "tune_type": TuneType.base,
                "input_type": InputType.ref,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
            "date": "260101",
        }
        with patch('src.pack_spec.pack_spec.load_pack_spec_cfg', return_value=config_data), \
             patch('src.pack_spec.pack_spec.setup_logger', return_value="/tmp/log"), \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls:
            mock_utils = MagicMock()
            mock_utils.get_pack_generated_dir_path.return_value = "/tmp/gen"
            mock_utils.msg = MagicMock()
            mock_utils.msg.get = MagicMock(return_value="mock")
            mock_utils_cls.return_value = mock_utils
            mock_create.return_value = MagicMock(
                get_spec_info=MagicMock(return_value={"spec_name": "X", "spec_version": "1", "spec_path": "/x"})
            )

            packer = PackSPEC("/fake/config.json")
            assert packer.pack_name == "file_test"
            assert packer.init_date == "260101"


class TestCopyBinariesDry:
    """PackSPEC.copy_binaries 干测试"""

    def test_copies_binaries_to_dest(self):
        packer = _create_packer()
        packer.spec_driver.get_binary_path_map.return_value = {
            "600.perlbench_s": "/fake/perlbench_s"
        }
        packer.utils.create_dest_dir.return_value = "/tmp/dest"
        packer.utils.copy_file_to_target_dir.return_value = True

        result = packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)
        assert result == "/tmp/dest"
        packer.utils.copy_file_to_target_dir.assert_called()

    def test_empty_binary_map_raises(self):
        packer = _create_packer()
        packer.spec_driver.get_binary_path_map.return_value = {}
        packer.utils.create_dest_dir.return_value = "/tmp/dest"

        with pytest.raises(FileOperationError):
            packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)

    def test_custom_dest_dir(self):
        packer = _create_packer()
        packer.spec_driver.get_binary_path_map.return_value = {
            "600.perlbench_s": "/fake/perlbench_s"
        }
        packer.utils.copy_file_to_target_dir.return_value = True

        result = packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed,
                                      dest_binary_dir="/custom/dir")
        assert result == "/custom/dir"


class TestCopyBenchesDry:
    """PackSPEC.copy_benches 干测试"""

    def test_copies_run_dirs(self):
        packer = _create_packer()
        packer.spec_driver.spec_bench_list = ["600.perlbench_s"]
        packer.spec_driver.get_bench_path.return_value = ["/fake/run_dir"]
        packer.utils.get_bench_dir.return_value = "/fake/run_dir"
        packer.utils.create_dest_dir.return_value = "/tmp/dest"
        packer.spec_driver.execute_specinvoke.return_value = True
        packer.spec_driver.execute_specdiff.return_value = True
        packer.spec_driver.get_ref_time.return_value = "1600"

        with patch('shutil.copytree'), \
             patch.object(packer, 'create_test_script'), \
             patch.object(packer, 'create_run_all_script'), \
             patch.object(packer, 'create_specdiff_all_script'):
            result = packer.copy_benches(TuneType.base, InputType.ref, SPECMode.speed)
            assert len(result) == 1

    def test_empty_bench_dir_raises(self):
        packer = _create_packer()
        packer.spec_driver.spec_bench_list = ["600.perlbench_s"]
        packer.spec_driver.get_bench_path.return_value = []
        packer.utils.get_bench_dir.return_value = ""
        packer.utils.create_dest_dir.return_value = "/tmp/dest"

        with pytest.raises(FileOperationError):
            packer.copy_benches(TuneType.base, InputType.ref, SPECMode.speed)

    def test_with_build_bench_dir_not_found_skips_and_raises(self):
        """测试 with_build=True 且 src_build_dir 未找到时跳过所有 bench 并抛异常"""
        packer = _create_packer()
        packer.spec_driver.spec_bench_list = ["600.perlbench_s"]
        # get_bench_dir 对 build 返回空（模拟找不到）
        packer.utils.get_bench_dir.return_value = ""
        packer.utils.create_dest_dir.return_value = "/tmp/dest"
        packer.spec_driver.get_bench_path.return_value = ["/fake/build_dir"]

        with pytest.raises(FileOperationError, match="没有基准测试可复制"):
            packer.copy_benches(TuneType.base, InputType.ref, SPECMode.speed, with_build=True)


class TestSetupSpecDry:
    """PackSPEC.setup_spec 干测试"""

    def test_copies_cfg_and_calls_run_setup(self):
        packer = _create_packer()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write("label = test\n")
            packer.spec_cfg_path = f.name

        try:
            packer.utils.get_pack_generated_dir_path.return_value = tempfile.mkdtemp()
            packer.spec_driver.run_setup_spec.return_value = "/tmp/setup.log"
            packer.utils.inject_riscv_x264_submit.return_value = False
            packer.utils.copy_spec_detail_log_to_generated_dir = MagicMock()

            packer.setup_spec()
            packer.spec_driver.run_setup_spec.assert_called_once()
        finally:
            os.unlink(packer.spec_cfg_path)
            shutil.rmtree(packer.utils.get_pack_generated_dir_path.return_value)


class TestRunSpecDry:
    """PackSPEC.run_spec 干测试"""

    def test_successful_run_generates_report(self):
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.return_value = {
            "success": True, "output_dir": "/tmp/out", "log_file": "/tmp/log",
            "return_code": 0, "error_message": ""
        }
        with patch('src.pack_spec.pack_spec.parse_spec_results', return_value={"int_score": 10.0, "fp_score": 5.0}), \
             patch('src.pack_spec.pack_spec.generate_json_report', return_value="/tmp/report.json"):
            result = packer.run_spec(output_dir="/tmp/out")
            assert result["success"] is True
            assert "results" in result
            assert "report_path" in result

    def test_failed_run_returns_failure(self):
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.return_value = {
            "success": False, "output_dir": "/tmp/out", "log_file": "/tmp/log",
            "return_code": 1, "error_message": "failed"
        }
        result = packer.run_spec(output_dir="/tmp/out")
        assert result["success"] is False

    def test_env_check_failure_raises(self):
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.side_effect = FileOperationError("no dir")
        with pytest.raises(FileOperationError):
            packer.run_spec(output_dir="/tmp/out")

    def test_command_execution_error_raises(self):
        """测试 run_spec 中 CommandExecutionError 被重新抛出"""
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.side_effect = CommandExecutionError("exec failed")
        with pytest.raises(CommandExecutionError):
            packer.run_spec(output_dir="/tmp/out")

    def test_generic_exception_wraps_as_command_error(self):
        """测试 run_spec 中通用异常被包装为 CommandExecutionError"""
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.side_effect = RuntimeError("unexpected error")
        with pytest.raises(CommandExecutionError, match="unexpected error"):
            packer.run_spec(output_dir="/tmp/out")

    def test_run_spec_without_report(self):
        """测试 run_spec 不生成报告时返回结果正确"""
        packer = _create_packer()
        packer.spec_driver.run_spec_directly.return_value = {
            "success": True, "output_dir": "/tmp/out", "log_file": "/tmp/log",
            "return_code": 0, "error_message": ""
        }
        result = packer.run_spec(output_dir="/tmp/out", generate_report=False)
        assert result["success"] is True
        assert "results" not in result

    def test_markdown_report_format(self):
        packer = _create_packer()
        packer.report_format = "markdown"
        packer.spec_driver.run_spec_directly.return_value = {
            "success": True, "output_dir": "/tmp/out", "log_file": "/tmp/log",
            "return_code": 0, "error_message": ""
        }
        with patch('src.pack_spec.pack_spec.parse_spec_results', return_value={"int_score": 0, "fp_score": 0}), \
             patch('src.pack_spec.pack_spec.generate_markdown_report', return_value="/tmp/report.md"):
            result = packer.run_spec(output_dir="/tmp/out")
            assert result["report_path"].endswith(".md")


class TestPackQemuVerifyDry:
    """PackSPEC.pack_qemu_verify 干测试"""

    def test_no_qemu_path_raises(self):
        packer = _create_packer()
        packer.verify_mode = True
        with patch('src.pack_spec.pack_spec.QEMU_PATH', None):
            with pytest.raises(ConfigError):
                packer.pack_qemu_verify()

    def test_verify_mode_false_raises(self):
        packer = _create_packer()
        packer.verify_mode = False
        with patch('src.pack_spec.pack_spec.QEMU_PATH', '/fake/qemu'):
            with pytest.raises(ConfigError):
                packer.pack_qemu_verify()

    def test_qemu_dir_not_exists_raises(self):
        """测试 QEMU_PATH 目录不存在时抛出 ConfigError"""
        packer = _create_packer()
        packer.verify_mode = True
        with patch('src.pack_spec.pack_spec.QEMU_PATH', '/nonexistent/qemu'), \
             patch('os.path.isdir', return_value=False):
            with pytest.raises(ConfigError):
                packer.pack_qemu_verify()

    def test_non_auto_mode_dir_exists_raises(self):
        """测试非自动模式下 _qemu_verify 目录已存在且不能覆盖时抛出"""
        packer = _create_packer()
        packer.verify_mode = True
        packer.auto_mode = False
        packer.spec_driver.spec_bench_list = ["600.perlbench_s"]
        with patch('src.pack_spec.pack_spec.QEMU_PATH', '/fake/qemu'), \
             patch('os.path.isdir', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('os.makedirs'):
            with pytest.raises(PackSPECError):
                packer.pack_qemu_verify()

    def test_run_dir_not_found_raises(self):
        """测试 run 目录不存在时抛出 FileOperationError"""
        packer = _create_packer()
        packer.verify_mode = True
        packer.auto_mode = True
        packer.spec_driver.spec_bench_list = ["600.perlbench_s"]
        with patch('src.pack_spec.pack_spec.QEMU_PATH', '/fake/qemu'), \
             patch('os.path.isdir', return_value=True), \
             patch('os.path.exists', return_value=False), \
             patch('os.makedirs'):
            with pytest.raises(FileOperationError):
                packer.pack_qemu_verify()


class TestRunMethodDry:
    """PackSPEC.run 方法干测试"""

    def test_direct_mode_calls_run_spec(self):
        packer = _create_packer()
        packer.run_mode = RunMode.direct
        packer.spec_driver.run_spec_directly.return_value = {
            "success": True, "output_dir": "/tmp/out", "log_file": "/tmp/log",
            "return_code": 0, "error_message": ""
        }
        with patch('src.pack_spec.pack_spec.parse_spec_results', return_value={"int_score": 0, "fp_score": 0}), \
             patch('src.pack_spec.pack_spec.generate_json_report', return_value="/tmp/r.json"):
            result = packer.run()
            assert "run_spec" in result["steps"]

    def test_pack_mode_setup_and_binaries(self):
        packer = _create_packer()
        packer.run_mode = RunMode.pack
        packer.setup_spec_enabled = True
        packer.pack_binaries_enabled = True

        with patch.object(packer, 'setup_spec') as mock_setup, \
             patch.object(packer, 'pack_binaries') as mock_bin:
            result = packer.run()
            mock_setup.assert_called_once()
            mock_bin.assert_called_once()
            assert "setup_spec" in result["steps"]
            assert "pack_binaries" in result["steps"]

    def test_pack_mode_verify(self):
        packer = _create_packer()
        packer.run_mode = RunMode.pack
        packer.verify_mode = True
        packer.setup_spec_enabled = False
        packer.pack_binaries_enabled = False
        packer.pack_benches_enabled = False
        packer.pack_builds_enabled = False

        with patch.object(packer, 'pack_qemu_verify', return_value={"success": True}):
            result = packer.run()
            assert "pack_qemu_verify" in result["steps"]

    def test_pack_mode_benches_and_builds(self):
        packer = _create_packer()
        packer.run_mode = RunMode.pack
        packer.setup_spec_enabled = False
        packer.pack_binaries_enabled = False
        packer.pack_benches_enabled = True
        packer.pack_builds_enabled = True
        packer.verify_mode = False

        with patch.object(packer, 'pack_benches_cfg') as mock_benches:
            result = packer.run()
            # pack_benches_cfg called twice: once without with_build, once with
            assert mock_benches.call_count == 2
            assert "pack_benches_cfg" in result["steps"]
            assert "pack_builds" in result["steps"]


class TestCreateRunAllScriptDry:
    """PackSPEC.create_run_all_script 边界测试"""

    def test_empty_bench_list_returns_early(self):
        """测试空 bench 列表时 create_run_all_script 直接返回而不写文件"""
        packer = _create_packer()
        with patch('builtins.open') as mock_open:
            packer.create_run_all_script("label", -1, [], TuneType.base, InputType.test)
            mock_open.assert_not_called()

    def test_empty_bench_list_for_specdiff_returns_early(self):
        """测试空 bench 列表时 create_specdiff_all_script 直接返回"""
        packer = _create_packer()
        with patch('builtins.open') as mock_open:
            packer.create_specdiff_all_script([], InputType.test)
            mock_open.assert_not_called()


class TestSetupSpecDryExtended:
    """PackSPEC.setup_spec 扩展测试"""

    def test_setup_spec_updates_cfg_label_when_different(self):
        """测试当 pack_name 与 driver.label 不同时更新 cfg 的 label"""
        packer = _create_packer()
        packer.pack_name = "my_custom_label"
        packer.spec_driver.label = "old_label"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write("label = old_label\n")
            cfg_path = f.name

        try:
            packer.spec_cfg_path = cfg_path
            packer.utils.get_pack_generated_dir_path.return_value = tempfile.mkdtemp()
            packer.spec_driver.run_setup_spec.return_value = "/tmp/setup.log"
            packer.utils.inject_riscv_x264_submit.return_value = False
            packer.utils.copy_spec_detail_log_to_generated_dir = MagicMock()
            packer.utils.update_cfg_label = MagicMock()

            packer.setup_spec()
            packer.utils.update_cfg_label.assert_called_once()
        finally:
            os.unlink(cfg_path)
            shutil.rmtree(packer.utils.get_pack_generated_dir_path.return_value)
