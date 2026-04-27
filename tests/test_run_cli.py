"""
run-cli.py 单元测试

测试命令行参数解析、枚举转换、配置构建、配置文件加载与合并、异常处理和帮助信息
"""

import sys
import os
import importlib
import pytest
from unittest.mock import patch, MagicMock

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, RunMode, PackSPECError
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_run_cli_spec = importlib.util.spec_from_file_location(
    "run_cli",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run-cli.py"),
)
run_cli = importlib.util.module_from_spec(_run_cli_spec)
sys.modules["run_cli"] = run_cli
_run_cli_spec.loader.exec_module(run_cli)

build_arg_parser = run_cli.build_arg_parser
build_config = run_cli.build_config
_get_explicit_args = run_cli._get_explicit_args
parse_enum = run_cli.parse_enum
ENUM_MAP = run_cli.ENUM_MAP


class TestBuildArgParser:
    """build_arg_parser() 参数解析测试"""

    def test_解析所有参数(self):
        """测试解析器能正确解析所有参数"""
        parser = build_arg_parser()
        args = parser.parse_args([
            "--spec-name", "spec2017",
            "--cfg-path", "/path/to/config.cfg",
            "--pack-name", "my_pack",
            "--tune-type", "peak",
            "--input-type", "test",
            "--spec-mode", "rate",
            "--spec-benches", "400.perlbench",
            "--iterations", "5",
            "--rebuild",
            "--test-core-num", "2",
            "--test-clock-rate", "2.5",
            "--profile-gen",
            "--auto-mode",
            "--verify-mode",
            "--minimal-mode",
            "--qemu-verify-parallel-jobs", "4",
            "--report-format", "markdown",
            "--run-mode", "direct",
            "--log-language", "en",
            "--setup-spec",
            "--pack-binaries",
            "--pack-benches",
            "--enable-dingtalk-message",
        ])
        assert args.spec_name == "spec2017"
        assert args.cfg_path == "/path/to/config.cfg"
        assert args.pack_name == "my_pack"
        assert args.tune_type == "peak"
        assert args.input_type == "test"
        assert args.spec_mode == "rate"
        assert args.spec_benches == "400.perlbench"
        assert args.iterations == 5
        assert args.rebuild is True
        assert args.test_core_num == 2
        assert args.test_clock_rate == 2.5
        assert args.profile_gen is True
        assert args.auto_mode is True
        assert args.verify_mode is True
        assert args.minimal_mode is True
        assert args.qemu_verify_parallel_jobs == 4
        assert args.report_format == "markdown"
        assert args.run_mode == "direct"
        assert args.log_language == "en"
        assert args.setup_spec is True
        assert args.pack_binaries is True
        assert args.pack_benches is True
        assert args.enable_dingtalk_message is True

    def test_默认参数值(self):
        """测试默认参数值正确"""
        parser = build_arg_parser()
        args = parser.parse_args([])
        assert args.config is None
        assert args.spec_name is None
        assert args.cfg_path is None
        assert args.pack_name == "packspec"
        assert args.tune_type == "base"
        assert args.input_type == "ref"
        assert args.spec_mode == "speed"
        assert args.spec_benches == "all"
        assert args.iterations == 3
        assert args.rebuild is False
        assert args.test_core_num == -1
        assert args.test_clock_rate == 1.0
        assert args.profile_gen is False
        assert args.auto_mode is False
        assert args.verify_mode is False
        assert args.minimal_mode is False
        assert args.qemu_verify_parallel_jobs == 0
        assert args.report_format == "json"
        assert args.run_mode == "pack"
        assert args.log_language == "zh"
        assert args.setup_spec is False
        assert args.pack_binaries is False
        assert args.pack_benches is False
        assert args.enable_dingtalk_message is False

    def test_store_true参数_rebuild(self):
        """测试 --rebuild store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--rebuild"])
        assert args.rebuild is True

    def test_store_true参数_profile_gen(self):
        """测试 --profile-gen store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--profile-gen"])
        assert args.profile_gen is True

    def test_store_true参数_auto_mode(self):
        """测试 --auto-mode store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--auto-mode"])
        assert args.auto_mode is True

    def test_store_true参数_verify_mode(self):
        """测试 --verify-mode store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--verify-mode"])
        assert args.verify_mode is True

    def test_store_true参数_minimal_mode(self):
        """测试 --minimal-mode store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--minimal-mode"])
        assert args.minimal_mode is True

    def test_store_true参数_setup_spec(self):
        """测试 --setup-spec store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--setup-spec"])
        assert args.setup_spec is True

    def test_store_true参数_enable_dingtalk_message(self):
        """测试 --enable-dingtalk-message store_true 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["--enable-dingtalk-message"])
        assert args.enable_dingtalk_message is True

    def test_pack_binaries正向标志(self):
        """测试 --pack-binaries 正向标志"""
        parser = build_arg_parser()
        args = parser.parse_args(["--pack-binaries"])
        assert args.pack_binaries is True
        args_default = parser.parse_args([])
        assert args_default.pack_binaries is False

    def test_pack_benches正向标志(self):
        """测试 --pack-benches 正向标志"""
        parser = build_arg_parser()
        args = parser.parse_args(["--pack-benches"])
        assert args.pack_benches is True
        args_default = parser.parse_args([])
        assert args_default.pack_benches is False

    def test_配置文件参数(self):
        """测试 -c/--config 参数"""
        parser = build_arg_parser()
        args = parser.parse_args(["-c", "/path/to/config.json"])
        assert args.config == "/path/to/config.json"
        args_long = parser.parse_args(["--config", "/path/to/other.json"])
        assert args_long.config == "/path/to/other.json"


class TestParseEnum:
    """parse_enum() 枚举转换测试"""

    def test_spec_name有效值_spec2006(self):
        assert parse_enum("spec_name", "spec2006") == SPECName.spec2006

    def test_spec_name有效值_spec2006v1p01(self):
        assert parse_enum("spec_name", "spec2006v1p01") == SPECName.spec2006v1p01

    def test_spec_name有效值_spec2017(self):
        assert parse_enum("spec_name", "spec2017") == SPECName.spec2017

    def test_tune_type有效值_base(self):
        assert parse_enum("tune_type", "base") == TuneType.base

    def test_tune_type有效值_peak(self):
        assert parse_enum("tune_type", "peak") == TuneType.peak

    def test_tune_type有效值_all(self):
        assert parse_enum("tune_type", "all") == TuneType.all

    def test_input_type有效值_test(self):
        assert parse_enum("input_type", "test") == InputType.test

    def test_input_type有效值_train(self):
        assert parse_enum("input_type", "train") == InputType.train

    def test_input_type有效值_ref(self):
        assert parse_enum("input_type", "ref") == InputType.ref

    def test_input_type有效值_all(self):
        assert parse_enum("input_type", "all") == InputType.all

    def test_spec_mode有效值_speed(self):
        assert parse_enum("spec_mode", "speed") == SPECMode.speed

    def test_spec_mode有效值_rate(self):
        assert parse_enum("spec_mode", "rate") == SPECMode.rate

    def test_run_mode有效值_pack(self):
        assert parse_enum("run_mode", "pack") == RunMode.pack

    def test_run_mode有效值_direct(self):
        assert parse_enum("run_mode", "direct") == RunMode.direct

    def test_无效值抛出SystemExit(self):
        """测试 parse_enum() 对无效值抛出 SystemExit（退出码 1）"""
        with pytest.raises(SystemExit) as exc_info:
            parse_enum("tune_type", "invalid_value")
        assert exc_info.value.code == 1

    def test_无效spec_name抛出SystemExit(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_enum("spec_name", "spec2099")
        assert exc_info.value.code == 1

    def test_无效input_type抛出SystemExit(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_enum("input_type", "unknown")
        assert exc_info.value.code == 1

    def test_无效spec_mode抛出SystemExit(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_enum("spec_mode", "fast")
        assert exc_info.value.code == 1

    def test_无效run_mode抛出SystemExit(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_enum("run_mode", "batch")
        assert exc_info.value.code == 1


class TestBuildConfig:
    """build_config() 配置构建测试"""

    def _make_args(self, **overrides):
        """构造命令行参数 Namespace 对象"""
        import argparse
        defaults = {
            "config": None,
            "spec_name": "spec2017",
            "cfg_path": "/path/to/config.cfg",
            "pack_name": "packspec",
            "tune_type": "base",
            "input_type": "ref",
            "spec_mode": "speed",
            "spec_benches": "all",
            "iterations": 3,
            "rebuild": False,
            "test_core_num": -1,
            "test_clock_rate": 1.0,
            "profile_gen": False,
            "auto_mode": False,
            "verify_mode": False,
            "minimal_mode": False,
            "allow_basepeak": False,
            "pack_builds": False,
            "qemu_verify_parallel_jobs": 0,
            "report_format": "json",
            "run_mode": "pack",
            "log_language": "zh",
            "setup_spec": False,
            "pack_binaries": False,
            "pack_benches": False,
            "enable_dingtalk_message": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _build_with_parser(self, args):
        """使用默认解析器调用 build_config"""
        parser = build_arg_parser()
        return build_config(parser, args)

    def test_从纯命令行参数构建完整配置字典(self):
        """测试 build_config() 从纯命令行参数构建完整配置字典"""
        args = self._make_args()
        config = self._build_with_parser(args)
        assert "task" in config
        assert "spec_config" in config
        assert "pack_config" in config
        assert "msg_config" in config

    def test_枚举值正确转换_spec_name(self):
        """测试 build_config() 中 spec_name 枚举值正确转换"""
        args = self._make_args(spec_name="spec2017")
        config = self._build_with_parser(args)
        assert config["spec_config"]["spec_name"] == SPECName.spec2017

    def test_枚举值正确转换_tune_type(self):
        """测试 build_config() 中 tune_type 枚举值正确转换"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--tune-type", "peak"])
        config = build_config(parser, args)
        assert config["spec_config"]["tune_type"] == TuneType.peak

    def test_枚举值正确转换_input_type(self):
        """测试 build_config() 中 input_type 枚举值正确转换"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--input-type", "test"])
        config = build_config(parser, args)
        assert config["spec_config"]["input_type"] == InputType.test

    def test_枚举值正确转换_spec_mode(self):
        """测试 build_config() 中 spec_mode 枚举值正确转换"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--spec-mode", "rate"])
        config = build_config(parser, args)
        assert config["spec_config"]["spec_mode"] == SPECMode.rate

    def test_枚举值正确转换_run_mode(self):
        """测试 build_config() 中 run_mode 枚举值正确转换"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--run-mode", "direct"])
        config = build_config(parser, args)
        assert config["task"]["run_mode"] == RunMode.direct

    def test_pack_binaries设置为True(self):
        """测试 build_config() 中 --pack-binaries 设置为 pack_binaries=True"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--pack-binaries"])
        config = build_config(parser, args)
        assert config["task"]["pack_binaries"] is True

    def test_pack_binaries默认不设置(self):
        """测试未指定 --pack-binaries 时 pack_binaries 不被设置（保留配置文件值）"""
        args = self._make_args(pack_binaries=False)
        config = self._build_with_parser(args)
        assert config["task"].get("pack_binaries") is None or "pack_binaries" not in config["task"]

    def test_pack_benches设置为True(self):
        """测试 build_config() 中 --pack-benches 设置为 pack_benches=True"""
        parser = build_arg_parser()
        args = parser.parse_args(["--spec-name", "spec2017", "--cfg-path", "/p", "--pack-benches"])
        config = build_config(parser, args)
        assert config["task"]["pack_benches"] is True

    def test_pack_benches默认不设置(self):
        """测试未指定 --pack-benches 时 pack_benches 不被设置（保留配置文件值）"""
        args = self._make_args(pack_benches=False)
        config = self._build_with_parser(args)
        assert config["task"].get("pack_benches") is None or "pack_benches" not in config["task"]

    def test_未指定c且缺少spec_name抛出SystemExit(self):
        """测试 build_config() 未指定 -c 且缺少 --spec-name 时抛出 SystemExit"""
        args = self._make_args(config=None, spec_name=None)
        with pytest.raises(SystemExit) as exc_info:
            self._build_with_parser(args)
        assert exc_info.value.code == 1

    def test_未指定c且缺少cfg_path抛出SystemExit(self):
        """测试 build_config() 未指定 -c 且缺少 --cfg-path 时抛出 SystemExit"""
        args = self._make_args(config=None, cfg_path=None)
        with pytest.raises(SystemExit) as exc_info:
            self._build_with_parser(args)
        assert exc_info.value.code == 1

    def test_配置字段完整性(self):
        """测试无配置文件时显式指定所有参数构建的配置字典包含所有必要字段"""
        parser = build_arg_parser()
        args = parser.parse_args([
            "--spec-name", "spec2017", "--cfg-path", "/path/to/config.cfg",
            "--pack-name", "my_pack", "--tune-type", "peak",
            "--input-type", "test", "--spec-mode", "rate",
            "--spec-benches", "int", "--iterations", "5",
            "--rebuild",
            "--test-core-num", "2", "--test-clock-rate", "2.5",
            "--profile-gen", "--auto-mode", "--verify-mode", "--minimal-mode",
            "--qemu-verify-parallel-jobs", "4",
            "--report-format", "markdown", "--run-mode", "direct",
            "--log-language", "en",
            "--setup-spec", "--pack-binaries", "--pack-benches",
            "--enable-dingtalk-message",
        ])
        config = build_config(parser, args)
        task = config["task"]
        assert task["pack_name"] == "my_pack"
        assert task["setup_spec"] is True
        assert task["pack_binaries"] is True
        assert task["pack_benches"] is True
        assert task["run_mode"] == RunMode.direct
        spec = config["spec_config"]
        assert spec["spec_cfg_path"] == "/path/to/config.cfg"
        assert spec["spec_name"] == SPECName.spec2017
        assert spec["tune_type"] == TuneType.peak
        assert spec["input_type"] == InputType.test
        assert spec["spec_mode"] == SPECMode.rate
        assert spec["spec_benches"] == "int"
        assert spec["iterations"] == 5
        assert spec["rebuild"] is True
        pack = config["pack_config"]
        assert pack["test_core_num"] == 2
        assert pack["test_clock_rate"] == 2.5
        assert pack["profile_gen"] is True
        assert pack["auto_mode"] is True
        assert pack["verify_mode"] is True
        assert pack["minimal_mode"] is True
        assert pack["qemu_verify_parallel_jobs"] == 4
        assert pack["report_format"] == "markdown"
        msg = config["msg_config"]
        assert msg["enable_dingtalk_message"] is True
        assert msg["log_language"] == "en"


