"""
PackSPEC - SPEC CPU 基准测试打包工具

本模块提供 SPEC CPU 基准测试的自动化打包功能，支持 SPEC2006 和 SPEC2017 版本。
支持两种运行模式：
- 打包模式 (pack): 将 SPEC 测试打包为可独立运行的文件集
- 直接运行模式 (direct): 直接调用 runspec/runcpu 命令执行测试
"""

from src.pack_spec.pack_spec import PackSPEC
from src.pack_spec.pack_config import (
    SPECName,
    TuneType,
    InputType,
    SPECMode,
    ActionType,
    PACKMode,
    RunMode,
    PackSPECError,
    ConfigError,
    FileOperationError,
    CommandExecutionError,
    BenchmarkError,
    QEMU_PATH,
    QEMU_CMD,
)
from src.pack_spec.pack_utils import (
    load_pack_spec_cfg,
    save_pack_spec_cfg,
    parse_spec_results,
    generate_json_report,
    generate_markdown_report,
    generate_qemu_verify_script,
    generate_qemu_verify_all_script,
)

__all__ = [
    'PackSPEC',
    'SPECName',
    'TuneType',
    'InputType',
    'SPECMode',
    'ActionType',
    'PACKMode',
    'RunMode',
    'PackSPECError',
    'ConfigError',
    'FileOperationError',
    'CommandExecutionError',
    'BenchmarkError',
    'QEMU_PATH',
    'QEMU_CMD',
    'load_pack_spec_cfg',
    'save_pack_spec_cfg',
    'parse_spec_results',
    'generate_json_report',
    'generate_markdown_report',
    'generate_qemu_verify_script',
    'generate_qemu_verify_all_script',
]

__version__ = '0.1.0'
