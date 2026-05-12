"""
pack_spec.py 单元测试

测试 PackSPEC 类初始化、配置解析、run() 方法等
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode, RunMode, ConfigError,
    DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_PROFILE_GEN, DEFAULT_VERIFY_MODE,
    DEFAULT_MINIMAL_MODE, DEFAULT_RUN_MODE,
    DEFAULT_REPORT_FORMAT, DEFAULT_PACK_BUILDS,
)
from src.pack_spec.pack_spec import PackSPEC


class TestPackSPECInit:
    """PackSPEC 类初始化测试"""

    @patch('src.pack_spec.pack_spec.setup_logger')
    @patch('src.pack_spec.pack_spec.SPECDriver.create')
    @patch('src.pack_spec.pack_spec.PackUtils')
    def test_init_with_dict_config(self, mock_utils_cls, mock_create, mock_setup_logger):
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
        mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
        mock_utils_instance.save_pack_spec_cfg = MagicMock()
        mock_utils_cls.return_value = mock_utils_instance
        mock_create.return_value = MagicMock()
        mock_setup_logger.return_value = "/tmp/test/log/test.log"
        packer = PackSPEC(config)
        assert packer.pack_name == "test"

    def test_init_with_invalid_type_raises(self):
        with pytest.raises(ValueError):
            PackSPEC(123)


class TestPackSPECInitPackSpec:
    """init_pack_spec 方法测试"""

    def _create_packer(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
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

    def test_pack_builds_default_false(self, base_config):
        """测试pack_builds默认值为False"""
        packer = self._create_packer(base_config)
        assert packer.pack_builds_enabled is DEFAULT_PACK_BUILDS
        assert packer.pack_builds_enabled is False

    def test_pack_builds_explicit_true(self):
        """测试显式设置pack_builds=True"""
        config = {
            "task": {"pack_name": "test", "pack_builds": True},
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
        assert packer.pack_builds_enabled is True

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
        assert packer.pack_binaries_enabled is False
        assert packer.pack_benches_enabled is False
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
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
            assert packer.spec_name == SPECName.spec2017


class TestPackSPECRun:
    """run() 方法测试"""

    def _create_packer_with_mocks(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
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

    def test_run_pack_builds_calls_with_build_true(self, base_config):
        """测试pack_builds=True时作为独立步骤执行pack_benches_cfg(with_build=True)"""
        base_config["task"]["pack_benches"] = True
        base_config["task"]["pack_builds"] = True

        packer = self._create_packer_with_mocks(base_config)
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()

        result = packer.run()

        packer.pack_benches_cfg.assert_called()
        assert "pack_builds" in result["steps"]

    def test_run_pack_builds_false_no_effect(self, base_config):
        """测试pack_builds=False时pack_builds步骤不执行"""
        base_config["task"]["pack_benches"] = True

        packer = self._create_packer_with_mocks(base_config)
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()

        result = packer.run()

        packer.pack_benches_cfg.assert_called_once_with()
        assert "pack_benches_cfg" in result["steps"]


class TestSetupSpecCfgIsolation:
    """setup_spec 配置文件隔离测试"""

    @patch('src.pack_spec.pack_spec.setup_logger')
    @patch('src.pack_spec.pack_spec.SPECDriver.create')
    @patch('src.pack_spec.pack_spec.PackUtils')
    @patch('src.pack_spec.pack_spec.os.makedirs')
    @patch('src.pack_spec.pack_spec.shutil.copy2')
    @patch('src.pack_spec.pack_spec.os.path.exists')
    @patch('src.pack_spec.pack_spec.os.path.join')
    @patch('src.pack_spec.pack_spec.os.path.basename')
    def test_setup_spec_copies_cfg_file(
        self, mock_basename, mock_join, mock_exists, mock_copy2, mock_makedirs,
        mock_utils_cls, mock_create, mock_setup_logger
    ):
        """测试 setup_spec 会复制 cfg 文件到 generated_files 目录"""
        mock_basename.return_value = "test.cfg"
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_exists.return_value = True
        mock_setup_logger.return_value = "/tmp/test/log/PackSpec_test.log"
        
        mock_utils_instance = MagicMock()
        mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
        mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
        mock_utils_instance.save_pack_spec_cfg = MagicMock()
        mock_utils_instance.msg = MagicMock()
        mock_utils_instance.msg.get = MagicMock(return_value="test message")
        mock_utils_cls.return_value = mock_utils_instance
        
        mock_driver_instance = MagicMock()
        mock_driver_instance.spec_cfg_path = "/original/path/test.cfg"
        mock_create.return_value = mock_driver_instance
        
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/original/path/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        
        packer = PackSPEC(config)
        packer.spec_cfg_path = "/original/path/test.cfg"
        packer.setup_spec()
        
        mock_makedirs.assert_called()
        mock_copy2.assert_called_once()

    @patch('src.pack_spec.pack_spec.setup_logger')
    @patch('src.pack_spec.pack_spec.SPECDriver.create')
    @patch('src.pack_spec.pack_spec.PackUtils')
    @patch('src.pack_spec.pack_spec.os.makedirs')
    @patch('src.pack_spec.pack_spec.shutil.copy2')
    @patch('src.pack_spec.pack_spec.os.path.exists')
    @patch('src.pack_spec.pack_spec.os.path.join')
    @patch('src.pack_spec.pack_spec.os.path.basename')
    def test_setup_spec_uses_copied_cfg(
        self, mock_basename, mock_join, mock_exists, mock_copy2, mock_makedirs,
        mock_utils_cls, mock_create, mock_setup_logger
    ):
        """测试 setup_spec 使用复制后的 cfg 文件路径"""
        mock_basename.return_value = "test.cfg"
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_exists.return_value = True
        mock_setup_logger.return_value = "/tmp/test/log/PackSpec_test.log"
        
        mock_utils_instance = MagicMock()
        mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
        mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
        mock_utils_instance.save_pack_spec_cfg = MagicMock()
        mock_utils_instance.msg = MagicMock()
        mock_utils_instance.msg.get = MagicMock(return_value="test message")
        mock_utils_cls.return_value = mock_utils_instance
        
        mock_driver_instance = MagicMock()
        mock_driver_instance.spec_cfg_path = "/original/path/test.cfg"
        mock_create.return_value = mock_driver_instance
        
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/original/path/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        
        packer = PackSPEC(config)
        packer.spec_cfg_path = "/original/path/test.cfg"
        packer.setup_spec()
        
        assert mock_driver_instance.spec_cfg_path == "/tmp/test/cfg/test.cfg"

    @patch('src.pack_spec.pack_spec.setup_logger')
    @patch('src.pack_spec.pack_spec.SPECDriver.create')
    @patch('src.pack_spec.pack_spec.PackUtils')
    @patch('src.pack_spec.pack_spec.os.makedirs')
    @patch('src.pack_spec.pack_spec.shutil.copy2')
    @patch('src.pack_spec.pack_spec.os.path.exists')
    @patch('src.pack_spec.pack_spec.os.path.join')
    @patch('src.pack_spec.pack_spec.os.path.basename')
    def test_setup_spec_calls_copy_spec_detail_log(
        self, mock_basename, mock_join, mock_exists, mock_copy2, mock_makedirs,
        mock_utils_cls, mock_create, mock_setup_logger
    ):
        """测试 setup_spec 执行后调用 copy_spec_detail_log_to_generated_dir"""
        mock_basename.return_value = "test.cfg"
        mock_join.side_effect = lambda *args: "/".join(args)
        mock_exists.return_value = True
        mock_setup_logger.return_value = "/tmp/test/log/PackSpec_test.log"
        
        mock_utils_instance = MagicMock()
        mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
        mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
        mock_utils_instance.save_pack_spec_cfg = MagicMock()
        mock_utils_instance.msg = MagicMock()
        mock_utils_instance.msg.get = MagicMock(return_value="test message")
        mock_utils_cls.return_value = mock_utils_instance
        
        mock_driver_instance = MagicMock()
        mock_driver_instance.spec_cfg_path = "/original/path/test.cfg"
        mock_driver_instance.spec_dir = "/spec_dir"
        mock_driver_instance.run_setup_spec.return_value = "/tmp/test/test.base_ref.setuplog"
        mock_create.return_value = mock_driver_instance
        
        config = {
            "task": {"pack_name": "test"},
            "spec_config": {
                "spec_cfg_path": "/original/path/test.cfg",
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.test,
                "spec_mode": SPECMode.speed,
                "spec_benches": "all",
            },
            "pack_config": {"auto_mode": True},
        }
        
        packer = PackSPEC(config)
        packer.spec_cfg_path = "/original/path/test.cfg"
        packer.setup_spec()
        
        mock_driver_instance.run_setup_spec.assert_called_once()
        mock_utils_instance.copy_spec_detail_log_to_generated_dir.assert_called_once_with(
            "/spec_dir", "/tmp/test/test.base_ref.setuplog", "/tmp/test"
        )


class TestCopyBenchesWithBuild:
    """copy_benches 方法 with_build 条件分支测试"""

    def _create_packer_with_mocks(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.create_dest_dir.return_value = "/tmp/dest_run"
            mock_utils_instance.get_bench_dir.return_value = "/tmp/run/400.perlbench"
            mock_utils_instance.get_run_script_name.return_value = "test_test.sh"
            mock_utils_instance.commands_to_prepare_run.return_value = ["#!/bin/bash"]
            mock_utils_instance.commands_to_cal_score.return_value = ["score_cmd"]
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.get_bench_path.return_value = "/tmp/bench/run"
            mock_driver_instance.spec_bench_list = ["400.perlbench"]
            mock_driver_instance.execute_specinvoke.return_value = True
            mock_driver_instance.execute_specdiff.return_value = None
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_bench_map = {}
            mock_driver_instance.get_ref_time.return_value = 0
            mock_driver_instance.utils = mock_utils_instance
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
        return packer

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    @patch('src.pack_spec.pack_spec.os.chmod')
    @patch('src.pack_spec.pack_spec.open', MagicMock())
    def test_copy_benches_without_build_no_name_error(self, mock_chmod, mock_copytree, base_config):
        """测试with_build=False时不引用未定义的src_build_bench_dir，不会引发NameError"""
        packer = self._create_packer_with_mocks(base_config)
        result = packer.copy_benches(
            tune_type=TuneType.base,
            input_type=InputType.test,
            spec_mode=SPECMode.speed,
            with_build=False
        )
        assert isinstance(result, list)

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    @patch('src.pack_spec.pack_spec.os.chmod')
    @patch('src.pack_spec.pack_spec.open', MagicMock())
    def test_copy_benches_without_build_does_not_call_get_bench_path_build(self, mock_chmod, mock_copytree, base_config):
        """测试with_build=False时不调用get_bench_path(ActionType.build, ...)"""
        packer = self._create_packer_with_mocks(base_config)
        packer.copy_benches(
            tune_type=TuneType.base,
            input_type=InputType.test,
            spec_mode=SPECMode.speed,
            with_build=False
        )
        from src.pack_spec.pack_config import ActionType
        build_calls = [
            call for call in packer.spec_driver.get_bench_path.call_args_list
            if call[0][0] == ActionType.build
        ]
        assert len(build_calls) == 0

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    @patch('src.pack_spec.pack_spec.os.chmod')
    @patch('src.pack_spec.pack_spec.open', MagicMock())
    def test_copy_benches_with_build_calls_get_bench_path_build(self, mock_chmod, mock_copytree, base_config):
        """测试with_build=True时调用get_bench_path(ActionType.build, ...)"""
        packer = self._create_packer_with_mocks(base_config)
        packer.utils.get_bench_dir.side_effect = ["/tmp/build/400.perlbench", "/tmp/run/400.perlbench"]
        packer.copy_benches(
            tune_type=TuneType.base,
            input_type=InputType.test,
            spec_mode=SPECMode.speed,
            with_build=True
        )
        from src.pack_spec.pack_config import ActionType
        build_calls = [
            call for call in packer.spec_driver.get_bench_path.call_args_list
            if call[0][0] == ActionType.build
        ]
        assert len(build_calls) == 1

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    @patch('src.pack_spec.pack_spec.os.chmod')
    @patch('src.pack_spec.pack_spec.open', MagicMock())
    def test_copy_benches_without_build_uses_run_mode_dest_dir(self, mock_chmod, mock_copytree, base_config):
        """测试with_build=False时使用PACKMode.run创建目标目录"""
        packer = self._create_packer_with_mocks(base_config)
        packer.copy_benches(
            tune_type=TuneType.base,
            input_type=InputType.test,
            spec_mode=SPECMode.speed,
            with_build=False
        )
        packer.utils.create_dest_dir.assert_called_once_with(
            packer.profile_gen, packer.auto_mode, PACKMode.run,
            packer.spec_name, TuneType.base, InputType.test, SPECMode.speed
        )

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    @patch('src.pack_spec.pack_spec.os.chmod')
    @patch('src.pack_spec.pack_spec.open', MagicMock())
    def test_copy_benches_with_build_uses_buildrun_mode_dest_dir(self, mock_chmod, mock_copytree, base_config):
        """测试with_build=True时使用PACKMode.buildrun创建目标目录"""
        packer = self._create_packer_with_mocks(base_config)
        packer.utils.get_bench_dir.side_effect = ["/tmp/build/400.perlbench", "/tmp/run/400.perlbench"]
        packer.utils.create_dest_dir.return_value = "/tmp/dest_buildrun"
        packer.copy_benches(
            tune_type=TuneType.base,
            input_type=InputType.test,
            spec_mode=SPECMode.speed,
            with_build=True
        )
        packer.utils.create_dest_dir.assert_called_once_with(
            packer.profile_gen, packer.auto_mode, PACKMode.buildrun,
            packer.spec_name, TuneType.base, InputType.test, SPECMode.speed
        )

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    def test_copy_benches_without_build_creates_specdiff_all_script(self, mock_copytree, base_config):
        """测试with_build=False时生成批量specdiff脚本"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, 'create_test_script'), \
             patch.object(packer, 'create_run_all_script'), \
             patch.object(packer, 'create_specdiff_all_script') as mock_specdiff_all:
            result = packer.copy_benches(
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                with_build=False
            )
        mock_specdiff_all.assert_called_once_with(result, InputType.test)

    @patch('src.pack_spec.pack_spec.shutil.copytree')
    def test_copy_benches_with_build_creates_specdiff_all_script(self, mock_copytree, base_config):
        """测试with_build=True时生成批量specdiff脚本"""
        packer = self._create_packer_with_mocks(base_config)
        packer.utils.get_bench_dir.side_effect = ["/tmp/build/400.perlbench", "/tmp/run/400.perlbench"]
        with patch.object(packer, 'create_test_script'), \
             patch.object(packer, 'create_run_all_script'), \
             patch.object(packer, 'create_specdiff_all_script') as mock_specdiff_all:
            result = packer.copy_benches(
                tune_type=TuneType.base,
                input_type=InputType.test,
                spec_mode=SPECMode.speed,
                with_build=True
            )
        mock_specdiff_all.assert_called_once_with(result, InputType.test)


