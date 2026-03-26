"""
PackSPEC - SPEC CPU 基准测试打包工具

本模块提供 SPEC CPU 基准测试的自动化打包功能，支持 SPEC2006 和 SPEC2017 版本。
"""

from src.pack_spec.pack_spec import PackSPEC
from src.pack_spec.pack_config import (
    SPECName,
    TuneType,
    InputType,
    SPECMode,
    ActionType,
    PACKMode,
    PackSPECError,
    ConfigError,
    FileOperationError,
    CommandExecutionError,
    BenchmarkError,
)
from src.pack_spec.pack_utils import (
    load_pack_spec_cfg,
    save_pack_spec_cfg,
)

__all__ = [
    'PackSPEC',
    'SPECName',
    'TuneType',
    'InputType',
    'SPECMode',
    'ActionType',
    'PACKMode',
    'PackSPECError',
    'ConfigError',
    'FileOperationError',
    'CommandExecutionError',
    'BenchmarkError',
    'load_pack_spec_cfg',
    'save_pack_spec_cfg',
]

__version__ = '0.1.0'
