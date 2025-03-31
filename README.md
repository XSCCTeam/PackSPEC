

# PackSPEC 项目

## 项目简介
PackSPEC 是一个用于打包和管理 SPEC 文件的工具。

## 主要功能
- 自动化打包 SPEC 文件
- 管理 SPEC 文件配置
- 提供便捷的脚本工具

## 安装步骤
1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置项目:
将 `config.py.example` 复制为 `config.py` 并编辑配置文件:
```bash
cp config.py.example config.py
# 然后编辑 config.py 文件配置您的 SPEC 路径等信息
```

## 使用说明
运行主程序:
```bash
python pack_spec.py
```
