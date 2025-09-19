#!/bin/bash

# 代理池API测试脚本
# 测试所有接口并展示详细的JSON响应结构

BASE_URL="http://192.168.8.168:8001/api/v1"
MARKET="cn"
MODE="live"

echo "🚀 代理池API测试开始"
echo "基础URL: $BASE_URL"
echo "测试市场: $MARKET"
echo "测试模式: $MODE"
echo "=" * 60

# 颜色输出函数
print_section() {
    echo -e "\n\033[1;34m=== $1 ===\033[0m"
}

print_subsection() {
    echo -e "\033[1;32m--- $1 ---\033[0m"
}

print_request() {
    echo -e "\033[1;33m请求:\033[0m $1"
}

print_response() {
    echo -e "\033[1;36m响应:\033[0m"
}

# 1. 标准代理池接口测试
print_section "1. 标准代理池接口测试"

# 1.1 获取代理池状态
print_subsection "1.1 获取代理池状态"
print_request "GET /status?market=$MARKET&mode=$MODE"
curl -s -X GET "$BASE_URL/status?market=$MARKET&mode=$MODE" | jq '.' || echo '{"error": "接口不可用或返回非JSON格式"}'
echo

# 1.2 启动代理池服务
print_subsection "1.2 启动代理池服务"
print_request "POST /start?market=$MARKET&mode=$MODE"
curl -s -X POST "$BASE_URL/start?market=$MARKET&mode=$MODE" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 1.3 再次获取状态确认启动
print_subsection "1.3 确认服务启动状态"
curl -s -X GET "$BASE_URL/status?market=$MARKET&mode=$MODE" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 1.4 获取代理IP
print_subsection "1.4 获取代理IP"
print_request "POST /rpc - get_proxy"
curl -s -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"get_proxy\",\"proxy_type\":\"short\",\"market\":\"$MARKET\",\"mode\":\"$MODE\"}" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 1.5 报告代理失败 (使用虚拟IP)
print_subsection "1.5 报告代理失败"
print_request "POST /rpc - report_failure"
curl -s -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"report_failure\",\"proxy_addr\":\"192.168.1.100:8080\",\"market\":\"$MARKET\",\"mode\":\"$MODE\"}" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 1.6 获取RPC状态
print_subsection "1.6 获取RPC状态"
print_request "POST /rpc - get_status"
curl -s -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"get_status\",\"market\":\"$MARKET\",\"mode\":\"$MODE\"}" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 1.7 Ping测试
print_subsection "1.7 Ping测试"
print_request "POST /rpc - ping"
curl -s -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"ping\",\"market\":\"$MARKET\",\"mode\":\"$MODE\"}" | jq '.' || echo '{"error": "接口不可用"}'
echo

# 2. 增强交易日类型接口测试
print_section "2. 增强交易日类型接口测试"

# 2.1 获取交易日信息
print_subsection "2.1 获取交易日信息"
print_request "GET /enhanced/trading-day/$MARKET"
curl -s -X GET "$BASE_URL/enhanced/trading-day/$MARKET" | jq '.' || echo '{"error": "增强接口不可用"}'
echo

# 2.2 获取指定日期的交易日信息
print_subsection "2.2 获取指定日期交易日信息"
TEST_DATE="2024-12-24"  # 平安夜，可能的半日交易
print_request "GET /enhanced/trading-day/hk?date=$TEST_DATE"
curl -s -X GET "$BASE_URL/enhanced/trading-day/hk?date=$TEST_DATE" | jq '.' || echo '{"error": "增强接口不可用"}'
echo

# 2.3 获取市场实时状态
print_subsection "2.3 获取市场实时状态"
print_request "GET /enhanced/trading-day/$MARKET/status"
curl -s -X GET "$BASE_URL/enhanced/trading-day/$MARKET/status" | jq '.' || echo '{"error": "增强接口不可用"}'
echo

# 2.4 获取MACL交易日类型
print_subsection "2.4 获取MACL交易日类型"
print_request "GET /enhanced/macl/day-type/$MARKET"
curl -s -X GET "$BASE_URL/enhanced/macl/day-type/$MARKET" | jq '.' || echo '{"error": "增强接口不可用"}'
echo

