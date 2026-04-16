"""
pack_utils.py 单元测试

测试工具函数、枚举序列化/反序列化、文件操作、脚本生成等
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, PACKMode,
    PackSPECError, FileOperationError, CommandExecutionError,
    SCRIPTS_PATH,
)
from src.pack_spec.pack_utils import (
    is_numeric, EnumEncoder, EnumDecoder,
    str_to_enum, convert_dict_enums,
    save_pack_spec_cfg, load_pack_spec_cfg,
    PackUtils, build_qemu_command,
    generate_json_report, generate_markdown_report,
    parse_spec_results, calculate_spec_score,
    generate_qemu_verify_script, generate_qemu_verify_all_script,
)


class TestIsNumeric:
    """is_numeric 函数测试"""

    def test_integer_string(self):
        assert is_numeric("123") is True

    def test_float_string(self):
        assert is_numeric("123.45") is True

    def test_negative_number(self):
        assert is_numeric("-42.5") is True

    def test_scientific_notation(self):
        assert is_numeric("1e10") is True

    def test_non_numeric(self):
        assert is_numeric("abc") is False

    def test_empty_string(self):
        assert is_numeric("") is False

    def test_none_value(self):
        assert is_numeric(None) is False

    def test_mixed_string(self):
        assert is_numeric("12abc") is False


class TestEnumEncoder:
    """EnumEncoder 测试"""

    def test_encode_tune_type(self):
        data = {"tune_type": TuneType.base}
        result = json.dumps(data, cls=EnumEncoder)
        assert '"tune_type": "base"' in result

    def test_encode_spec_name(self):
        data = {"spec_name": SPECName.spec2017}
        result = json.dumps(data, cls=EnumEncoder)
        assert '"spec_name": "spec2017"' in result

    def test_encode_input_type(self):
        data = {"input_type": InputType.ref}
        result = json.dumps(data, cls=EnumEncoder)
        assert '"input_type": "ref"' in result

    def test_encode_spec_mode(self):
        data = {"spec_mode": SPECMode.speed}
        result = json.dumps(data, cls=EnumEncoder)
        assert '"spec_mode": "speed"' in result

    def test_encode_mixed_types(self):
        data = {"spec_name": SPECName.spec2006, "iterations": 3, "name": "test"}
        result = json.dumps(data, cls=EnumEncoder)
        parsed = json.loads(result)
        assert parsed["spec_name"] == "spec2006"
        assert parsed["iterations"] == 3
        assert parsed["name"] == "test"

    def test_encode_nested_dict(self):
        data = {"spec_config": {"tune_type": TuneType.peak}}
        result = json.dumps(data, cls=EnumEncoder)
        parsed = json.loads(result)
        assert parsed["spec_config"]["tune_type"] == "peak"


class TestEnumDecoder:
    """EnumDecoder 测试"""

    def test_decode_tune_type(self):
        json_str = '{"tune_type": "base"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["tune_type"] == TuneType.base

    def test_decode_spec_name(self):
        json_str = '{"spec_name": "spec2017"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["spec_name"] == SPECName.spec2017

    def test_decode_input_type(self):
        json_str = '{"input_type": "ref"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["input_type"] == InputType.ref

    def test_decode_spec_mode(self):
        json_str = '{"spec_mode": "speed"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["spec_mode"] == SPECMode.speed

    def test_decode_non_enum_field(self):
        json_str = '{"iterations": 3, "name": "test"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["iterations"] == 3
        assert data["name"] == "test"

    def test_decode_nested_dict(self):
        json_str = '{"spec_config": {"tune_type": "peak"}}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["spec_config"]["tune_type"] == TuneType.peak

    def test_decode_invalid_enum_value(self):
        json_str = '{"tune_type": "invalid_value"}'
        data = json.loads(json_str, cls=EnumDecoder)
        assert data["tune_type"] == "invalid_value"

    def test_roundtrip_encode_decode(self):
        original = {
            "spec_name": SPECName.spec2006,
            "tune_type": TuneType.base,
            "input_type": InputType.ref,
            "spec_mode": SPECMode.speed,
            "iterations": 3,
        }
        json_str = json.dumps(original, cls=EnumEncoder)
        decoded = json.loads(json_str, cls=EnumDecoder)
        assert decoded["spec_name"] == original["spec_name"]
        assert decoded["tune_type"] == original["tune_type"]
        assert decoded["input_type"] == original["input_type"]
        assert decoded["spec_mode"] == original["spec_mode"]
        assert decoded["iterations"] == original["iterations"]


class TestStrToEnum:
    """str_to_enum 函数测试"""

    def test_valid_tune_type(self):
        assert str_to_enum("base", TuneType) == TuneType.base

    def test_valid_spec_name(self):
        assert str_to_enum("spec2017", SPECName) == SPECName.spec2017

    def test_invalid_value(self):
        result = str_to_enum("invalid", TuneType)
        assert result == "invalid"

    def test_none_enum_class(self):
        with pytest.raises(TypeError):
            str_to_enum("base", None)


class TestConvertDictEnums:
    """convert_dict_enums 函数测试"""

    def test_convert_single_field(self):
        data = {"tune_type": "base"}
        enum_fields = {"tune_type": TuneType}
        result = convert_dict_enums(data, enum_fields)
        assert result["tune_type"] == TuneType.base

    def test_convert_multiple_fields(self):
        data = {"tune_type": "peak", "spec_name": "spec2006", "name": "test"}
        enum_fields = {"tune_type": TuneType, "spec_name": SPECName}
        result = convert_dict_enums(data, enum_fields)
        assert result["tune_type"] == TuneType.peak
        assert result["spec_name"] == SPECName.spec2006
        assert result["name"] == "test"

    def test_skip_non_string_values(self):
        data = {"tune_type": TuneType.base, "iterations": 3}
        enum_fields = {"tune_type": TuneType}
        result = convert_dict_enums(data, enum_fields)
        assert result["tune_type"] == TuneType.base
        assert result["iterations"] == 3


class TestSaveLoadPackSpecCfg:
    """save_pack_spec_cfg / load_pack_spec_cfg 函数测试"""

    def test_save_and_load(self, temp_dir):
        config = {
            "spec_name": SPECName.spec2006,
            "tune_type": TuneType.base,
            "input_type": InputType.ref,
            "spec_mode": SPECMode.speed,
            "iterations": 3,
        }
        cfg_path = save_pack_spec_cfg(config, temp_dir)
        assert os.path.exists(cfg_path)

        loaded = load_pack_spec_cfg(cfg_path)
        assert loaded["spec_name"] == SPECName.spec2006
        assert loaded["tune_type"] == TuneType.base
        assert loaded["input_type"] == InputType.ref
        assert loaded["spec_mode"] == SPECMode.speed
        assert loaded["iterations"] == 3

    def test_save_creates_file(self, temp_dir):
        config = {"name": "test"}
        cfg_path = save_pack_spec_cfg(config, temp_dir)
        assert os.path.exists(cfg_path)
        assert cfg_path.endswith("pack_spec.cfg")


class TestPackUtils:
    """PackUtils 类测试"""

    def test_init_with_task_config(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        assert utils.pack_name == "test_pack"

    def test_init_with_old_config(self):
        config = {"pack_name": "old_pack"}
        utils = PackUtils(config, MagicMock())
        assert utils.pack_name == "old_pack"

    def test_init_default_pack_name(self):
        config = {}
        utils = PackUtils(config, MagicMock())
        assert utils.pack_name == "packspec"

    def test_get_dest_dir_bin_mode(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        dest_dir = utils.get_dest_dir(
            False, True, PACKMode.bin,
            SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed
        )
        assert "bin" in dest_dir
        assert "spec2006" in dest_dir
        assert "base_test_speed" in dest_dir

    def test_get_dest_dir_run_mode(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        dest_dir = utils.get_dest_dir(
            False, True, PACKMode.run,
            SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed
        )
        assert "run" in dest_dir
        assert "spec2006" in dest_dir

    def test_get_dest_dir_profile_gen(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        dest_dir = utils.get_dest_dir(
            True, True, PACKMode.run,
            SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed
        )
        assert "profilegen" in dest_dir

    def test_get_run_script_name_normal(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        name = utils.get_run_script_name(False, InputType.ref)
        assert name == "test_ref.sh"

    def test_get_run_script_name_profile(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        name = utils.get_run_script_name(True, InputType.ref)
        assert name == "profile_gen_ref.sh"

    def test_get_run_script_name_with_suffix(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        name = utils.get_run_script_name(False, InputType.test, "verify")
        assert name == "test_test_verify.sh"

    def test_get_pack_generated_dir_path(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_dir_path()
        assert "test_pack" in path

    def test_get_pack_generated_dir_path_auto_mode_true(self, base_config):
        base_config["pack_config"]["auto_mode"] = True
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_dir_path()
        assert path.endswith("test_pack")
        assert "_" not in os.path.basename(path) or "test_pack" in os.path.basename(path)

    def test_get_pack_generated_dir_path_auto_mode_false(self, base_config):
        base_config["pack_config"]["auto_mode"] = False
        base_config["date"] = "260408"
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_dir_path()
        assert path.endswith("260408_test_pack")
        assert "260408" in path

    def test_get_pack_generated_file_path_auto_mode_true(self, base_config):
        base_config["pack_config"]["auto_mode"] = True
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_file_path()
        assert path.endswith("test_pack.json")

    def test_get_pack_generated_file_path_auto_mode_false(self, base_config):
        base_config["pack_config"]["auto_mode"] = False
        base_config["date"] = "260408"
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_file_path()
        assert path.endswith("260408_test_pack.json")

    def test_copy_file_to_target_dir_success(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        src_file = os.path.join(temp_dir, "src.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        with open(src_file, "w") as f:
            f.write("test")
        result = utils.copy_file_to_target_dir(src_file, dest_file, "test file")
        assert result is True
        assert os.path.exists(dest_file)

    def test_copy_file_to_target_dir_fail(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        result = utils.copy_file_to_target_dir("/nonexistent/file", temp_dir, "test file")
        assert result is False

    def test_copy_script_file_to_target_dir_not_found(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with pytest.raises(FileOperationError):
            utils.copy_script_file_to_target_dir("nonexistent_script.sh", temp_dir)

    def test_get_spec_setup_log_path(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_spec_setup_log_path("test.cfg", TuneType.base, InputType.ref)
        assert "test.base_ref.setuplog" in path

    def test_get_bench_dir_found(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        bench_dirs = [
            "/spec/benchspec/CPU2006/400.perlbench/run/00000001",
            "/spec/benchspec/CPU2006/401.bzip2/run/00000001",
        ]
        result = utils.get_bench_dir("400.perlbench", bench_dirs)
        assert "400.perlbench" in result

    def test_get_bench_dir_not_found(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        result = utils.get_bench_dir("999.nonexistent", [])
        assert result == ""

    def test_commands_to_prepare_run_normal(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_prepare_run("test.log", -1, 3)
        assert commands[0] == "#!/bin/bash"
        assert any("test.log" in cmd for cmd in commands)
        assert any("TEST_TIMES=3" in cmd for cmd in commands)

    def test_commands_to_prepare_run_minimal(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_prepare_run("test.log", -1, 3, minimal_mode=True)
        assert commands[0] == "#!/bin/sh"
        assert any("set -e" in cmd for cmd in commands)

    def test_commands_to_prepare_run_with_core_num(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_prepare_run("test.log", 4, 3)
        assert any("CORE_NUM=4" in cmd for cmd in commands)

    def test_commands_to_cal_score_normal(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'copy_script_file_to_target_dir', return_value=True):
            commands = utils.commands_to_cal_score(temp_dir, 1.0)
        assert any("cal_score.py" in cmd for cmd in commands)

    def test_commands_to_cal_score_minimal(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'copy_script_file_to_target_dir', return_value=True):
            commands = utils.commands_to_cal_score(temp_dir, 1.0, minimal_mode=True)
        assert any("cal_score_minimal.sh" in cmd for cmd in commands)

    def test_commands_to_cal_score_with_score_file(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'copy_script_file_to_target_dir', return_value=True):
            commands = utils.commands_to_cal_score(temp_dir, 1.0, score_file="score.csv")
        assert any("tee score.csv" in cmd for cmd in commands)

    def test_create_dest_dir_new(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'get_dest_dir', return_value=os.path.join(temp_dir, "new_dir")):
            result = utils.create_dest_dir(False, True, PACKMode.run,
                                           SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed)
        assert os.path.isdir(result)

    def test_create_dest_dir_auto_mode_overwrite(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        existing_dir = os.path.join(temp_dir, "existing_dir")
        os.makedirs(existing_dir)
        with patch.object(utils, 'get_dest_dir', return_value=existing_dir):
            result = utils.create_dest_dir(False, True, PACKMode.run,
                                           SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed)
        assert os.path.isdir(result)

    def test_create_dest_dir_overwrite_confirmed(self, base_config, temp_dir):
        """测试 overwrite_confirmed=True 时直接覆盖已存在目录，不抛出异常"""
        utils = PackUtils(base_config, MagicMock())
        existing_dir = os.path.join(temp_dir, "existing_dir")
        os.makedirs(existing_dir)
        utils.overwrite_confirmed = True
        with patch.object(utils, 'get_dest_dir', return_value=existing_dir):
            result = utils.create_dest_dir(False, False, PACKMode.run,
                                           SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed)
        assert os.path.isdir(result)

    def test_create_dest_dir_not_auto_mode_raises(self, base_config, temp_dir):
        """测试非自动模式下目录已存在且未设置覆盖确认时抛出PackSPECError"""
        utils = PackUtils(base_config, MagicMock())
        existing_dir = os.path.join(temp_dir, "existing_dir")
        os.makedirs(existing_dir)
        with patch.object(utils, 'get_dest_dir', return_value=existing_dir):
            with pytest.raises(PackSPECError):
                utils.create_dest_dir(False, False, PACKMode.run,
                                      SPECName.spec2006, TuneType.base, InputType.test, SPECMode.speed)

    def test_create_generated_dir_auto_mode_overwrite(self, base_config, temp_dir):
        """测试自动模式下覆盖已存在的生成目录"""
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'get_pack_generated_dir_path', return_value=os.path.join(temp_dir, "gen_dir")):
            os.makedirs(os.path.join(temp_dir, "gen_dir"))
            with patch('src.pack_spec.pack_utils.GENERATED_FILES_PATH', temp_dir):
                result = utils.create_generated_dir(auto_mode=True)
        assert os.path.isdir(result)

    def test_create_generated_dir_overwrite_confirmed(self, base_config, temp_dir):
        """测试 overwrite_confirmed=True 时直接覆盖已存在目录，不抛出异常"""
        utils = PackUtils(base_config, MagicMock())
        gen_dir = os.path.join(temp_dir, "gen_dir")
        os.makedirs(gen_dir)
        utils.overwrite_confirmed = True
        with patch.object(utils, 'get_pack_generated_dir_path', return_value=gen_dir):
            with patch('src.pack_spec.pack_utils.GENERATED_FILES_PATH', temp_dir):
                result = utils.create_generated_dir(auto_mode=False)
        assert os.path.isdir(result)

    def test_create_generated_dir_not_auto_mode_raises(self, base_config, temp_dir):
        """测试非自动模式下目录已存在且未设置覆盖确认时抛出PackSPECError"""
        utils = PackUtils(base_config, MagicMock())
        gen_dir = os.path.join(temp_dir, "gen_dir")
        os.makedirs(gen_dir)
        with patch.object(utils, 'get_pack_generated_dir_path', return_value=gen_dir):
            with patch('src.pack_spec.pack_utils.GENERATED_FILES_PATH', temp_dir):
                with pytest.raises(PackSPECError):
                    utils.create_generated_dir(auto_mode=False)


class TestBuildQemuCommand:
    """build_qemu_command 函数测试"""

    def test_build_qemu_command_basic(self):
        spec_bench_map = {"400.perlbench": "perlbench"}
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            commands = build_qemu_command(
                InputType.test, "400.perlbench", spec_bench_map,
                TuneType.base, "test_label"
            )
        assert any("QEMU_CMD" in cmd for cmd in commands)
        assert any("perlbench" in cmd for cmd in commands)

    def test_build_qemu_command_empty_raises(self):
        with patch('src.pack_spec.pack_utils.QEMU_CMD', ''):
            with pytest.raises(Exception):
                build_qemu_command(
                    InputType.test, "400.perlbench", {},
                    TuneType.base, "test_label"
                )

    def test_build_qemu_command_with_args(self):
        spec_bench_map = {"400.perlbench": "perlbench"}
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-riscv64 -s 83886080000'):
            commands = build_qemu_command(
                InputType.test, "400.perlbench", spec_bench_map,
                TuneType.base, "test_label"
            )
        assert any("qemu-riscv64" in cmd for cmd in commands)


class TestReportGeneration:
    """报告生成函数测试"""

    def test_generate_json_report(self, temp_dir):
        results = {
            "benchmarks": {
                "400.perlbench": {"runtime": 100.0, "score": 5.0},
            },
            "int_score": 5.0,
            "fp_score": 0.0,
        }
        config = {
            "spec_config": {
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.ref,
                "spec_mode": SPECMode.speed,
                "iterations": 3,
            }
        }
        output_path = os.path.join(temp_dir, "report.json")
        result = generate_json_report(results, config, output_path)
        assert os.path.exists(result)
        with open(result) as f:
            report = json.load(f)
        assert "report_info" in report
        assert "config" in report
        assert "results" in report
        assert report["results"]["int_score"] == 5.0

    def test_generate_markdown_report(self, temp_dir):
        results = {
            "benchmarks": {
                "400.perlbench": {"runtime": 100.0, "score": 5.0},
            },
            "int_score": 5.0,
            "fp_score": 0.0,
        }
        config = {
            "spec_config": {
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.base,
                "input_type": InputType.ref,
                "spec_mode": SPECMode.speed,
                "iterations": 3,
            }
        }
        output_path = os.path.join(temp_dir, "report.md")
        result = generate_markdown_report(results, config, output_path)
        assert os.path.exists(result)
        with open(result) as f:
            content = f.read()
        assert "SPEC CPU" in content
        assert "5.00" in content


class TestCommandsToRunBench:
    """commands_to_run_bench 函数测试"""

    def test_normal_mode(self, base_config, spec_bench_map):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_run_bench(
            "400.perlbench", False, spec_bench_map,
            -1, 100.0, TuneType.base, "test_label", InputType.test
        )
        assert any("perlbench" in cmd for cmd in commands)
        assert any("run_test.sh" in cmd for cmd in commands)
        assert any("bash run_test.sh" in cmd for cmd in commands)

    def test_minimal_mode(self, base_config, spec_bench_map):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_run_bench(
            "400.perlbench", False, spec_bench_map,
            -1, 100.0, TuneType.base, "test_label", InputType.test,
            minimal_mode=True
        )
        assert any("perlbench" in cmd for cmd in commands)
        assert any("./run_test.sh" in cmd for cmd in commands)
        assert any("while" in cmd for cmd in commands)

    def test_with_core_num(self, base_config, spec_bench_map):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_run_bench(
            "400.perlbench", False, spec_bench_map,
            4, 100.0, TuneType.base, "test_label", InputType.test
        )
        assert any("taskset" in cmd for cmd in commands)
        assert any("CORE_NUM" in cmd for cmd in commands)

    def test_with_profile_gen(self, base_config, spec_bench_map):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_run_bench(
            "400.perlbench", True, spec_bench_map,
            -1, 100.0, TuneType.base, "test_label", InputType.test
        )
        assert any("LLVM_PROFILE_FILE" in cmd for cmd in commands)

    def test_ref_time_in_commands(self, base_config, spec_bench_map):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_run_bench(
            "400.perlbench", False, spec_bench_map,
            -1, 100.0, TuneType.base, "test_label", InputType.test
        )
        assert any("100.0" in cmd for cmd in commands)


class TestCommandsToSendMessage:
    """commands_to_send_message 函数测试"""

    def test_basic_message(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'copy_script_file_to_target_dir', return_value=True):
            commands = utils.commands_to_send_message("test message")
        assert len(commands) > 0
        assert any("message" in cmd.lower() for cmd in commands)

    def test_message_url_from_env(self, base_config):
        """测试消息URL从环境变量BOSC_MESSAGE_URL获取"""
        with patch('src.pack_spec.pack_utils.BOSC_MESSAGE_URL', 'http://custom-host:9999'):
            utils = PackUtils(base_config, MagicMock())
            commands = utils.commands_to_send_message("test message")
        assert any("http://custom-host:9999/send-message" in cmd for cmd in commands)

    def test_message_url_default(self, base_config):
        """测试未设置BOSC_MESSAGE_URL时使用默认值"""
        with patch('src.pack_spec.pack_utils.BOSC_MESSAGE_URL', 'http://172.38.8.102:8848'):
            utils = PackUtils(base_config, MagicMock())
            commands = utils.commands_to_send_message("test message")
        assert any("http://172.38.8.102:8848/send-message" in cmd for cmd in commands)


class TestCommandsToSendMdMessage:
    """commands_to_send_md_message 函数测试"""

    def test_basic_md_message(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'copy_script_file_to_target_dir', return_value=True):
            commands = utils.commands_to_send_md_message(
                temp_dir, "Test Title", "Test Content", "test.md"
            )
        assert len(commands) > 0


class TestCommandsToCollectProfiles:
    """commands_to_collect_profiles 函数测试"""

    def test_collect_profiles(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        with patch.object(utils, 'use_template_to_create_script'):
            commands = utils.commands_to_collect_profiles(temp_dir)
        assert len(commands) > 0


class TestParseSpecResults:
    """parse_spec_results 函数测试"""

    def test_empty_dir(self, temp_dir):
        result = parse_spec_results(temp_dir, SPECName.spec2006)
        assert result["benchmarks"] == {}
        assert result["int_score"] == 0.0
        assert result["fp_score"] == 0.0

    def test_no_sum_files(self, temp_dir):
        result_dir = os.path.join(temp_dir, "result")
        os.makedirs(result_dir)
        with open(os.path.join(result_dir, "other.txt"), "w") as f:
            f.write("not a sum file")
        result = parse_spec_results(temp_dir, SPECName.spec2006)
        assert result["benchmarks"] == {}

    def test_with_sum_file(self, temp_dir):
        result_dir = os.path.join(temp_dir, "result")
        os.makedirs(result_dir)
        sum_content = "Benchmark  Base  100.0  5.0\n400.perlbench  base  100.0  5.0\n"
        with open(os.path.join(result_dir, "test.sum"), "w") as f:
            f.write(sum_content)
        result = parse_spec_results(temp_dir, SPECName.spec2006)
        assert "400.perlbench" in result["benchmarks"]
        assert result["benchmarks"]["400.perlbench"]["score"] == 5.0


class TestCalculateSpecScore:
    """calculate_spec_score 函数测试"""

    def test_int_score_spec2006(self):
        benchmarks = {
            "400.perlbench": {"runtime": 100.0, "score": 5.0},
            "401.bzip2": {"runtime": 80.0, "score": 6.25},
        }
        score = calculate_spec_score(benchmarks, "int", SPECName.spec2006)
        assert score > 0

    def test_fp_score_spec2006(self):
        benchmarks = {
            "433.milc": {"runtime": 100.0, "score": 5.0},
            "434.zeusmp": {"runtime": 80.0, "score": 6.25},
        }
        score = calculate_spec_score(benchmarks, "fp", SPECName.spec2006)
        assert score > 0

    def test_int_score_spec2017(self):
        benchmarks = {
            "600.perlbench_s": {"runtime": 100.0, "score": 5.0},
            "602.gcc_s": {"runtime": 80.0, "score": 6.25},
        }
        score = calculate_spec_score(benchmarks, "int", SPECName.spec2017)
        assert score > 0

    def test_fp_score_spec2017(self):
        benchmarks = {
            "603.bwaves_s": {"runtime": 100.0, "score": 5.0},
            "607.cactuBSSN_s": {"runtime": 80.0, "score": 6.25},
        }
        score = calculate_spec_score(benchmarks, "fp", SPECName.spec2017)
        assert score > 0

    def test_empty_benchmarks(self):
        score = calculate_spec_score({}, "int", SPECName.spec2006)
        assert score == 0.0

    def test_spec2006v1p01_uses_spec2006_benches(self):
        """测试spec2006v1p01版本使用SPEC2006的基准测试列表"""
        benchmarks = {
            "400.perlbench": {"runtime": 100.0, "score": 5.0},
        }
        score = calculate_spec_score(benchmarks, "int", SPECName.spec2006v1p01)
        assert score > 0

    def test_bench_list_consistency_with_driver(self):
        """测试calculate_spec_score使用的基准测试列表与驱动模块定义一致"""
        from src.pack_spec.spec_2006_driver import SPEC2006_INT_BENCHES, SPEC2006_FP_BENCHES
        from src.pack_spec.spec_2017_driver import SPEC2017_INT_BENCHES, SPEC2017_FP_BENCHES

        all_2006_int = {"400.perlbench", "401.bzip2", "403.gcc", "429.mcf", "445.gobmk",
                        "456.hmmer", "458.sjeng", "462.libquantum", "464.h264ref",
                        "471.omnetpp", "473.astar", "483.xalancbmk"}
        assert set(SPEC2006_INT_BENCHES) == all_2006_int

        all_2006_fp = {"410.bwaves", "416.gamess", "433.milc", "434.zeusmp", "435.gromacs",
                       "436.cactusADM", "437.leslie3d", "444.namd", "447.dealII", "450.soplex",
                       "453.povray", "454.calculix", "459.GemsFDTD", "465.tonto", "470.lbm",
                       "481.wrf", "482.sphinx3"}
        assert set(SPEC2006_FP_BENCHES) == all_2006_fp

        all_2017_int = {"600.perlbench_s", "602.gcc_s", "605.mcf_s", "620.omnetpp_s",
                        "623.xalancbmk_s", "625.x264_s", "631.deepsjeng_s", "641.leela_s",
                        "648.exchange2_s", "657.xz_s"}
        assert set(SPEC2017_INT_BENCHES) == all_2017_int

        all_2017_fp = {"603.bwaves_s", "607.cactuBSSN_s", "619.lbm_s", "621.wrf_s",
                       "627.cam4_s", "628.pop2_s", "638.imagick_s", "644.nab_s",
                       "649.fotonik3d_s", "654.roms_s"}
        assert set(SPEC2017_FP_BENCHES) == all_2017_fp


class TestGenerateQemuVerifyScript:
    """generate_qemu_verify_script 函数测试"""

    def test_basic_script(self, temp_dir, spec_bench_map):
        run_script_path = os.path.join(temp_dir, "run_test.sh")
        with open(run_script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Starting run for copy #0\n")
            f.write("./perlbench_base.test_label < /dev/null\n")
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_script(
                "400.perlbench", temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test,
                "data", temp_dir
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "perlbench" in content
        assert "$QEMU_CMD ./perlbench_base.test_label" in content

    def test_script_without_run_file(self, temp_dir, spec_bench_map):
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_script(
                "400.perlbench", temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test,
                "data", temp_dir
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "警告: 未找到 run_test.sh" in content


class TestGenerateQemuVerifyAllScript:
    """generate_qemu_verify_all_script 函数测试"""

    def test_basic_all_script(self, temp_dir, spec_bench_map):
        for bench in ["400.perlbench", "401.bzip2"]:
            bench_dir = os.path.join(temp_dir, bench)
            os.makedirs(bench_dir, exist_ok=True)
            run_script_path = os.path.join(bench_dir, "run_test.sh")
            with open(run_script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"./{bench.split('.')[1]}_base.test_label < /dev/null\n")
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_all_script(
                ["400.perlbench", "401.bzip2"], temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test, temp_dir
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "perlbench" in content
        assert "bzip2" in content
        assert "$QEMU_CMD" in content

    def test_all_script_without_run_files(self, temp_dir, spec_bench_map):
        for bench in ["400.perlbench"]:
            bench_dir = os.path.join(temp_dir, bench)
            os.makedirs(bench_dir, exist_ok=True)
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_all_script(
                ["400.perlbench"], temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test, temp_dir
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "警告: 未找到 run_test.sh" in content

    def test_parallel_script_generation(self, temp_dir, spec_bench_map):
        """测试并行脚本生成功能"""
        for bench in ["400.perlbench", "401.bzip2", "403.gcc"]:
            bench_dir = os.path.join(temp_dir, bench)
            os.makedirs(bench_dir, exist_ok=True)
            run_script_path = os.path.join(bench_dir, "run_test.sh")
            with open(run_script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"./{bench.split('.')[1]}_base.test_label < /dev/null\n")
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_all_script(
                ["400.perlbench", "401.bzip2", "403.gcc"], temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test, temp_dir,
                parallel_jobs=4
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "PARALLEL_JOBS" in content
        assert "parallel_jobs=4" not in content
        assert "PARALLEL_JOBS=4" in content or "PARALLEL_JOBS=${PARALLEL_JOBS:-4}" in content
        assert "wait_for_slot" in content
        assert "&" in content
        assert "wait" in content

    def test_parallel_script_default_jobs(self, temp_dir, spec_bench_map):
        """测试默认并行数量（使用CPU核心数-2）"""
        for bench in ["400.perlbench"]:
            bench_dir = os.path.join(temp_dir, bench)
            os.makedirs(bench_dir, exist_ok=True)
            run_script_path = os.path.join(bench_dir, "run_test.sh")
            with open(run_script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("./perlbench_base.test_label < /dev/null\n")
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_all_script(
                ["400.perlbench"], temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test, temp_dir,
                parallel_jobs=0
            )
        assert os.path.exists(script_path)
        with open(script_path) as f:
            content = f.read()
        assert "$(nproc)" in content
        assert "$(($(nproc) - 2))" in content

    def test_parallel_script_result_statistics(self, temp_dir, spec_bench_map):
        """测试结果统计功能"""
        for bench in ["400.perlbench"]:
            bench_dir = os.path.join(temp_dir, bench)
            os.makedirs(bench_dir, exist_ok=True)
            run_script_path = os.path.join(bench_dir, "run_test.sh")
            with open(run_script_path, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("./perlbench_base.test_label < /dev/null\n")
        
        with patch('src.pack_spec.pack_utils.QEMU_CMD', 'qemu-aarch64'):
            script_path = generate_qemu_verify_all_script(
                ["400.perlbench"], temp_dir, spec_bench_map,
                TuneType.base, "test_label", InputType.test, temp_dir,
                parallel_jobs=2
            )
        with open(script_path) as f:
            content = f.read()
        assert "SUCCESS_COUNT" in content
        assert "FAIL_COUNT" in content
        assert "RESULT_DIR" in content
        assert "成功:" in content or "SUCCESS" in content
        assert "失败:" in content or "FAIL" in content


class TestPackUtilsExtended:
    """PackUtils 扩展方法测试"""

    def test_create_env_file(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        env_name = "compile"
        utils.create_env_file(temp_dir, env_name)
        env_path = os.path.join(temp_dir, "compile.env")
        assert os.path.exists(env_path)

    def test_execute_commands_success(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="output\n", returncode=0)
            result = utils.execute_commands("echo hello", "/tmp")
        mock_run.assert_called_once()
        # 验证命令以列表形式传递（shlex.split的结果）
        call_args = mock_run.call_args[0][0]
        assert isinstance(call_args, list)
        assert call_args == ["echo", "hello"]
        assert "output" in result

    def test_execute_commands_failure(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("command failed")
            with pytest.raises(CommandExecutionError):
                utils.execute_commands("bad_command", "/tmp")

    def test_execute_commands_shlex_split_quoted_args(self, base_config):
        """测试shlex.split正确处理带引号的命令参数，防止命令注入"""
        utils = PackUtils(base_config, MagicMock())
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
            utils.execute_commands('echo "hello world"', "/tmp")
        call_args = mock_run.call_args[0][0]
        assert isinstance(call_args, list)
        # shlex.split会将引号内的内容作为一个整体参数
        assert call_args == ["echo", "hello world"]
        # 确保不会被错误拆分为 ["echo", "\"hello", "world\""]
        assert call_args != ["echo", '"hello', 'world"']

    def test_execute_commands_shlex_split_injection_prevention(self, base_config):
        """测试shlex.split防止命令注入攻击"""
        utils = PackUtils(base_config, MagicMock())
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
            # 模拟恶意输入：尝试通过分号注入额外命令
            utils.execute_commands('echo "test; rm -rf /"', "/tmp")
        call_args = mock_run.call_args[0][0]
        assert isinstance(call_args, list)
        # shlex.split会将分号作为参数的一部分，而不是命令分隔符
        assert call_args == ["echo", "test; rm -rf /"]
        # 确保不会拆分成多个命令
        assert len(call_args) == 2

    def test_use_template_to_create_script(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        template_content = "LLVM_PATH=<your llvm-profdata abspath>\n"
        template_path = os.path.join(SCRIPTS_PATH, "test_template.sh.template")
        with open(template_path, "w") as f:
            f.write(template_content)
        try:
            replace_dict = {"<your llvm-profdata abspath>": "/usr/bin/llvm-profdata"}
            utils.use_template_to_create_script("test_template.sh.template", temp_dir, replace_dict)
            script_path = os.path.join(temp_dir, "test_template.sh")
            assert os.path.exists(script_path)
            with open(script_path) as f:
                content = f.read()
            assert "/usr/bin/llvm-profdata" in content
        finally:
            if os.path.exists(template_path):
                os.remove(template_path)

    def test_create_spec_setup_log_path(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        log_content = "setup log content"
        with patch.object(utils, 'get_pack_generated_dir_path', return_value=temp_dir):
            path = utils.create_spec_setup_log_path(log_content, "test.cfg", TuneType.base, InputType.ref)
        assert "test.base_ref.setuplog" in path

    def test_copy_spec_cfg_and_logs_to_target_dir(self, base_config, temp_dir):
        utils = PackUtils(base_config, MagicMock())
        spec_dir = os.path.join(temp_dir, "spec")
        config_dir = os.path.join(spec_dir, "config")
        os.makedirs(config_dir)
        cfg_path = os.path.join(config_dir, "test.cfg")
        with open(cfg_path, "w") as f:
            f.write("config content")
        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir)
        with patch.object(utils, 'get_spec_setup_log_path', return_value=""), \
             patch.object(utils, 'get_spec_log_file_path', return_value=""), \
             patch.object(utils, 'create_env_file'), \
             patch.object(utils, 'copy_pack_log_file_to_target_dir'):
            utils.copy_spec_cfg_and_logs_to_target_dir(spec_dir, "test.cfg", dest_dir, TuneType.base, InputType.ref)
        assert os.path.exists(os.path.join(dest_dir, "test.cfg"))

    def test_commands_to_prepare_run_minimal_no_curl(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_prepare_run("test.log", -1, 3, minimal_mode=True)
        assert not any("curl" in cmd for cmd in commands)

    def test_commands_to_prepare_run_normal_has_curl(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        commands = utils.commands_to_prepare_run("test.log", -1, 3, minimal_mode=False)
        assert any("curl" in cmd for cmd in commands)

    def test_get_run_script_name_with_suffix(self, base_config):
        utils = PackUtils(base_config, MagicMock())
        name = utils.get_run_script_name(False, InputType.ref, "qemu_verify")
        assert name == "test_ref_qemu_verify.sh"

    def test_get_pack_generated_dir_path_contains_name(self, base_config):
        base_config["pack_config"]["auto_mode"] = True
        utils = PackUtils(base_config, MagicMock())
        path = utils.get_pack_generated_dir_path()
        assert path.endswith("test_pack")
