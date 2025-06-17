from pack_spec.pack_spec import *

if __name__ == "__main__":
    """
    SPEC基准测试打包工具主程序
    
    示例：打包SPEC2006整数基准测试套件
    """
    
    # 创建SPEC2006整数基准测试打包实例
    packer = PackSPEC(
        # SPEC基准测试版本选择
        # 可选值：
        #   SPECName.spec2006: SPEC2006基准套件
        #   SPECName.spec2017: SPEC2017基准套件
        spec_name=SPECName.spec2017,
        
        # 选择SPEC基准测试子集
        # 格式：空格分隔的基准测试名称或子集标识
        # 可用子集标识：
        #   "all": 完整基准套件
        #   "int": 仅整数基准测试
        #   "fp":  仅浮点基准测试
        # 示例：
        #   "int" - 打包所有整数基准测试
        #   "401 403" - 打包指定基准测试
        spec_benches="all",
        
        # SPEC基准测试优化级别
        # 可选值：
        #   TuneType.base: 基础优化级别
        #   TuneType.peak: 峰值优化级别
        #   TuneType.all:  同时包含base和peak
        tune_type=TuneType.base,
        
        # SPEC基准测试输入数据集类型
        # 可选值：
        #   InputType.test:  测试输入数据集(最小)
        #   InputType.train: 训练输入数据集(中等)
        #   InputType.ref:   参考输入数据集(最大)
        #   InputType.all:   包含所有输入数据集
        input_type=InputType.ref,

        # SPEC基准测试运行模式
        # 可选值：
        #   SPECMode.speed: 运行速度测试
        #   SPECMode.rate: 运行吞吐测试
        spec_mode=SPECMode.speed,
        
        # 运行测试的迭代次数
        # 主要用于生成运行脚本，不影响二进制打包
        iterations=3,
        
        # 测试运行绑定的核心编号, 不设置则不绑定
        # 仅在生成运行脚本时生效，不影响二进制打包
        test_core_num=4,

        # # 测试运行的 CPU 主频，用于算分，单位 GHz
        # # 仅在生成运行脚本时生效，不影响二进制打包
        # test_clock_rate=1,

        # # 是否以生成 profile 模式运行，默认为 False
        # # profile 生成模式只跑一次程序，iterations 将强制设置为 1
        # profile_gen=True,

        # # 是否以自动模式运行, 用于配合其他脚本执行, 默认为 False
        # # 如果为 True, 程序将自动覆盖已存在的文件，无需用户确认
        # # 且生成的打包目录会以极简目录形式生成，且不包含日期
        # auto_mode=False,

        # 是否以HOST模式运行，默认为 False
        # 仅在打包SPEC2017基准测试625.x264_s的时生效
        # HOST模式下，打包SPEC2017的625.x264_s的例子将不会单独生成input
        # host_mode=False,
    )

    # SPEC config file name
    spec_config = "x86_llvm19_novec.cfg"

    # 使用spec进行编译并设置好运行目录
    packer.setup_spec(spec_config)