"""
PackSPEC 命令行入口模块

本模块提供 PackSPEC 工具的命令行接口，支持通过命令行参数配置和运行 SPEC 基准测试打包任务。

使用方式：
    # 使用命令行参数
    python run-cli.py --spec-name spec2017 --cfg-path /path/to/config.cfg

    # 使用配置文件
    python run-cli.py -c /path/to/config.json

    # 混合使用（命令行参数覆盖配置文件）
    python run-cli.py -c /path/to/config.json --tune-type peak
"""

import argparse
import sys

from src.pack_spec.pack_spec import PackSPEC
from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, RunMode, PackSPECError
)
from src.pack_spec.pack_utils import load_pack_spec_cfg


# 枚举类型映射表，用于将命令行字符串转换为对应的枚举值
ENUM_MAP = {
    "spec_name": {
        "cls": SPECName,
        "values": {
            "spec2006": SPECName.spec2006,
            "spec2006v1p01": SPECName.spec2006v1p01,
            "spec2017": SPECName.spec2017,
        },
    },
    "tune_type": {
        "cls": TuneType,
        "values": {
            "base": TuneType.base,
            "peak": TuneType.peak,
            "all": TuneType.all,
        },
    },
    "input_type": {
        "cls": InputType,
        "values": {
            "test": InputType.test,
            "train": InputType.train,
            "ref": InputType.ref,
            "all": InputType.all,
        },
    },
    "spec_mode": {
        "cls": SPECMode,
        "values": {
            "speed": SPECMode.speed,
            "rate": SPECMode.rate,
        },
    },
    "run_mode": {
        "cls": RunMode,
        "values": {
            "pack": RunMode.pack,
            "direct": RunMode.direct,
        },
    },
}


def parse_enum(field_name: str, value: str):
    """
    将命令行字符串参数转换为对应的枚举值

    Args:
        field_name (str): 枚举字段名称，用于在 ENUM_MAP 中查找映射
        value (str): 命令行传入的字符串值

    Returns:
        Enum: 对应的枚举实例

    Raises:
        SystemExit: 当传入的值不在有效枚举值范围内时，打印错误信息并退出
    """
    mapping = ENUM_MAP[field_name]
    values = mapping["values"]
    if value not in values:
        valid = ", ".join(values.keys())
        print(f"错误: '{field_name}' 的值 '{value}' 无效，有效值为: {valid}", file=sys.stderr)
        sys.exit(1)
    return values[value]


