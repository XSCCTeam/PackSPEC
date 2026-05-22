# 为项目增加 SPEC CPU 2026 支持

  ## Summary

  - 现有项目把 SPEC CPU 2006 作为 runspec/ext/benchspec/CPU2006 体系处理，把 SPEC CPU 2017 作
    为 runcpu/label/benchspec/CPU 体系处理，但 2017 driver 当前只覆盖 speed benchmark 列表。
  - SPEC CPU 2026 与 2017 更接近：使用 runcpu、label、benchspec/CPU、refspeed/refrate 输入目
    录；主要差异是 benchmark 集合换成 7xx/8xx，且有部分 benchmark 需要多个可执行文件。
  - 新增 spec2026 支持时采用独立 SPEC2026Driver，不顺带改动 2017 既有行为，避免扩大回归面。参
    考官方文档：https://www.spec.org/cpu2026/Docs/ 、https://www.spec.org/cpu2017/Docs/ 、
    https://www.spec.org/cpu2006/Docs/

  ## Key Changes

  - 配置与注册：
      - 在 SPECName 增加 spec2026，新增 SPEC2026_PATH、SPEC2026_BENCH_PATH、
        SPEC2026_CONFIG_PATH，bench 路径兼容 benchspec/CPU2026 与 benchspec/CPU。
      - 在 driver registry 和包初始化中注册 SPEC2026Driver，让 PackSPEC、JSON enum decode、
        CLI 都能使用 spec2026。
      - analyze_spec_config() 对 spec2026 使用 label，_check_spec_environment() 使用 bin/
        runcpu。
  - SPEC2026 driver：
      - 新建 src/pack_spec/spec_2026_driver.py，实现 4 个 suite：intspeed、fpspeed、intrate、
        fprate；默认排除 998.specrand_s 和 999.specrand_r。
      - SPECMode.speed 下 all/int/fp 映射到 speed benchmark，SPECMode.rate 下映射到 rate
        benchmark；精确编号或完整 benchmark 名只匹配当前 mode。
      - get_ref_time() 从 data/refspeed/reftime 或 data/refrate/reftime 读取第三列时间；test/
        train 仍读取对应输入目录。
      - build/run 目录规则沿用 2017 风格：build_{tune}_{label}、run_{tune}_refspeed_{label}、
        run_{tune}_refrate_{label}。
      - run 命令使用 runcpu -c <cfg> --tune --size --iterations --noreportable；rate/speed 由
        benchmark suite 选择表达，不再为 2026 追加旧式 --rate。
  - 工具链适配：
      - PackUtils.parse_spec_results() 不再只识别 4xx/6xx benchmark，改为按已知 SPEC
        benchmark 集合识别 2006/2017/2026。
      - calculate_spec_score() 增加 2026 int/fp 集合，按已有几何平均逻辑计算。
      - 二进制处理支持单 executable 与多 executable：如 827.cppcheck_s、735.gem5_r、
      - 新增 scripts/setup-spec26.sh，接口与现有 setup-spec17.sh 保持一致，默认 setup
        intspeed fpspeed。
  - CLI 与文档：
      - run-cli.py 增加 spec2026 choice 与 enum 映射。
      - .env.example、README、示例配置和扩展文档补充 SPEC2026_PATH、spec2026 示例、benchmark
        mode 说明。

  ## Test Plan

  - 新增 tests/test_spec_2026_driver_dry.py：
      - 验证 speed all/int/fp 数量分别为 26/13/13，rate 为 26/14/12。
      - 验证 801.xz_s 只在 speed 可选，706.stockfish_r 只在 rate 可选。
      - 验证 refspeed/refrate/test/train reftime 解析。
      - 验证 run 命令使用 runcpu 且不包含 --rate。
      - 验证多二进制 benchmark 的 binary map。
  - 扩展现有测试：
      - driver registry、CLI parse、enum encode/decode、version tag、score calculation、
        result parsing、binary copy/QEMU command helper。
  - 执行完整 pytest。当前改动前基线已验证：280 passed in 0.23s。

  ## Assumptions

  - 不在本次变更中修正 SPEC2017 rate benchmark 列表只覆盖 speed benchmark 的既有行为；2026 新
    driver 会按 mode 正确选择 speed/rate。
  - CPU2026 的 copies、threads 继续由 SPEC config 文件控制，本项目只负责选择 suite、setup/
    run、解析和打包。
  - 本地已有 spec_env/setup_spec2026env.sh 且当前为 dirty 状态；实现时不覆盖它，只补项目
    runtime 支持。