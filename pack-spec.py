from config import *
from enum import Enum
import shutil
import os
import subprocess

class ActionType(Enum):
    build = 1
    run = 2

class TuneType(Enum):
    base = 1
    peak = 2

class InputType(Enum):
    test = 1
    train = 2
    ref = 3


def get_bench_path(action_type: ActionType, tune_type: TuneType, input_type: InputType, label: str) -> list:
    """获取指定配置的SPEC基准测试路径
    
    根据给定的动作类型、优化类型、输入类型和标签，在SPEC目录中查找匹配的基准测试目录。
    如果找到多个匹配的目录，会选择编号最大的那个（最新的）。
    
    Args:
        action_type: 动作类型（build：编译目录，run：运行目录）
        tune_type: 优化类型（如base）
        input_type: 输入类型（如test），仅在action_type为run时使用
        label: 标签（如llvm19-m64）
    
    Returns:
        list: 返回符合条件的基准测试路径列表
    """
    # 根据动作类型构建目录前缀
    if action_type == ActionType.build:
        # 编译目录格式：build_优化类型_标签
        bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{label}"
    elif action_type == ActionType.run:
        # 运行目录格式：run_优化类型_输入类型_标签
        bench_dir_perfix = f"{action_type.name}_{tune_type.name}_{input_type.name}_{label}"

    selected_bench_dir = []
    
    # 遍历SPEC2017基准测试目录
    for bench_dir in os.listdir(SPEC2017_BENCH_PATH):
        # 检查是否为指定的基准测试集合
        if bench_dir in SPEC2017_BENCHES:
            # 根据动作类型构建完整路径（build或run目录）
            bench_run_dir = os.path.join(SPEC2017_BENCH_PATH, bench_dir, action_type.name)
            run_dir_path_list = []
            
            # 查找符合前缀的目录
            for run_dir in os.listdir(bench_run_dir):
                if run_dir.startswith(bench_dir_perfix):
                    run_dir_path_list.append(os.path.join(bench_run_dir, run_dir))
                    
            # 处理查找结果
            if len(run_dir_path_list) == 0:
                # 未找到符合条件的目录
                logger.warning(f"Bench{os.path.basename(bench_dir)} not found in {bench_dir_perfix}.")
            elif len(run_dir_path_list) > 1:
                # 找到多个符合条件的目录，选择编号最大的那个（最新的）
                logger.warning(f"Bench{os.path.basename(bench_dir)} found in more than one {bench_dir_perfix}.")
                max = 0
                selected = run_dir_path_list[0]
                for run_dir_perfix in run_dir_path_list:
                    # 检查目录名末尾是否为数字，如果是则比较大小
                    if run_dir_perfix.split(".")[-1].isnumeric():
                        if int(run_dir_perfix.split(".")[-1]) > max:
                            max = int(run_dir_perfix.split(".")[-1])
                            selected = run_dir_perfix
                selected_bench_dir.append(selected)
                logger.info(f"Bench {os.path.basename(bench_dir)} using {selected}")
            else:
                # 只找到一个符合条件的目录
                selected_bench_dir.append(run_dir_path_list[0])
                logger.info(f"Bench {os.path.basename(bench_dir)} using {run_dir_path_list[0]}")
        else:
            # 不在指定的基准测试集合中，跳过
            logger.debug(f"bench_dir: {bench_dir} not included.")

    return selected_bench_dir

def copy_bench(selected_bench_dir, pack_spec_dir, input_type: InputType):
    """复制基准测试目录并生成运行脚本
    
    将选中的基准测试目录复制到打包目录，并为每个基准测试生成运行脚本。
    
    Args:
        selected_bench_dir: 源基准测试目录列表
        pack_spec_dir: 打包目标目录
        input_type: 输入类型，用于生成运行脚本
    
    Returns:
        list: 返回打包后的基准测试目录列表
    """
    # 复制选中的基准测试目录到打包目录
    dest_dir_list = []
    for src_dir in selected_bench_dir:
        # 获取基准测试名称（目录的最后两级：如 500.perlbench_r/run_base_test_llvm19-m64）
        bench_name = os.path.basename(os.path.dirname(os.path.dirname(src_dir)))
        dest_dir = os.path.join(pack_spec_dir, bench_name)
        
        logger.info(f"Copying {bench_name}\n\tFrom {src_dir} -to-> {dest_dir}")
        try:
            shutil.copytree(src_dir, dest_dir, symlinks=True)
            logger.info(f"Successfully copied {bench_name}")
            dest_dir_list.append(dest_dir)
        except Exception as e:
            logger.error(f"Failed to copy {bench_name}: {str(e)}")
            continue

        # 执行specinvoke命令并生成run_test.sh
        if execute_specinvoke(src_dir, dest_dir, input_type):
            logger.info(f"Successfully generated run_test.sh in {dest_dir}")
        else:
            logger.error(f"Failed to generate run_test.sh in {dest_dir}")

    return dest_dir_list

