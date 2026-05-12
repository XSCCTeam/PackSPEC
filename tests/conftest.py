"""
PackSPEC 单元测试公共 fixtures
"""

import os
import sys
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pack_spec.pack_config import (
    SPECName, TuneType, InputType, SPECMode, DEFAULT_CORE_NUM, DEFAULT_CLOCK_RATE, DEFAULT_PROFILE_GEN, DEFAULT_VERIFY_MODE, DEFAULT_MINIMAL_MODE, DEFAULT_RUN_MODE,
    DEFAULT_REPORT_FORMAT,
)


@pytest.fixture
def base_config():
    """基础测试配置字典"""
    return {
        "task": {
            "pack_name": "test_pack",
            "setup_spec": False,
            "pack_binaries": True,
            "pack_benches": True,
        },
        "spec_config": {
            "spec_cfg_path": "/tmp/test/spec.cfg",
            "spec_name": SPECName.spec2006,
            "tune_type": TuneType.base,
            "input_type": InputType.test,
            "spec_mode": SPECMode.speed,
            "spec_benches": "all",
            "iterations": 1,
            "rebuild": False,
        },
        "pack_config": {
            "test_core_num": DEFAULT_CORE_NUM,
            "test_clock_rate": DEFAULT_CLOCK_RATE,
            "profile_gen": DEFAULT_PROFILE_GEN,
            "auto_mode": True,
            "verify_mode": DEFAULT_VERIFY_MODE,
            "minimal_mode": DEFAULT_MINIMAL_MODE,
            "run_mode": DEFAULT_RUN_MODE,
            "report_format": DEFAULT_REPORT_FORMAT,
        },
        "msg_config": {
            "enable_dingtalk_message": False,
            "log_language": "zh",
        },
    }


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    dir_path = tempfile.mkdtemp(prefix="packspec_test_")
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


@pytest.fixture
def temp_file(temp_dir):
    """临时文件 fixture"""
    file_path = os.path.join(temp_dir, "test_file.txt")
    with open(file_path, "w") as f:
        f.write("test content")
    return file_path


@pytest.fixture
def spec_bench_map():
    """SPEC2006 基准测试二进制文件映射"""
    return {
        "400.perlbench": "perlbench",
        "401.bzip2": "bzip2",
        "403.gcc": "gcc",
        "429.mcf": "mcf",
        "445.gobmk": "gobmk",
        "456.hmmer": "hmmer",
        "458.sjeng": "sjeng",
        "462.libquantum": "libquantum",
        "464.h264ref": "h264ref",
        "471.omnetpp": "omnetpp",
        "473.astar": "astar",
        "483.xalancbmk": "xalancbmk",
        "433.milc": "milc",
        "434.zeusmp": "zeusmp",
        "435.gromacs": "gromacs",
        "436.cactusADM": "cactusADM",
        "437.leslie3d": "leslie3d",
        "444.namd": "namd",
        "447.dealII": "dealII",
        "450.soplex": "soplex",
        "453.povray": "povray",
        "454.calculix": "calculix",
        "459.GemsFDTD": "GemsFDTD",
        "465.tonto": "tonto",
        "470.lbm": "lbm",
        "481.wrf": "wrf",
        "482.sphinx3": "sphinx3",
    }
