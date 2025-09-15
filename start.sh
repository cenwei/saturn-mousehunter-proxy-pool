#!/bin/bash

# Saturn MouseHunter 代理池服务启动脚本
# 支持多环境配置

set -e

echo "🚀 启动 Saturn MouseHunter 代理池服务"
echo "========================================"

# 默认配置
DEFAULT_ENVIRONMENT="development"
DEFAULT_MARKETS="cn,hk,us"  # 默认启动所有主要市场

# 读取环境变量
ENVIRONMENT=${ENVIRONMENT:-$DEFAULT_ENVIRONMENT}
MARKETS=${MARKETS:-$DEFAULT_MARKETS}

echo "环境: $ENVIRONMENT"
echo "市场: $MARKETS (支持: cn=中国A股, hk=香港股市, us=美股)"

# 根据环境显示配置信息
case $ENVIRONMENT in
    "development"|"dev")
        echo "📍 开发环境配置:"
        echo "   地址: 192.168.8.168:8005"
        echo "   管理界面: http://192.168.8.168:8005"
        echo "   API文档: http://192.168.8.168:8005/docs"
        ;;
    "testing"|"test")
        echo "📍 测试环境配置:"
        echo "   地址: test-proxy-pool:8005"
        echo "   管理界面: http://test-proxy-pool:8005"
        echo "   API文档: http://test-proxy-pool:8005/docs"
        ;;
    "production"|"prod")
        echo "📍 生产环境配置:"
        echo "   地址: proxy-pool.saturn-mousehunter.internal:8005"
        echo "   管理界面: http://proxy-pool.saturn-mousehunter.internal:8005"
        echo "   API文档: http://proxy-pool.saturn-mousehunter.internal:8005/docs"
        ;;
    *)
        echo "⚠️  未知环境: $ENVIRONMENT，使用开发环境配置"
        ENVIRONMENT="development"
        ;;
esac

echo ""
echo "🔧 启动参数:"
echo "   ENVIRONMENT=$ENVIRONMENT"
echo "   MARKETS=$MARKETS"

# 检查依赖
echo ""
echo "🔍 检查依赖..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到"
    exit 1
fi

# 启动服务
echo ""
echo "🚀 启动服务..."

cd "$(dirname "$0")"

# 导出环境变量
export ENVIRONMENT
export MARKETS

# 启动
exec python3 src/main.py