def execute_specinvoke(src_dir: str, dest_dir: str, input_type: InputType) -> bool:
    """生成基准测试的运行脚本
    
    使用specinvoke命令生成运行脚本，并处理路径替换。
    
    Args:
        src_dir: 源基准测试目录
        dest_dir: 目标基准测试目录
        input_type: 输入类型
    
    Returns:
        bool: 是否成功生成运行脚本
    """
    specinvoke = os.path.join(SPEC2017_PATH, "bin", "specinvoke")
    specinvoke_cmd = f"{specinvoke} -nn speccmds.cmd"

    src_dir_name = os.path.basename(src_dir)
    dest_dir_name = os.path.basename(dest_dir)

    try:
        # 切换到目标目录
        logger.info(f"Changing directory to {dest_dir}")
        
        # 执行specinvoke命令并捕获输出
        logger.info(f"Executing command: {specinvoke_cmd}")
        result = subprocess.run(
            specinvoke_cmd.split(),
            cwd=dest_dir,
            capture_output=True,
            text=True,
            check=True
        )

        # 处理命令输出
        commands = result.stdout.split("\n")
        start_index = -1
        
        # 查找第一次出现"# Starting run"的行
        for i, line in enumerate(commands):
            if line.strip().startswith("# Starting run"):
                start_index = i
                break
        
        # 如果找到了起始行，只保留该行及其后面的内容
        if start_index != -1:
            commands = commands[start_index:]
        else:
            logger.warning("No '# Starting run' found in command output")

        # 替换路径和目录名
        processed_commands = []
        for line in commands:
            # 替换完整路径
            line = line.replace(src_dir, dest_dir)
            # 替换目录名
            line = line.replace(f"/{src_dir_name}/", f"/{dest_dir_name}/")
            if not line.startswith("specinvoke"):
                processed_commands.append(line)
        
        # 将输出写入run.sh文件
        output_file = os.path.join(dest_dir, f"run_{input_type.name}.sh")
        with open(output_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("\n".join(processed_commands))  # 将处理后的命令写入文件
        
        # 添加执行权限
        os.chmod(output_file, 0o755)
        
        logger.info(f"Successfully created {output_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to execute command: {str(e)}")
        return False

def create_run_all_script(packed_bench_dir_list: list, input_type: InputType):
    """创建运行所有基准测试的批处理脚本
    
    生成一个shell脚本，用于按顺序运行所有基准测试并记录运行时间。
    脚本会记录每个基准测试的开始时间、结束时间和运行时长，
    所有输出都会被记录到run_all.log文件中。
    
    Args:
        packed_bench_dir_list: 打包后的基准测试目录列表
        input_type: 输入类型，用于确定运行哪个脚本（如run_test.sh）
    """
    if not packed_bench_dir_list:
        logger.warning("No benchmark directories to run")
        return
        
    # 获取父目录
    parent_dir = os.path.dirname(packed_bench_dir_list[0])
    run_all_script = os.path.join(parent_dir, "run_all.sh")
    
    script_content = [
        "#!/bin/bash",
        "",
        "# 获取脚本所在目录的绝对路径",
        "SCRIPT_DIR=$(pwd)",
        "LOG_FILE=\"$SCRIPT_DIR/run_all.log\"",
        "CORE_NUM=0",
        "",
        "# 运行所有基准测试并记录时间",
        "echo \"Starting benchmarks run at $(date)\" > \"$LOG_FILE\"",
        "",
        "ulimit -s unlimited",
        "",
        "# 运行每个基准测试",
    ]
    
    for bench_dir in packed_bench_dir_list:
        bench_name = os.path.basename(bench_dir)
        
        script_content.extend([
            f"echo -e '\\nRunning {bench_name}...' | tee -a \"$LOG_FILE\"",
            f"cd {bench_name}",
            f"(time -p taskset -c $CORE_NUM bash run_{input_type.name}.sh) 2>&1 | tee -a \"$LOG_FILE\"",
            f"echo -e '{bench_name} completed ' | tee -a \"$LOG_FILE\"",
            "cd \"$SCRIPT_DIR\"",
            ""
        ])
    
    script_content.extend([
        "echo -e '\\nAll benchmarks completed' | tee -a \"$LOG_FILE\"",
        "echo \"Finished at $(date)\" >> \"$LOG_FILE\""
    ])
    
    # 写入脚本文件
    with open(run_all_script, 'w') as f:
        f.write("\n".join(script_content))
    
    # 添加执行权限
    os.chmod(run_all_script, 0o755)
    logger.info(f"Created run_all script at {run_all_script}")

def copy_analyze_log(pack_spec_dir: str):
    logger.info(f"Copying analyze_log.py\n\tFrom {P_PATH} -to-> {pack_spec_dir}")
    try:
        shutil.copy(os.path.join(P_PATH, "analyze_log.py"), pack_spec_dir)
        logger.info(f"Successfully copied analyze_log.py")
    except Exception as e:
        logger.error(f"Failed to copy analyze_log.py: {str(e)}")

if __name__ == "__main__":
    logger.info("PackSPEC Started")

    label = "llvm19-m64"

    selected_bench_dir = get_bench_path(ActionType.run, TuneType.base, InputType.test, label)
    
    os.makedirs(PACK_PATH, exist_ok=True)
    pack_spec_dir = os.path.join(PACK_PATH, f"run_{label}")
    os.makedirs(pack_spec_dir, exist_ok=False)

    packed_bench_dir_list = copy_bench(selected_bench_dir, pack_spec_dir, InputType.test)
    
    create_run_all_script(packed_bench_dir_list, InputType.test)

    copy_analyze_log(pack_spec_dir)
    
    logger.info("Finished packing SPEC benchmarks")
