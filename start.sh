#!/bin/bash

# 代理池微服务启动脚本
# 在微服务目录内运行，不污染workspace

set -e

echo "🚀 代理池微服务"
echo "================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查是否在正确目录
if [[ ! -f "src/main.py" ]]; then
    echo -e "${RED}❌ 请在代理池微服务目录内运行此脚本${NC}"
    echo "正确路径: saturn-mousehunter-proxy-pool/"
    exit 1
fi

# 检查uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv 未安装${NC}"
    exit 1
fi

# 设置默认环境变量
export ENVIRONMENT=${ENVIRONMENT:-development}
export MARKETS=${MARKETS:-cn,hk,us}
export PORT=${PORT:-8005}

echo -e "${YELLOW}配置信息:${NC}"
echo "  环境: $ENVIRONMENT"
echo "  市场: $MARKETS"
echo "  端口: $PORT"
echo "================"

# 启动服务
echo -e "${GREEN}启动代理池微服务...${NC}"
uv run python start_service.py
