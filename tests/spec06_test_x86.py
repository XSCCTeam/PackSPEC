import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pack_spec.pack_spec import PackSPEC
from src.pack_spec.pack_config import SPECName, TuneType, InputType, SPECMode

if __name__ == "__main__":
    """
    SPEC基准测试打包工具主程序
    
    示例：打包SPEC2006整数基准测试套件
    """
    
    config = {
        "pack_name": "x86_llvm19_novec_wll",
        "spec_cfg_path": "/home/wll/BOSC/speccpu2006-v1.0.1/config/x86_llvm19_novec_wll.cfg",
        "spec_config": {
            "spec_name": SPECName.spec2006,
            "tune_type": TuneType.base,
            "input_type": InputType.test,
            "spec_mode": SPECMode.speed,
            "spec_benches": "all",
            "iterations": 1,
            "rebuild": False,
        },
        "pack_config": {
            "test_core_num": 4,
            "test_clock_rate": 1,
            "profile_gen": False,
            "auto_mode": True,
            "host_mode": False,
        },
    }

    packer = PackSPEC(config)

    # packer.setup_spec()

    packer.pack_binaries()

    packer.pack_benches_cfg()