# 2.5 获取所有市场交易总结
print_subsection "2.5 获取所有市场交易总结"
print_request "GET /enhanced/trading-modes/summary"
curl -s -X GET "$BASE_URL/enhanced/trading-modes/summary" | jq '.' || echo '{"error": "增强接口不可用"}'
echo

# 3. 调度器接口测试
print_section "3. 调度器接口测试"

# 3.1 获取增强调度器状态
print_subsection "3.1 获取增强调度器状态"
print_request "GET /enhanced/scheduler/status"
curl -s -X GET "$BASE_URL/enhanced/scheduler/status" | jq '.' || echo '{"error": "调度器接口不可用"}'
echo

# 3.2 强制启动市场 (增强版)
print_subsection "3.2 强制启动市场 (增强版)"
print_request "POST /enhanced/scheduler/force-start/$MARKET"
curl -s -X POST "$BASE_URL/enhanced/scheduler/force-start/$MARKET" | jq '.' || echo '{"error": "调度器接口不可用"}'
echo

# 4. 批量操作接口测试
print_section "4. 批量操作接口测试"

# 4.1 批量启动服务
print_subsection "4.1 批量启动服务"
print_request "POST /batch/start"
curl -s -X POST "$BASE_URL/batch/start" \
  -H "Content-Type: application/json" \
  -d "{\"markets\":[\"cn\",\"hk\"],\"mode\":\"live\"}" | jq '.' || echo '{"error": "批量接口不可用"}'
echo

# 5. 配置管理接口测试
print_section "5. 配置管理接口测试"

# 5.1 获取配置信息
print_subsection "5.1 获取配置信息"
print_request "GET /config?market=$MARKET&mode=$MODE"
curl -s -X GET "$BASE_URL/config?market=$MARKET&mode=$MODE" | jq '.' || echo '{"error": "配置接口不可用"}'
echo

# 5.2 更新配置
print_subsection "5.2 更新配置"
print_request "POST /config?market=$MARKET&mode=$MODE"
curl -s -X POST "$BASE_URL/config?market=$MARKET&mode=$MODE" \
  -H "Content-Type: application/json" \
  -d "{\"rotation_interval_minutes\":7,\"proxy_lifetime_minutes\":10}" | jq '.' || echo '{"error": "配置更新接口不可用"}'
echo

# 6. 错误处理测试
print_section "6. 错误处理测试"

# 6.1 测试不存在的市场
print_subsection "6.1 测试不存在的市场"
print_request "GET /status?market=invalid&mode=live"
curl -s -X GET "$BASE_URL/status?market=invalid&mode=live" | jq '.' || echo '{"expected": "404错误"}'
echo

# 6.2 测试无效的RPC事件
print_subsection "6.2 测试无效的RPC事件"
print_request "POST /rpc - invalid_event"
curl -s -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"invalid_event\",\"market\":\"$MARKET\"}" | jq '.' || echo '{"expected": "400错误"}'
echo

# 最后停止服务
print_section "7. 清理测试环境"
print_subsection "7.1 停止代理池服务"
print_request "POST /stop?market=$MARKET&mode=$MODE"
curl -s -X POST "$BASE_URL/stop?market=$MARKET&mode=$MODE" | jq '.' || echo '{"error": "停止接口不可用"}'
echo

print_section "测试完成"
echo "🎉 所有API接口测试完成！"
echo "请查看上述响应结果，确认JSON字段结构符合前端需求。"
echo ""
echo "📝 主要字段说明："
echo "  - status: 操作状态 (running/stopped/error/ok/started等)"
echo "  - market: 市场代码 (CN/HK/US)"
echo "  - day_type: 交易日类型 (NORMAL/HALF_DAY/HOLIDAY/WEEKEND)"
echo "  - session_type: 交易时段 (full_day/morning_only/afternoon_only)"
echo "  - trading_hours: 交易时间 {start, end, lunch_break}"
echo "  - stats: 统计信息 {pool_a_size, pool_b_size, success_rate等}"