class TestAddScoreAndMessageCommandsDryRun:
    """_add_score_and_message_commands 方法干跑测试"""

    def _create_packer_with_mocks(self, config, profile_gen=False, minimal_mode=False, msg_enabled=False):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.commands_to_cal_score.return_value = ["python3 cal_score.py"]
            mock_utils_instance.commands_to_send_message.return_value = ["curl -X POST ..."]
            mock_utils_instance.commands_to_send_md_message.return_value = ["curl -X POST ... md"]
            mock_utils_instance.copy_script_file_to_target_dir.return_value = True
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_bench_map = {"400.perlbench": "perlbench"}
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
            packer.profile_gen = profile_gen
            packer.minimal_mode = minimal_mode
            packer.msg_enabled = msg_enabled
            packer.test_clock_rate = 1.0
        return packer

    def test_profile_gen_only_sends_completion_message(self, base_config):
        """测试profile_gen模式且配置API密钥时，只发送完成消息不计算分数"""
        packer = self._create_packer_with_mocks(base_config, profile_gen=True)
        script_content = []
        with patch('src.pack_spec.pack_spec.BOSC_API_KEY', 'test_key'), \
             patch('src.pack_spec.pack_spec.BOSC_AT_USER', 'test_user'):
            packer._add_score_and_message_commands(
                script_content, "/tmp/score_dir", "test_label",
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_send_message.assert_called()
        packer.utils.commands_to_cal_score.assert_not_called()

    def test_no_api_key_only_calculates_score(self, base_config):
        """测试未配置API密钥时，只计算分数不发送消息"""
        packer = self._create_packer_with_mocks(base_config)
        script_content = []
        with patch('src.pack_spec.pack_spec.BOSC_API_KEY', None), \
             patch('src.pack_spec.pack_spec.BOSC_AT_USER', None):
            packer._add_score_and_message_commands(
                script_content, "/tmp/score_dir", "test_label",
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_cal_score.assert_called()
        packer.utils.commands_to_send_message.assert_not_called()
        packer.utils.commands_to_send_md_message.assert_not_called()

    def test_with_api_key_sends_score_and_message(self, base_config):
        """测试配置API密钥且非profile模式时，同时计算分数和发送消息"""
        packer = self._create_packer_with_mocks(base_config)
        script_content = []
        with patch('src.pack_spec.pack_spec.BOSC_API_KEY', 'test_key'), \
             patch('src.pack_spec.pack_spec.BOSC_AT_USER', 'test_user'):
            packer._add_score_and_message_commands(
                script_content, "/tmp/score_dir", "test_label",
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_send_message.assert_called()
        packer.utils.commands_to_cal_score.assert_called_with(
            "/tmp/score_dir", packer.test_clock_rate, "score.txt", packer.minimal_mode
        )
        packer.utils.commands_to_send_md_message.assert_called()

    def test_minimal_mode_uses_posix_commands(self, base_config):
        """测试极简模式下，minimal_mode标志传递到commands_to_cal_score且不进入消息分支"""
        packer = self._create_packer_with_mocks(base_config, minimal_mode=True)
        script_content = []
        with patch('src.pack_spec.pack_spec.BOSC_API_KEY', 'test_key'), \
             patch('src.pack_spec.pack_spec.BOSC_AT_USER', 'test_user'):
            packer._add_score_and_message_commands(
                script_content, "/tmp/score_dir", "test_label",
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_cal_score.assert_called_once_with(
            "/tmp/score_dir", packer.test_clock_rate, minimal_mode=True
        )
        packer.utils.commands_to_send_message.assert_not_called()

    def test_name_prefix_in_message(self, base_config):
        """测试name_prefix参数使消息内容包含基准测试名称"""
        packer = self._create_packer_with_mocks(base_config)
        script_content = []
        with patch('src.pack_spec.pack_spec.BOSC_API_KEY', 'test_key'), \
             patch('src.pack_spec.pack_spec.BOSC_AT_USER', 'test_user'):
            packer._add_score_and_message_commands(
                script_content, "/tmp/score_dir", "test_label",
                TuneType.base, InputType.ref, name_prefix="400.perlbench"
            )
        send_msg_call_args = packer.utils.commands_to_send_message.call_args
        message_content = send_msg_call_args[0][0]
        assert "400.perlbench" in message_content


class TestCreateTestScriptDryRun:
    """create_test_script 方法干跑测试"""

    def _create_packer_with_mocks(self, base_config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.get_run_script_name.return_value = "test_ref.sh"
            mock_utils_instance.commands_to_prepare_run.return_value = ["#!/bin/bash", "LOG_FILE=test.log", "CORE_NUM=-1", "TEST_TIMES=3"]
            mock_utils_instance.commands_to_cal_score.return_value = ["python3 cal_score.py 1.0"]
            mock_utils_instance.commands_to_send_message.return_value = ["curl message"]
            mock_utils_instance.commands_to_send_md_message.return_value = ["curl md message"]
            mock_utils_instance.copy_script_file_to_target_dir.return_value = True
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_bench_map = {"400.perlbench": "perlbench"}
            mock_driver_instance.get_ref_time.return_value = "100.0"
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(base_config)
        return packer

    def test_script_contains_shebang(self, base_config):
        """测试脚本内容包含shebang行"""
        packer = self._create_packer_with_mocks(base_config)
        captured_content = []
        with patch.object(packer, '_write_script_file', side_effect=lambda path, content: captured_content.extend(content)):
            packer.create_test_script(
                "test_label", "400.perlbench", -1, "/tmp/dest",
                TuneType.base, InputType.ref
            )
        assert captured_content[0] == "#!/bin/bash"

    def test_script_contains_prepare_commands(self, base_config):
        """测试commands_to_prepare_run使用正确参数调用"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, '_write_script_file'):
            packer.create_test_script(
                "test_label", "400.perlbench", -1, "/tmp/dest",
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_prepare_run.assert_called_once()
        call_args = packer.utils.commands_to_prepare_run.call_args
        assert "ref" in call_args[0][0]
        assert call_args[0][1] == -1
        assert call_args[0][2] == packer.iterations
        assert call_args[0][3] == packer.minimal_mode

    def test_script_contains_run_bench_commands(self, base_config):
        """测试commands_to_run_bench使用正确参数调用"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, '_write_script_file'):
            packer.create_test_script(
                "test_label", "400.perlbench", -1, "/tmp/dest",
                TuneType.base, InputType.ref
            )
        packer.spec_driver.utils.commands_to_run_bench.assert_called_once_with(
            "400.perlbench", packer.profile_gen,
            packer.spec_driver.spec_bench_map,
            -1, "100.0",
            TuneType.base, "test_label", InputType.ref, packer.minimal_mode
        )

    def test_script_contains_score_commands(self, base_config):
        """测试调用_add_score_and_message_commands添加分数计算命令"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, '_write_script_file'), \
             patch.object(packer, '_add_score_and_message_commands') as mock_add:
            packer.create_test_script(
                "test_label", "400.perlbench", -1, "/tmp/dest",
                TuneType.base, InputType.ref
            )
        mock_add.assert_called_once()
        call_kwargs = mock_add.call_args
        assert call_kwargs[1].get("name_prefix") == "400.perlbench" or \
               (len(call_kwargs[0]) > 4 and "400.perlbench" in str(call_kwargs))

    def test_profile_gen_adds_merge_profile(self, base_config):
        """测试profile_gen模式下调用use_template_to_create_script生成merge_profile脚本"""
        packer = self._create_packer_with_mocks(base_config)
        packer.profile_gen = True
        with patch.object(packer, '_write_script_file'):
            packer.create_test_script(
                "test_label", "400.perlbench", -1, "/tmp/dest",
                TuneType.base, InputType.ref
            )
        packer.utils.use_template_to_create_script.assert_called_once()
        template_arg = packer.utils.use_template_to_create_script.call_args[0][0]
        assert template_arg == "merge_profile.sh.template"


class TestCreateRunAllScriptDryRun:
    """create_run_all_script 方法干跑测试"""

    def _create_packer_with_mocks(self, base_config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.get_run_script_name.return_value = "test_ref_all.sh"
            mock_utils_instance.commands_to_prepare_run.return_value = ["#!/bin/bash", "LOG_FILE=run_all.log"]
            mock_utils_instance.commands_to_cal_score.return_value = ["python3 cal_score.py"]
            mock_utils_instance.commands_to_send_message.return_value = ["curl message"]
            mock_utils_instance.commands_to_send_md_message.return_value = ["curl md message"]
            mock_utils_instance.commands_to_collect_profiles.return_value = ["./collect_profiles.sh"]
            mock_utils_instance.copy_script_file_to_target_dir.return_value = True
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_bench_map = {"400.perlbench": "perlbench", "401.bzip2": "bzip2"}
            mock_driver_instance.get_ref_time.return_value = "100.0"
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(base_config)
        return packer

    def test_script_contains_cd_commands(self, base_config):
        """测试脚本内容包含cd进入各基准测试目录的命令"""
        packer = self._create_packer_with_mocks(base_config)
        captured_content = []
        with patch.object(packer, '_write_script_file', side_effect=lambda path, content: captured_content.extend(content)):
            packer.create_run_all_script(
                "test_label", -1,
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                TuneType.base, InputType.ref
            )
        assert "cd 400.perlbench" in captured_content
        assert "cd 401.bzip2" in captured_content

    def test_script_contains_run_bench_for_each(self, base_config):
        """测试对每个基准测试调用commands_to_run_bench"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, '_write_script_file'):
            packer.create_run_all_script(
                "test_label", -1,
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                TuneType.base, InputType.ref
            )
        assert packer.spec_driver.utils.commands_to_run_bench.call_count == 2

    def test_script_contains_cd_back(self, base_config):
        """测试脚本内容包含cd $SCRIPT_DIR返回脚本目录的命令"""
        packer = self._create_packer_with_mocks(base_config)
        captured_content = []
        with patch.object(packer, '_write_script_file', side_effect=lambda path, content: captured_content.extend(content)):
            packer.create_run_all_script(
                "test_label", -1,
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                TuneType.base, InputType.ref
            )
        cd_back_count = captured_content.count("cd $SCRIPT_DIR")
        assert cd_back_count == 2

    def test_script_contains_completion_message(self, base_config):
        """测试脚本内容包含所有基准测试完成的消息"""
        packer = self._create_packer_with_mocks(base_config)
        captured_content = []
        with patch.object(packer, '_write_script_file', side_effect=lambda path, content: captured_content.extend(content)):
            packer.create_run_all_script(
                "test_label", -1,
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                TuneType.base, InputType.ref
            )
        completion_lines = [line for line in captured_content if "All benchmarks completed" in line]
        assert len(completion_lines) >= 1

    def test_profile_gen_adds_collect_profiles(self, base_config):
        """测试profile_gen模式下调用commands_to_collect_profiles"""
        packer = self._create_packer_with_mocks(base_config)
        packer.profile_gen = True
        with patch.object(packer, '_write_script_file'):
            packer.create_run_all_script(
                "test_label", -1,
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                TuneType.base, InputType.ref
            )
        packer.utils.commands_to_collect_profiles.assert_called_once()


class TestCreateSpecdiffAllScriptDryRun:
    """create_specdiff_all_script 方法干跑测试"""

    def _create_packer_with_mocks(self, base_config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_cls.return_value = mock_utils_instance
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(base_config)
        return packer

    def test_script_path_and_commands(self, base_config):
        """测试生成脚本路径和核心命令"""
        packer = self._create_packer_with_mocks(base_config)
        captured = {}
        with patch.object(packer, '_write_script_file', side_effect=lambda path, content: captured.update({"path": path, "content": content})):
            packer.create_specdiff_all_script(
                ["/tmp/run/400.perlbench", "/tmp/run/401.bzip2"],
                InputType.ref
            )

        assert captured["path"] == "/tmp/run/specdiff_ref_all.sh"
        content = "\n".join(captured["content"])
        assert "LOG_FILE=\"$SCRIPT_DIR/specdiff_ref_all.log\"" in content
        assert "if [ ! -f \"$SCRIPT_DIR/400.perlbench/specdiff_ref.sh\" ]; then" in content
        assert "cd \"$SCRIPT_DIR/401.bzip2\"" in content
        assert "bash ./specdiff_ref.sh >> \"$LOG_FILE\" 2>&1" in content
        assert "Failed benchmarks:$FAILED_BENCHES" in content
        assert "exit 1" in content

    def test_empty_bench_list_does_not_write_script(self, base_config):
        """测试空基准测试列表不生成脚本"""
        packer = self._create_packer_with_mocks(base_config)
        with patch.object(packer, '_write_script_file') as mock_write:
            packer.create_specdiff_all_script([], InputType.ref)
        mock_write.assert_not_called()


class TestProcessTuneInputCombinations:
    """_process_tune_input_combinations 方法测试"""

    def _create_packer_with_tune_input(self, tune_type, input_type, base_config):
        config = base_config.copy()
        config["spec_config"] = base_config["spec_config"].copy()
        config["spec_config"]["tune_type"] = tune_type
        config["spec_config"]["input_type"] = input_type
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_cls.return_value = mock_utils_instance
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
        return packer

    def test_single_combination(self, base_config):
        """测试tune_type和input_type均为非all时，func只调用1次"""
        packer = self._create_packer_with_tune_input(TuneType.base, InputType.ref, base_config)
        mock_func = MagicMock()
        packer._process_tune_input_combinations(mock_func)
        assert mock_func.call_count == 1

    def test_tune_all_expands_to_base_peak(self, base_config):
        """测试tune_type=all时展开为base和peak，func调用2次"""
        packer = self._create_packer_with_tune_input(TuneType.all, InputType.ref, base_config)
        mock_func = MagicMock()
        packer._process_tune_input_combinations(mock_func)
        assert mock_func.call_count == 2
        called_tune_types = [c[1].get('tune_type', c[0][0] if len(c[0]) > 0 else None) for c in mock_func.call_args_list]
        assert TuneType.base in called_tune_types
        assert TuneType.peak in called_tune_types

    def test_input_all_expands_to_test_train_ref(self, base_config):
        """测试input_type=all时展开为test、train和ref，func调用3次"""
        packer = self._create_packer_with_tune_input(TuneType.base, InputType.all, base_config)
        mock_func = MagicMock()
        packer._process_tune_input_combinations(mock_func)
        assert mock_func.call_count == 3
        called_input_types = [c[1].get('input_type') for c in mock_func.call_args_list]
        assert InputType.test in called_input_types
        assert InputType.train in called_input_types
        assert InputType.ref in called_input_types

    def test_both_all_expands_to_six(self, base_config):
        """测试tune_type=all且input_type=all时展开为6种组合，func调用6次"""
        packer = self._create_packer_with_tune_input(TuneType.all, InputType.all, base_config)
        mock_func = MagicMock()
        packer._process_tune_input_combinations(mock_func)
        assert mock_func.call_count == 6


class TestRunDirectMode:
    """run() 方法的RunMode.direct模式测试"""

    def _create_packer_with_mocks(self, config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_cls.return_value = MagicMock()
            mock_utils_cls.return_value.create_generated_dir.return_value = "/tmp/test"
            mock_utils_cls.return_value.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_cls.return_value.save_pack_spec_cfg = MagicMock()
            mock_create.return_value = MagicMock()
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
        return packer

    def test_direct_mode_calls_run_spec(self, base_config):
        """测试RunMode.direct模式下调用run_spec而非打包方法"""
        base_config["task"]["run_mode"] = RunMode.direct
        packer = self._create_packer_with_mocks(base_config)
        packer.run_spec = MagicMock()
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()
        result = packer.run()
        packer.run_spec.assert_called_once()
        packer.setup_spec.assert_not_called()
        packer.pack_binaries.assert_not_called()
        packer.pack_benches_cfg.assert_not_called()
        packer.pack_qemu_verify.assert_not_called()
        assert "run_spec" in result["steps"]

    def test_pack_mode_does_not_call_run_spec(self, base_config):
        """测试RunMode.pack模式下不调用run_spec"""
        base_config["task"]["run_mode"] = RunMode.pack
        packer = self._create_packer_with_mocks(base_config)
        packer.run_spec = MagicMock()
        packer.setup_spec = MagicMock()
        packer.pack_binaries = MagicMock()
        packer.pack_benches_cfg = MagicMock()
        packer.pack_qemu_verify = MagicMock()
        packer.run()
        packer.run_spec.assert_not_called()


class TestCopyBinariesDryRun:
    """copy_binaries 方法干跑测试"""

    def _create_packer_with_mocks(self, base_config):
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.create_dest_dir.return_value = "/tmp/dest_bin"
            mock_utils_instance.copy_file_to_target_dir.return_value = True
            mock_utils_instance.copy_spec_cfg_and_logs_to_target_dir = MagicMock()
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.get_binary_path_map.return_value = {
                "400.perlbench": "/path/bin1",
                "401.bzip2": "/path/bin2"
            }
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_dir = "/spec_dir"
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(base_config)
        return packer

    def test_dest_dir_uses_bin_mode(self, base_config):
        """测试目标目录使用PACKMode.bin模式创建"""
        packer = self._create_packer_with_mocks(base_config)
        packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)
        packer.utils.create_dest_dir.assert_called_once_with(
            packer.profile_gen, packer.auto_mode, PACKMode.bin,
            packer.spec_name, TuneType.base, InputType.ref, SPECMode.speed
        )

    def test_copy_count_matches_bench_count(self, base_config):
        """测试复制二进制文件的次数与基准测试数量一致"""
        packer = self._create_packer_with_mocks(base_config)
        packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)
        assert packer.utils.copy_file_to_target_dir.call_count == 2

    def test_copy_spec_cfg_called(self, base_config):
        """测试复制二进制文件后调用copy_spec_cfg_and_logs_to_target_dir"""
        packer = self._create_packer_with_mocks(base_config)
        packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)
        packer.utils.copy_spec_cfg_and_logs_to_target_dir.assert_called_once()

    def test_no_binaries_raises_error(self, base_config):
        """测试没有二进制文件时抛出FileOperationError异常"""
        from src.pack_spec.pack_config import FileOperationError
        packer = self._create_packer_with_mocks(base_config)
        packer.spec_driver.get_binary_path_map.return_value = {}
        with pytest.raises(FileOperationError):
            packer.copy_binaries(TuneType.base, InputType.ref, SPECMode.speed)


class TestPackQemuVerifyDryRun:
    """pack_qemu_verify 方法干跑测试"""

    def _create_packer_with_mocks(self, base_config, verify_mode=True):
        config = base_config.copy()
        config["pack_config"] = base_config["pack_config"].copy()
        config["pack_config"]["verify_mode"] = verify_mode
        with patch('src.pack_spec.pack_spec.PackUtils') as mock_utils_cls, \
             patch('src.pack_spec.pack_spec.SPECDriver.create') as mock_create, \
             patch('src.pack_spec.pack_spec.setup_logger') as mock_setup_logger:
            mock_utils_instance = MagicMock()
            mock_utils_instance.create_generated_dir.return_value = "/tmp/test"
            mock_utils_instance.get_pack_generated_dir_path.return_value = "/tmp/test"
            mock_utils_instance.save_pack_spec_cfg = MagicMock()
            mock_utils_instance.get_dest_dir.return_value = "/tmp/packed/run_dir"
            mock_utils_instance.copy_spec_cfg_and_logs_to_target_dir = MagicMock()
            mock_utils_cls.return_value = mock_utils_instance
            mock_driver_instance = MagicMock()
            mock_driver_instance.label = "test_label"
            mock_driver_instance.spec_bench_map = {"400.perlbench": "perlbench", "401.bzip2": "bzip2"}
            mock_driver_instance.spec_bench_list = ["400.perlbench", "401.bzip2"]
            mock_driver_instance.spec_dir = "/spec_dir"
            mock_create.return_value = mock_driver_instance
            mock_setup_logger.return_value = "/tmp/test/log/test.log"
            packer = PackSPEC(config)
        return packer

    def test_qemu_path_none_raises_config_error(self, base_config):
        """测试QEMU_PATH为None时抛出ConfigError异常"""
        packer = self._create_packer_with_mocks(base_config)
        with patch('src.pack_spec.pack_spec.QEMU_PATH', None):
            with pytest.raises(ConfigError):
                packer.pack_qemu_verify()

    def test_verify_mode_false_raises_config_error(self, base_config):
        """测试verify_mode为False时抛出ConfigError异常"""
        packer = self._create_packer_with_mocks(base_config, verify_mode=False)
        with patch('src.pack_spec.pack_spec.QEMU_PATH', "/fake/qemu"):
            with pytest.raises(ConfigError):
                packer.pack_qemu_verify()

    def test_output_dir_has_qemu_verify_suffix(self, base_config):
        """测试输出目录路径包含_qemu_verify后缀"""
        packer = self._create_packer_with_mocks(base_config)
        with patch('src.pack_spec.pack_spec.QEMU_PATH', "/fake/qemu"), \
             patch('src.pack_spec.pack_spec.os.path.isdir', return_value=True), \
             patch('src.pack_spec.pack_spec.os.path.exists', side_effect=lambda p: False if "_qemu_verify" in p else True), \
             patch('src.pack_spec.pack_spec.os.makedirs'), \
             patch('src.pack_spec.pack_spec.shutil.copytree'), \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_script', return_value="/tmp/verify.sh"), \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_all_script', return_value="/tmp/verify_all.sh"):
            result = packer.pack_qemu_verify()
        assert "_qemu_verify" in result["output_dir"]

    def test_generates_verify_script_for_each_bench(self, base_config):
        """测试为每个基准测试生成QEMU验证脚本"""
        packer = self._create_packer_with_mocks(base_config)
        with patch('src.pack_spec.pack_spec.QEMU_PATH', "/fake/qemu"), \
             patch('src.pack_spec.pack_spec.os.path.isdir', return_value=True), \
             patch('src.pack_spec.pack_spec.os.path.exists', side_effect=lambda p: False if "_qemu_verify" in p else True), \
             patch('src.pack_spec.pack_spec.os.makedirs'), \
             patch('src.pack_spec.pack_spec.shutil.copytree'), \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_script', return_value="/tmp/verify.sh") as mock_gen, \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_all_script', return_value="/tmp/verify_all.sh"):
            packer.pack_qemu_verify()
        assert mock_gen.call_count == 2

    def test_generates_batch_verify_script(self, base_config):
        """测试生成批量验证脚本"""
        packer = self._create_packer_with_mocks(base_config)
        with patch('src.pack_spec.pack_spec.QEMU_PATH', "/fake/qemu"), \
             patch('src.pack_spec.pack_spec.os.path.isdir', return_value=True), \
             patch('src.pack_spec.pack_spec.os.path.exists', side_effect=lambda p: False if "_qemu_verify" in p else True), \
             patch('src.pack_spec.pack_spec.os.makedirs'), \
             patch('src.pack_spec.pack_spec.shutil.copytree'), \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_script', return_value="/tmp/verify.sh"), \
             patch('src.pack_spec.pack_spec.generate_qemu_verify_all_script', return_value="/tmp/verify_all.sh") as mock_batch:
            packer.pack_qemu_verify()
        mock_batch.assert_called_once()