def build_arg_parser() -> argparse.ArgumentParser:
    """
    构建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 配置好的参数解析器实例
    """
    parser = argparse.ArgumentParser(
        description="PackSPEC - SPEC CPU 基准测试打包工具命令行接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 配置文件参数
    parser.add_argument(
        "-c", "--config",
        dest="config",
        default=None,
        help="配置文件路径（JSON格式），指定后其他命令行参数可覆盖配置文件中的对应字段",
    )

    # 必选参数（当未指定 -c 时必须提供）
    parser.add_argument(
        "--spec-name",
        dest="spec_name",
        default=None,
        choices=["spec2006", "spec2006v1p01", "spec2017"],
        help="SPEC 版本（spec2006/spec2006v1p01/spec2017），未指定 -c 时必选",
    )
    parser.add_argument(
        "--cfg-path",
        dest="cfg_path",
        default=None,
        help="SPEC cfg 文件路径，未指定 -c 时必选",
    )

    # 可选参数
    parser.add_argument(
        "--pack-name",
        dest="pack_name",
        default="packspec",
        help="打包任务名称（默认: packspec）",
    )
    parser.add_argument(
        "--tune-type",
        dest="tune_type",
        default="base",
        choices=["base", "peak", "all"],
        help="优化级别（base/peak/all，默认: base）",
    )
    parser.add_argument(
        "--input-type",
        dest="input_type",
        default="ref",
        choices=["test", "train", "ref", "all"],
        help="输入类型（test/train/ref/all，默认: ref）",
    )
    parser.add_argument(
        "--spec-mode",
        dest="spec_mode",
        default="speed",
        choices=["speed", "rate"],
        help="运行模式（speed/rate，默认: speed）",
    )
    parser.add_argument(
        "--spec-benches",
        dest="spec_benches",
        default="all",
        help="基准测试选择（默认: all）",
    )
    parser.add_argument(
        "--iterations",
        dest="iterations",
        type=int,
        default=3,
        help="迭代次数（默认: 3）",
    )
    parser.add_argument(
        "--rebuild",
        dest="rebuild",
        action="store_true",
        help="是否重新构建",
    )
    parser.add_argument(
        "--test-core-num",
        dest="test_core_num",
        type=int,
        default=-1,
        help="绑定核心编号（默认: -1，不绑定）",
    )
    parser.add_argument(
        "--test-clock-rate",
        dest="test_clock_rate",
        type=float,
        default=1.0,
        help="CPU 主频 GHz（默认: 1.0）",
    )
    parser.add_argument(
        "--profile-gen",
        dest="profile_gen",
        action="store_true",
        help="Profile 生成模式",
    )
    parser.add_argument(
        "--auto-mode",
        dest="auto_mode",
        action="store_true",
        help="自动模式",
    )
    parser.add_argument(
        "--verify-mode",
        dest="verify_mode",
        action="store_true",
        help="QEMU 验证模式",
    )
    parser.add_argument(
        "--minimal-mode",
        dest="minimal_mode",
        action="store_true",
        help="极简模式",
    )
    parser.add_argument(
        "--allow-basepeak",
        dest="allow_basepeak",
        action="store_true",
        help="允许basepeak配置（当cfg文件中设置basepeak=yes时需要启用）",
    )
    parser.add_argument(
        "--pack-builds",
        dest="pack_builds",
        action="store_true",
        help="打包 build 和 run 目录到一个 build 目录",
    )
    parser.add_argument(
        "--qemu-verify-parallel-jobs",
        dest="qemu_verify_parallel_jobs",
        type=int,
        default=0,
        help="QEMU 验证并行数（默认: 0，自动使用 CPU 核心数-2）",
    )
    parser.add_argument(
        "--report-format",
        dest="report_format",
        default="json",
        choices=["json", "markdown"],
        help="报告格式（json/markdown，默认: json）",
    )
    parser.add_argument(
        "--run-mode",
        dest="run_mode",
        default="pack",
        choices=["pack", "direct"],
        help="运行模式（pack/direct，默认: pack）",
    )
    parser.add_argument(
        "--log-language",
        dest="log_language",
        default="zh",
        choices=["zh", "en"],
        help="日志语言（zh/en，默认: zh）",
    )
    parser.add_argument(
        "--setup-spec",
        dest="setup_spec",
        action="store_true",
        help="执行 setup 编译",
    )
    parser.add_argument(
        "--pack-binaries",
        dest="pack_binaries",
        action="store_true",
        help="打包二进制文件（需配合 --setup-spec 使用）",
    )
    parser.add_argument(
        "--pack-benches",
        dest="pack_benches",
        action="store_true",
        help="打包完整测试环境（需配合 --setup-spec 使用）",
    )
    parser.add_argument(
        "--enable-dingtalk-message",
        dest="enable_dingtalk_message",
        action="store_true",
        help="是否开启钉钉消息",
    )

    return parser


def _get_explicit_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> set:
    """
    获取用户在命令行中显式指定的参数名集合

    通过比较解析结果与默认值，识别哪些参数是用户显式指定的。
    对于 store_true 类型的参数，值为 True 时即为显式指定。

    Args:
        parser (argparse.ArgumentParser): 参数解析器
        args (argparse.Namespace): 解析后的命令行参数

    Returns:
        set: 用户显式指定的参数 dest 名称集合
    """
    explicit = set()
    for action in parser._actions:
        if action.dest == "help":
            continue
        if isinstance(action, argparse._HelpAction):
            continue
        value = getattr(args, action.dest, None)
        if value != action.default:
            explicit.add(action.dest)
    return explicit


def build_config(parser: argparse.ArgumentParser, args: argparse.Namespace) -> dict:
    """
    根据命令行参数构建 PackSPEC 配置字典

    如果指定了配置文件，先加载配置文件作为基础配置，
    然后仅用用户显式指定的命令行参数覆盖配置文件中的对应字段。
    未显式指定的参数保留配置文件中的值。

    Args:
        parser (argparse.ArgumentParser): 参数解析器，用于检测显式指定的参数
        args (argparse.Namespace): 解析后的命令行参数

    Returns:
        dict: 完整的 PackSPEC 配置字典

    Raises:
        SystemExit: 当未指定 -c 且缺少必选参数时退出
    """
    # 获取用户显式指定的参数集合
    explicit = _get_explicit_args(parser, args)

    # 如果指定了配置文件，先加载
    if args.config:
        config = load_pack_spec_cfg(args.config)
    else:
        # 未指定配置文件时，必须提供 spec_name 和 cfg_path
        if not args.spec_name:
            print("错误: 未指定 -c 时，--spec-name 为必选参数", file=sys.stderr)
            sys.exit(1)
        if not args.cfg_path:
            print("错误: 未指定 -c 时，--cfg-path 为必选参数", file=sys.stderr)
            sys.exit(1)
        config = {}

    # 枚举参数转换（仅在显式指定时）
    spec_name = parse_enum("spec_name", args.spec_name) if args.spec_name else None
    tune_type = parse_enum("tune_type", args.tune_type) if "tune_type" in explicit else None
    input_type = parse_enum("input_type", args.input_type) if "input_type" in explicit else None
    spec_mode = parse_enum("spec_mode", args.spec_mode) if "spec_mode" in explicit else None
    run_mode = parse_enum("run_mode", args.run_mode) if "run_mode" in explicit else None

    # 构建 task 配置，仅用显式指定的命令行参数覆盖配置文件
    task_config = config.get("task", {})
    if "pack_name" in explicit:
        task_config["pack_name"] = args.pack_name
    if "setup_spec" in explicit:
        task_config["setup_spec"] = args.setup_spec
    if "pack_binaries" in explicit:
        task_config["pack_binaries"] = args.pack_binaries
    if "pack_benches" in explicit:
        task_config["pack_benches"] = args.pack_benches
    if "pack_builds" in explicit:
        task_config["pack_builds"] = args.pack_builds
    if run_mode is not None:
        task_config["run_mode"] = run_mode

    # 构建 spec_config 配置，仅用显式指定的命令行参数覆盖配置文件
    spec_config = config.get("spec_config", {})
    if args.cfg_path:
        spec_config["spec_cfg_path"] = args.cfg_path
    if spec_name is not None:
        spec_config["spec_name"] = spec_name
    if tune_type is not None:
        spec_config["tune_type"] = tune_type
    if input_type is not None:
        spec_config["input_type"] = input_type
    if spec_mode is not None:
        spec_config["spec_mode"] = spec_mode
    if "spec_benches" in explicit:
        spec_config["spec_benches"] = args.spec_benches
    if "iterations" in explicit:
        spec_config["iterations"] = args.iterations
    if "rebuild" in explicit:
        spec_config["rebuild"] = args.rebuild

    # 构建 pack_config 配置，仅用显式指定的命令行参数覆盖配置文件
    pack_config = config.get("pack_config", {})
    if "test_core_num" in explicit:
        pack_config["test_core_num"] = args.test_core_num
    if "test_clock_rate" in explicit:
        pack_config["test_clock_rate"] = args.test_clock_rate
    if "profile_gen" in explicit:
        pack_config["profile_gen"] = args.profile_gen
    if "auto_mode" in explicit:
        pack_config["auto_mode"] = args.auto_mode
    if "verify_mode" in explicit:
        pack_config["verify_mode"] = args.verify_mode
    if "minimal_mode" in explicit:
        pack_config["minimal_mode"] = args.minimal_mode
    if "allow_basepeak" in explicit:
        pack_config["allow_basepeak"] = args.allow_basepeak
    if "qemu_verify_parallel_jobs" in explicit:
        pack_config["qemu_verify_parallel_jobs"] = args.qemu_verify_parallel_jobs
    if "report_format" in explicit:
        pack_config["report_format"] = args.report_format

    # 构建 msg_config 配置，仅用显式指定的命令行参数覆盖配置文件
    msg_config = config.get("msg_config", {})
    if "enable_dingtalk_message" in explicit:
        msg_config["enable_dingtalk_message"] = args.enable_dingtalk_message
    if "log_language" in explicit:
        msg_config["log_language"] = args.log_language

    # 组装完整配置
    config["task"] = task_config
    config["spec_config"] = spec_config
    config["pack_config"] = pack_config
    config["msg_config"] = msg_config

    return config


def main():
    """
    PackSPEC 命令行主入口函数

    解析命令行参数，构建配置字典，创建 PackSPEC 实例并运行。
    异常处理：
    - PackSPECError: 以异常的 code 属性值退出
    - KeyboardInterrupt: 以退出码 130 退出
    """
    parser = build_arg_parser()
    args = parser.parse_args()
    config = build_config(parser, args)

    try:
        packer = PackSPEC(config)
        packer.run()
    except PackSPECError as e:
        print(f"PackSPEC 错误: {e.message}", file=sys.stderr)
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("\n用户中断执行", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
