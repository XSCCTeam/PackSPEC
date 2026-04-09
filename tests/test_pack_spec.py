"""
pack_spec.py 单元测试

测试 PackSPEC 类初始化、配置解析、run() 方法等
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode, RunMode,
    ConfigError, FileOperationError,
    DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_ITERATIONS,
    DEFAULT_REBUILD, DEFAULT_PROFILE_GEN, DEFAULT_AUTO_MODE,
    DEFAULT_VERIFY_MODE, DEFAULT_MINIMAL_MODE, DEFAULT_RUN_MODE,
    DEFAULT_REPORT_FORMAT,
)
from src.pack_spec.pack_spec import PackSPEC


class TestPackSPECInit:
    """PackSPEC 类初始化测试"""

    @patch('src.pack_spec.pack_spec.SPEC2006Driver')
    @patch('src.pack_spec.pack_spec.PackUtils')
    def test_init_with_dict_config(self, mock_utils_cls, mock_driver_cls):
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/tmp/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        mock_utils_instance = MagicMock()
        mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
        mock_utils_instance.save_pack_spec_cfg = MagicMock()
        mock_utils_cls.return_value = mock_utils_instance
        mock_driver_cls.return_value = MagicMock()
        packer = PackSPEC(config)
        assert packer.pack_name == "test"

    def test_init_with_invalid_type_raises(self):
        with pytest.raises(ValueError):
            PackSPEC(123)


class TestPackSPECInitPackSpec:
    """init_pack_spec 方法测试"""

    def _create_packer(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPEC2006Driver') as mock_driver:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            return PackSPEC(config)

    def test_task_config_parsing(self, base_config):
        packer = self._create_packer(base_config)
        assert packer.pack_name == "test_pack"
        assert packer.setup_spec_enabled is False
        assert packer.pack_binaries_enabled is True
        assert packer.pack_benches_enabled is True

    def test_spec_config_parsing(self, base_config):
        packer = self._create_packer(base_config)
        assert packer.spec_cfg_path == "/tmp/test/spec.cfg"
        assert packer.spec_name == SPECName.spec2006
        assert packer.tune_type == TuneType.base
        assert packer.input_type == InputType.test
        assert packer.spec_mode == SPECMode.speed
        assert packer.spec_benches == "all"
        assert packer.iterations == 1
        assert packer.rebuild is False

    def test_pack_config_parsing(self, base_config):
        packer = self._create_packer(base_config)
        assert packer.test_core_num == DEFAULT_CORE_NUM
        assert packer.test_clock_rate == DEFAULT_CLOCK_RATE
        assert packer.profile_gen is DEFAULT_PROFILE_GEN
        assert packer.auto_mode is True
        assert packer.verify_mode is DEFAULT_VERIFY_MODE
        assert packer.minimal_mode is DEFAULT_MINIMAL_MODE
        assert packer.run_mode == DEFAULT_RUN_MODE
        assert packer.report_format == DEFAULT_REPORT_FORMAT

    def test_msg_config_parsing(self, base_config):
        packer = self._create_packer(base_config)
        assert packer.msg_enabled is False

    def test_profile_gen_forces_iterations_to_1(self):
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/tmp/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
                "iterations": 3,
            },
            "pack_config": {"auto_mode": True, "profile_gen": True},
        }
        packer = self._create_packer(config)
        assert packer.iterations == 1

    def test_default_values_when_missing(self):
        config = {
            "spec_config": {
                "spec_cfg_path": "/tmp/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        packer = self._create_packer(config)
        assert packer.pack_name == "packspec"
        assert packer.setup_spec_enabled is False
        assert packer.pack_binaries_enabled is True
        assert packer.pack_benches_enabled is True
        assert packer.msg_enabled is False

    def test_spec2017_driver_creation(self):
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/tmp/test.cfg",
                "spec_name": SPECName.spec2017,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPEC2017Driver') as mock_driver:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            packer = PackSPEC(config)
            assert packer.spec_name == SPECName.spec2017


class TestPackSPECRun:
    """run() 方法测试"""

    def _create_packer_with_mocks(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPEC2006Driver') as mock_driver:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            packer = PackSPEC(config)
        return packer

    def test_run_all_enabled(self, base_config):
        base_config["task"]["setup_spec"] = True
        base_config["task"]["pack_binaries"] = True
        base_config["task"]["pack_benches"] = True
        base_config["pack_config"]["verify_mode"] = True

        packer = self._create_packer_with_mocks(base_config)
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()

        result = packer.run()

        packer.setup_spec.assert_called_once()
        packer.pack_binaries.assert_called_once()
        packer.pack_benches_cfg.assert_called_once()
        packer.pack_qemu_verify.assert_called_once()
        assert result["success"] is True
        assert "setup_spec" in result["steps"]
        assert "pack_binaries" in result["steps"]
        assert "pack_benches_cfg" in result["steps"]
        assert "pack_qemu_verify" in result["steps"]

    def test_run_only_pack_binaries(self, base_config):
        base_config["task"]["setup_spec"] = False
        base_config["task"]["pack_binaries"] = True
        base_config["task"]["pack_benches"] = False
        base_config["pack_config"]["verify_mode"] = False

        packer = self._create_packer_with_mocks(base_config)
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()

        result = packer.run()

        packer.setup_spec.assert_not_called()
        packer.pack_binaries.assert_called_once()
        packer.pack_benches_cfg.assert_not_called()
        packer.pack_qemu_verify.assert_not_called()
        assert "pack_binaries" in result["steps"]
        assert "setup_spec" not in result["steps"]

    def test_run_all_disabled(self, base_config):
        base_config["task"]["setup_spec"] = False
        base_config["task"]["pack_binaries"] = False
        base_config["task"]["pack_benches"] = False
        base_config["pack_config"]["verify_mode"] = False

        packer = self._create_packer_with_mocks(base_config)
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()

        result = packer.run()

        packer.setup_spec.assert_not_called()
        packer.pack_binaries.assert_not_called()
        packer.pack_benches_cfg.assert_not_called()
        packer.pack_qemu_verify.assert_not_called()
        assert result["steps"] == []
        assert result["success"] is True