class TestBuildConfigWithFile:
    """build_config() 配置文件加载与合并测试"""

    def _make_args(self, **overrides):
        """构造命令行参数 Namespace 对象"""
        import argparse
        defaults = {
            "config": None,
            "spec_name": "spec2017",
            "cfg_path": "/path/to/config.cfg",
            "pack_name": "packspec",
            "tune_type": "base",
            "input_type": "ref",
            "spec_mode": "speed",
            "spec_benches": "all",
            "iterations": 3,
            "rebuild": False,
            "test_core_num": -1,
            "test_clock_rate": 1.0,
            "profile_gen": False,
            "auto_mode": False,
            "verify_mode": False,
            "minimal_mode": False,
            "allow_basepeak": False,
            "pack_builds": False,
            "qemu_verify_parallel_jobs": 0,
            "report_format": "json",
            "run_mode": "pack",
            "log_language": "zh",
            "setup_spec": False,
            "pack_binaries": False,
            "pack_benches": False,
            "enable_dingtalk_message": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _build_with_parser(self, args):
        """使用默认解析器调用 build_config"""
        parser = build_arg_parser()
        return build_config(parser, args)

    @patch("run_cli.load_pack_spec_cfg")
    def test_指定c时加载配置文件(self, mock_load):
        """测试 build_config() 指定 -c 时加载配置文件"""
        mock_load.return_value = {
            "task": {"pack_name": "file_pack"},
            "spec_config": {"spec_name": SPECName.spec2006},
            "pack_config": {"auto_mode": True},
            "msg_config": {"log_language": "en"},
        }
        args = self._make_args(config="/path/to/config.json")
        config = self._build_with_parser(args)
        mock_load.assert_called_once_with("/path/to/config.json")
        # 未显式指定 --pack-name，应保留配置文件中的值
        assert config["task"]["pack_name"] == "file_pack"

    @patch("run_cli.load_pack_spec_cfg")
    def test_显式指定的命令行参数覆盖配置文件字段(self, mock_load):
        """测试 build_config() 显式指定的命令行参数覆盖配置文件字段"""
        mock_load.return_value = {
            "task": {"pack_name": "file_pack", "setup_spec": True},
            "spec_config": {
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.peak,
                "iterations": 1,
            },
            "pack_config": {"auto_mode": True},
            "msg_config": {"log_language": "en"},
        }
        parser = build_arg_parser()
        args = parser.parse_args([
            "-c", "/path/to/config.json",
            "--pack-name", "cli_pack",
            "--tune-type", "all",
            "--iterations", "5",
        ])
        config = build_config(parser, args)
        # 显式指定的参数应覆盖配置文件
        assert config["task"]["pack_name"] == "cli_pack"
        assert config["spec_config"]["tune_type"] == TuneType.all
        assert config["spec_config"]["iterations"] == 5
        # 未显式指定的参数应保留配置文件中的值
        assert config["task"]["setup_spec"] is True
        assert config["spec_config"]["spec_name"] == SPECName.spec2006
        assert config["pack_config"]["auto_mode"] is True
        assert config["msg_config"]["log_language"] == "en"

    @patch("run_cli.load_pack_spec_cfg")
    def test_未显式指定的参数保留配置文件值(self, mock_load):
        """测试未显式指定的命令行参数不覆盖配置文件中的值"""
        mock_load.return_value = {
            "task": {"pack_name": "file_pack", "setup_spec": True, "pack_binaries": False},
            "spec_config": {
                "spec_name": SPECName.spec2006,
                "tune_type": TuneType.peak,
                "input_type": InputType.test,
                "spec_mode": SPECMode.rate,
                "spec_benches": "int",
                "iterations": 1,
            },
            "pack_config": {"auto_mode": True, "test_core_num": 8, "test_clock_rate": 2.5},
            "msg_config": {"log_language": "en", "enable_dingtalk_message": True},
        }
        # 只指定 -c，不指定其他参数
        parser = build_arg_parser()
        args = parser.parse_args(["-c", "/path/to/config.json"])
        config = build_config(parser, args)
        # 所有值应来自配置文件
        assert config["task"]["pack_name"] == "file_pack"
        assert config["task"]["setup_spec"] is True
        assert config["task"]["pack_binaries"] is False
        assert config["spec_config"]["spec_name"] == SPECName.spec2006
        assert config["spec_config"]["tune_type"] == TuneType.peak
        assert config["spec_config"]["input_type"] == InputType.test
        assert config["spec_config"]["spec_mode"] == SPECMode.rate
        assert config["spec_config"]["spec_benches"] == "int"
        assert config["spec_config"]["iterations"] == 1
        assert config["pack_config"]["auto_mode"] is True
        assert config["pack_config"]["test_core_num"] == 8
        assert config["pack_config"]["test_clock_rate"] == 2.5
        assert config["msg_config"]["log_language"] == "en"
        assert config["msg_config"]["enable_dingtalk_message"] is True

    @patch("run_cli.load_pack_spec_cfg")
    def test_配置文件中缺少子字典时自动创建(self, mock_load):
        """测试配置文件中缺少子字典时 build_config() 自动创建"""
        mock_load.return_value = {}
        args = self._make_args(config="/path/to/config.json")
        config = self._build_with_parser(args)
        assert "task" in config
        assert "spec_config" in config
        assert "pack_config" in config
        assert "msg_config" in config


class TestMainExceptions:
    """main() 异常处理测试"""

    @patch("run_cli.PackSPEC")
    @patch("run_cli.build_config")
    @patch("run_cli.build_arg_parser")
    def test_PackSPECError被捕获并以错误码退出(self, mock_parser_cls, mock_build_config, mock_packspec_cls):
        """测试 main() 中 PackSPECError 被捕获并以 e.code 退出"""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_build_config.return_value = {"task": {}, "spec_config": {}, "pack_config": {}, "msg_config": {}}
        mock_packspec_cls.side_effect = PackSPECError("测试错误", code=42)

        from run_cli import main
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 42

    @patch("run_cli.PackSPEC")
    @patch("run_cli.build_config")
    @patch("run_cli.build_arg_parser")
    def test_KeyboardInterrupt以130退出(self, mock_parser_cls, mock_build_config, mock_packspec_cls):
        """测试 main() 中 KeyboardInterrupt 以 130 退出"""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock()
        mock_parser_cls.return_value = mock_parser
        mock_build_config.return_value = {"task": {}, "spec_config": {}, "pack_config": {}, "msg_config": {}}
        mock_packspec_cls.side_effect = KeyboardInterrupt()

        from run_cli import main
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 130


class TestHelpInfo:
    """帮助信息测试"""

    def test_h显示帮助信息(self):
        """测试 -h 显示帮助信息并退出"""
        parser = build_arg_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["-h"])
        assert exc_info.value.code == 0

    def test_help显示帮助信息(self):
        """测试 --help 显示帮助信息并退出"""
        parser = build_arg_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_帮助信息包含描述(self):
        """测试帮助信息包含程序描述"""
        parser = build_arg_parser()
        assert "PackSPEC" in parser.description
        assert "SPEC" in parser.description


