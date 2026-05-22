"""
PackSPEC - SPEC CPU 基准测试自动化打包与运行工具
PackSPEC - Automated SPEC CPU Benchmark Packaging and Execution Tool

本模块提供 SPEC CPU 基准测试的自动化打包和运行功能，支持 SPEC2006 和 SPEC2017 版本。
This module provides automated packaging and execution for SPEC CPU benchmarks,
supporting both SPEC2006 and SPEC2017 versions.

主要功能 / Key Features:
- 打包模式 (pack): 将 SPEC 测试打包为可独立运行的文件集
- 直接运行模式 (direct): 直接调用 runspec/runcpu 命令执行测试并生成报告
- QEMU 验证模式 (verify): 通过 QEMU 模拟器验证编译出的二进制文件正确性
- 极简模式 (minimal): 生成 POSIX 兼容脚本，适用于嵌入式系统
- Profile 生成模式 (PGO): 支持 Profile Guided Optimization 工作流
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
    DEFAULT_MINIMAL_MODE,
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

from src.pack_spec import spec_2006_driver, spec_2017_driver

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
    'DEFAULT_MINIMAL_MODE',
    'load_pack_spec_cfg',
    'save_pack_spec_cfg',
    'parse_spec_results',
    'generate_json_report',
    'generate_markdown_report',
    'generate_qemu_verify_script',
    'generate_qemu_verify_all_script',
]

__version__ = '0.3.0'
