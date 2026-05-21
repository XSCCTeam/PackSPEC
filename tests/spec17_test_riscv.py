import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pack_spec.pack_spec import PackSPEC
from src.pack_spec.pack_config import SPECName, TuneType, InputType, SPECMode, RunMode

if __name__ == "__main__":
    """
    SPEC基准测试打包工具主程序
    
    示例：打包SPEC2017整数基准测试套件
    """
    
    config = {
        # 任务配置
        "task": {
            # 打包任务名称
            "pack_name": "riscv_llvm22_novec_wll",

            # 是否setup SPEC CPU 2006/2017
            # 也就是是否编译SPEC基准测试，默认为 False
            "setup_spec": True,

            # 是否打包二进制文件，默认为 False
            # 需要显式设置为 True 才会执行打包二进制操作
            "pack_binaries": True,

            # 是否打包完整测试环境，默认为 False
            # 需要显式设置为 True 才会执行打包测试环境操作
            # 包含输入数据集、运行脚本、验证脚本等
            "pack_benches": True,

            # 是否打包 build 和 run 目录，默认为 False
            # 需要显式设置为 True 才会执行打包 build 目录操作
            # 包含 build 和 run 的全部内容，合并到一个 build 目录
            # 输出目录结构为 generated_files/{pack_name}/build/spec2006_build_{pack_name}.xxx/
            "pack_builds": True,

            # 运行模式，默认为 RunMode.pack（打包模式）
            # 可选值：
            #   RunMode.pack: 打包模式，根据 task 配置执行打包操作
            #   RunMode.direct: 直接运行模式，直接运行 SPEC 测试，跳过打包操作
            # 当设置为 RunMode.direct 时，会调用 run_spec() 方法直接运行 SPEC 测试
            "run_mode": RunMode.pack,
        },
        # SPEC基准测试相关配置
        "spec_config": {
            # SPEC cfg 文件绝对路径
            # 注意：setup 操作前会自动将 cfg 文件复制到 generated_files/{pack_name}/cfg/ 目录
            # 以保护源配置文件不被修改
            # 日志文件会自动保存到 generated_files/{pack_name}/log/ 目录
            "spec_cfg_path": "/home/wll/sdbdata/pack_spec/tests/test_cfgs/spec17_riscv_llvm22_novec.cfg",

            # SPEC基准测试版本选择
            # 可选值：
            #   SPECName.spec2006: SPEC2006基准套件
            #   SPECName.spec2006v1p01: SPEC2006 v1.0.1基准套件
            #   SPECName.spec2017: SPEC2017基准套件
            "spec_name": SPECName.spec2017,

            # SPEC基准测试优化级别
            # 可选值：
            #   TuneType.base: 基础优化级别
            #   TuneType.peak: 峰值优化级别
            #   TuneType.all:  同时包含base和peak
            "tune_type": TuneType.base,

            # SPEC基准测试输入数据集类型
            # 可选值：
            #   InputType.test:  测试输入数据集(最小)
            #   InputType.train: 训练输入数据集(中等)
            #   InputType.ref:   参考输入数据集(最大)
            #   InputType.all:   包含所有输入数据集
            "input_type": InputType.ref,

            # SPEC基准测试运行模式
            # 可选值：
            #   SPECMode.speed: 运行速度测试
            #   SPECMode.rate: 运行吞吐测试
            "spec_mode": SPECMode.speed,

            # 选择SPEC基准测试子集
            # 格式：空格分隔的基准测试名称或子集标识
            # 可用子集标识：
            #   "all": 完整基准套件
            #   "int": 仅整数基准测试
            #   "fp":  仅浮点基准测试
            # 示例：
            #   "int" - 打包所有整数基准测试
            #   "401 403" - 打包指定基准测试
            "spec_benches": "all",

            # 运行测试的迭代次数
            # 主要用于生成运行脚本，不影响二进制打包
            "iterations": 1,

            # 是否重新构建基准测试，默认为 False
            # 如果为 True, 程序将在打包前重新构建基准测试
            "rebuild": False,
        },
        # PackSPEC打包相关配置
        "pack_config": {
            # 测试运行绑定的核心编号，设置为 -1 则不绑定
            # 仅在生成运行脚本时生效，不影响二进制打包
            "test_core_num": 4,

            # 测试运行的 CPU 主频，用于算分，单位 GHz
            # 仅在生成运行脚本时生效，不影响二进制打包
            "test_clock_rate": 1,

            # 是否以生成 profile 模式运行，默认为 False
            # profile 生成模式只跑一次程序，iterations 将强制设置为 1
            "profile_gen": False,

            # 是否以自动模式运行, 用于配合其他脚本执行, 默认为 False
            # 如果为 True, 程序将自动覆盖已存在的目录，无需用户确认
            # 且生成的打包目录和子目录不包含日期前缀
            # 如果为 False, 程序会在目录已存在时询问用户是否覆盖
            # 且生成的打包目录和子目录包含日期前缀
            "auto_mode": False,

            # 测试报告格式，默认为 json
            # 可选值：
            #   "json": JSON 格式报告
            #   "markdown": Markdown 格式报告
            # 仅在 run_mode 为 RunMode.direct 时生效
            "report_format": "json",

            # 是否开启QEMU验证模式，默认为 False
            # 开启后生成QEMU验证脚本
            # 用于验证编译出的二进制文件是否正确
            # 需要在 .env 中配置 QEMU_PATH 环境变量
            "verify_mode": False,

            # QEMU验证并行任务数，默认为 0（使用 CPU 核心数-2）
            # 用于并行执行多个测试子项，提高验证效率
            # 设置为 0 时自动使用系统 CPU 核心数-2，避免占用所有核心导致服务器卡死
            # 设置为 1 时串行执行
            "qemu_verify_parallel_jobs": 0,

            # 是否开启极简模式，默认为 False
            # 开启后生成的脚本使用 POSIX 兼容语法，降低对运行环境的要求
            # 适用于功能简单的嵌入式系统或最小化Linux环境
            # 极简模式下：
            # - 使用 #!/bin/sh 替代 #!/bin/bash
            # - 跳过 curl 检查和消息发送功能
            # - 使用 POSIX 兼容的循环语法
            "minimal_mode": False,

            # 是否允许basepeak配置，默认为 False
            # 当SPEC cfg文件中设置了 basepeak=yes 时，需要设置为 True 才允许继续
            # 否则会抛出 ConfigError 异常
            # basepeak=yes 表示使用base的二进制和/或结果用于peak
            # 详见: https://www.spec.org/cpu2006/Docs/config.html#basepeak
            "allow_basepeak": False,
        },
        # 消息发送相关配置
        "msg_config": {
            # 是否开启钉钉消息发送，默认为 False
            # 开启后会在测试完成后发送消息通知用户
            # 需要在 .env 中配置 BOSC_AT_USER、BOSC_AT_TOKEN、BOSC_MESSAGE_URL 环境变量
            "enable_dingtalk_message": True,

            # 日志输出语言，默认为 "zh"（中文）
            # 可选值：
            #   "zh" 或 "chinese": 中文输出
            #   "en" 或 "english": 英文输出
            "log_language": "cn",
        },
    }

    # 创建SPEC2006整数基准测试打包实例
    packer = PackSPEC(config)

    # 根据配置自动执行相应操作
    # run() 方法会根据配置自动调用相应的内部方法：
    # - 当 run_mode == RunMode.pack（默认）时：
    #   - 根据 task.setup_spec 配置决定是否调用 setup_spec()
    #   - 根据 task.pack_binaries 配置决定是否调用 pack_binaries()
    #   - 根据 task.pack_benches 配置决定是否调用 pack_benches_cfg()
    #   - 根据 pack_config.verify_mode 配置决定是否调用 pack_qemu_verify()
    # - 当 run_mode == RunMode.direct 时：
    #   - 调用 run_spec() 直接运行 SPEC 测试
    #   - 跳过所有打包相关操作
    packer.run()
