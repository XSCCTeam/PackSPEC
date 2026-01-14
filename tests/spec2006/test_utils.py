import os
import subprocess

# 执行set_test_env.sh脚本获取环境变量
script_dir = os.path.dirname(os.path.abspath(__file__))
env_script_path = os.path.join(script_dir, 'set_test_env.sh')

# 执行shell脚本并获取环境变量
def execute_env_script(script_path):
    """
    执行shell脚本并获取设置的环境变量
    
    Args:
        script_path (str): shell脚本路径
    
    Returns:
        dict: 脚本中设置的环境变量
    """
    # 确保脚本存在
    if not os.path.exists(script_path):
        print(f"警告: 环境变量脚本 {script_path} 不存在")
        return {}
    
    # 执行脚本并获取输出
    cmd = f"bash -c 'source {script_path} && env'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"执行脚本 {script_path} 失败: {result.stderr}")
        return {}
    
    # 解析环境变量
    env_vars = {}
    for line in result.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            env_vars[key] = value
    
    return env_vars

# 执行脚本获取环境变量
print(f"执行环境变量脚本: {env_script_path}")
env_vars = execute_env_script(env_script_path)

# 设置环境变量
for key in ['SPEC_TEST_CFG_PATH', 'SPEC_TEST_2006_INSTALL_PATH', 'SPEC_TEST_SETUPLOG_PATH', 'SPEC_TEST_GENERATED_PATH']:
    if key in env_vars:
        os.environ[key] = env_vars[key]
        print(f"设置环境变量 {key} = {env_vars[key]}")
    else:
        print(f"警告: 未从脚本获取到环境变量 {key}")

# 从环境变量获取测试配置路径
SPEC_TEST_CFG_PATH = os.environ.get('SPEC_TEST_CFG_PATH')
SPEC_TEST_2006_INSTALL_PATH = os.environ.get('SPEC_TEST_2006_INSTALL_PATH')
SPEC_TEST_SETUPLOG_PATH = os.environ.get('SPEC_TEST_SETUPLOG_PATH')
SPEC_TEST_GENERATED_PATH = os.environ.get('SPEC_TEST_GENERATED_PATH')
