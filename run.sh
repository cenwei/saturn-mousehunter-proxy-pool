#!/bin/bash
# Saturn MouseHunter Proxy Pool 启动脚本

# 设置项目根目录
PROJECT_ROOT="/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-proxy-pool"
cd "$PROJECT_ROOT"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# 启动应用
python src/main.py