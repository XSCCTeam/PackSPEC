"""
pack_config.py 单元测试

测试枚举类型、异常类、环境变量加载和默认值配置
"""

import os
import pytest
from unittest.mock import patch

from src.pack_spec.pack_config import (
    ActionType, TuneType, InputType, SPECName, SPECSubBench,
    SPECMode, PACKMode, RunMode,
    PackSPECError, ConfigError, FileOperationError,
    CommandExecutionError, BenchmarkError,
    DEFAULT_CORE_NUM, DEFAULT_ITERATIONS, DEFAULT_CLOCK_RATE,
    DEFAULT_REBUILD, DEFAULT_PROFILE_GEN, DEFAULT_AUTO_MODE,
    DEFAULT_VERIFY_MODE, DEFAULT_MINIMAL_MODE, DEFAULT_RUN_MODE,
    DEFAULT_REPORT_FORMAT, RANDOM_SUFFIX_LENGTH,
    P_PATH, SCRIPTS_PATH, GENERATED_FILES_PATH,
)


class TestActionType:
    """ActionType 枚举测试"""

    def test_build_value(self):
        assert ActionType.build.value == 1

    def test_run_value(self):
        assert ActionType.run.value == 2

    def test_enum_count(self):
        assert len(ActionType) == 2


class TestTuneType:
    """TuneType 枚举测试"""

    def test_base_value(self):
        assert TuneType.base.value == 1

    def test_peak_value(self):
        assert TuneType.peak.value == 2

    def test_all_value(self):
        assert TuneType.all.value == 3

    def test_enum_count(self):
        assert len(TuneType) == 3

    def test_name_access(self):
        assert TuneType.base.name == "base"
        assert TuneType.peak.name == "peak"


class TestInputType:
    """InputType 枚举测试"""

    def test_test_value(self):
        assert InputType.test.value == 1

    def test_train_value(self):
        assert InputType.train.value == 2

    def test_ref_value(self):
        assert InputType.ref.value == 3

    def test_all_value(self):
        assert InputType.all.value == 4

    def test_enum_count(self):
        assert len(InputType) == 4


class TestSPECName:
    """SPECName 枚举测试"""

    def test_spec2006_value(self):
        assert SPECName.spec2006.value == 1

    def test_spec2006v1p01_value(self):
        assert SPECName.spec2006v1p01.value == 2

    def test_spec2017_value(self):
        assert SPECName.spec2017.value == 3

    def test_enum_count(self):
        assert len(SPECName) == 3


class TestSPECMode:
    """SPECMode 枚举测试"""

    def test_speed_value(self):
        assert SPECMode.speed.value == 1

    def test_rate_value(self):
        assert SPECMode.rate.value == 2

    def test_enum_count(self):
        assert len(SPECMode) == 2


class TestPACKMode:
    """PACKMode 枚举测试"""

    def test_bin_value(self):
        assert PACKMode.bin.value == 1

    def test_run_value(self):
        assert PACKMode.run.value == 2

    def test_buildrun_value(self):
        assert PACKMode.buildrun.value == 3


class TestRunMode:
    """RunMode 枚举测试"""

    def test_pack_value(self):
        assert RunMode.pack.value == 1

    def test_direct_value(self):
        assert RunMode.direct.value == 2


class TestExceptions:
    """异常类测试"""

    def test_packspec_error(self):
        with pytest.raises(PackSPECError) as exc_info:
            raise PackSPECError("test error")
        assert str(exc_info.value) == "test error"
        assert exc_info.value.code == 1

    def test_packspec_error_custom_code(self):
        with pytest.raises(PackSPECError) as exc_info:
            raise PackSPECError("test error", code=42)
        assert exc_info.value.code == 42

    def test_config_error_inherits(self):
        with pytest.raises(PackSPECError):
            raise ConfigError("config error")

    def test_file_operation_error_inherits(self):
        with pytest.raises(PackSPECError):
            raise FileOperationError("file error")

    def test_command_execution_error_inherits(self):
        with pytest.raises(PackSPECError):
            raise CommandExecutionError("command error")

    def test_benchmark_error_inherits(self):
        with pytest.raises(PackSPECError):
            raise BenchmarkError("benchmark error")

    def test_config_error_is_instance(self):
        err = ConfigError("test")
        assert isinstance(err, PackSPECError)
        assert isinstance(err, ConfigError)

    def test_file_operation_error_is_instance(self):
        err = FileOperationError("test")
        assert isinstance(err, PackSPECError)
        assert isinstance(err, FileOperationError)


class TestDefaultValues:
    """默认值配置测试"""

    def test_default_core_num(self):
        assert DEFAULT_CORE_NUM == -1

    def test_default_iterations(self):
        assert DEFAULT_ITERATIONS == 3

    def test_default_clock_rate(self):
        assert DEFAULT_CLOCK_RATE == 1.0

    def test_default_rebuild(self):
        assert DEFAULT_REBUILD is True

    def test_default_profile_gen(self):
        assert DEFAULT_PROFILE_GEN is False

    def test_default_auto_mode(self):
        assert DEFAULT_AUTO_MODE is False

    def test_default_verify_mode(self):
        assert DEFAULT_VERIFY_MODE is False

    def test_default_minimal_mode(self):
        assert DEFAULT_MINIMAL_MODE is False

    def test_default_run_mode(self):
        assert DEFAULT_RUN_MODE == RunMode.pack

    def test_default_report_format(self):
        assert DEFAULT_REPORT_FORMAT == "json"

    def test_random_suffix_length(self):
        assert RANDOM_SUFFIX_LENGTH == 4


class TestPathConfig:
    """路径配置测试"""

    def test_p_path_exists(self):
        assert os.path.isdir(P_PATH)

    def test_scripts_path_exists(self):
        assert os.path.isdir(SCRIPTS_PATH)

    def test_generated_files_path_format(self):
        assert GENERATED_FILES_PATH.endswith("generated_files")

    def test_p_path_is_project_root(self):
        assert os.path.exists(os.path.join(P_PATH, "pyproject.toml"))


class TestEnvLoading:
    """环境变量加载测试"""

    def test_qemu_cmd_default(self):
        from src.pack_spec.pack_config import QEMU_CMD
        assert QEMU_CMD is not None

    def test_spec2006_path_type(self):
        from src.pack_spec.pack_config import SPEC2006_PATH
        assert SPEC2006_PATH is None or isinstance(SPEC2006_PATH, str)

    def test_spec2017_path_type(self):
        from src.pack_spec.pack_config import SPEC2017_PATH
        assert SPEC2017_PATH is None or isinstance(SPEC2017_PATH, str)

    def test_qemu_path_type(self):
        from src.pack_spec.pack_config import QEMU_PATH
        assert QEMU_PATH is None or isinstance(QEMU_PATH, str)
