"""
pack_spec.py 单元测试

测试 PackSPEC 类初始化、配置解析、run() 方法等
"""

import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode, DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_PROFILE_GEN, DEFAULT_VERIFY_MODE, DEFAULT_MINIMAL_MODE, DEFAULT_RUN_MODE,
    DEFAULT_REPORT_FORMAT,
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