class TestGetExplicitArgs:
    """_get_explicit_args() 显式参数检测测试"""

    def test_无显式参数时返回空集(self):
        """测试不传任何参数时返回空集合"""
        parser = build_arg_parser()
        args = parser.parse_args([])
        explicit = _get_explicit_args(parser, args)
        assert len(explicit) == 0

    def test_显式指定的参数被检测到(self):
        """测试显式指定的参数出现在结果集合中"""
        parser = build_arg_parser()
        args = parser.parse_args(["--tune-type", "peak", "--iterations", "5"])
        explicit = _get_explicit_args(parser, args)
        assert "tune_type" in explicit
        assert "iterations" in explicit

    def test_store_true参数为True时被检测到(self):
        """测试 store_true 参数值为 True 时被检测为显式指定"""
        parser = build_arg_parser()
        args = parser.parse_args(["--rebuild", "--auto-mode"])
        explicit = _get_explicit_args(parser, args)
        assert "rebuild" in explicit
        assert "auto_mode" in explicit

    def test_store_true参数为False时不被检测到(self):
        """测试 store_true 参数值为 False（默认值）时不被检测为显式指定"""
        parser = build_arg_parser()
        args = parser.parse_args([])
        explicit = _get_explicit_args(parser, args)
        assert "rebuild" not in explicit
        assert "auto_mode" not in explicit

    def test_config参数被检测到(self):
        """测试 -c 参数被检测为显式指定"""
        parser = build_arg_parser()
        args = parser.parse_args(["-c", "/path/to/config.json"])
        explicit = _get_explicit_args(parser, args)
        assert "config" in explicit


class TestEnumMap:
    """ENUM_MAP 映射表测试"""

    def test_ENUM_MAP包含所有字段(self):
        """测试 ENUM_MAP 包含所有枚举字段"""
        assert "spec_name" in ENUM_MAP
        assert "tune_type" in ENUM_MAP
        assert "input_type" in ENUM_MAP
        assert "spec_mode" in ENUM_MAP
        assert "run_mode" in ENUM_MAP

    def test_ENUM_MAP字段与枚举类一致(self):
        """测试 ENUM_MAP 中每个字段的 cls 与对应枚举类一致"""
        assert ENUM_MAP["spec_name"]["cls"] == SPECName
        assert ENUM_MAP["tune_type"]["cls"] == TuneType
        assert ENUM_MAP["input_type"]["cls"] == InputType
        assert ENUM_MAP["spec_mode"]["cls"] == SPECMode
        assert ENUM_MAP["run_mode"]["cls"] == RunMode
