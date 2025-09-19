# Saturn MouseHunter 代理池微服务 OpenAPI 接口文档

**服务信息**
- **服务名称**: Saturn MouseHunter Proxy Pool Service
- **版本**: 1.0.0
- **描述**: Saturn MouseHunter代理池轮换微服务 - 支持多市场自动调度
- **OpenAPI规范**: 3.1.0

**基础URL**: `http://192.168.8.168:8005`

## 📊 核心端点总览

### 🎯 代理池管理端点

| 端点 | 方法 | 描述 | 重要性 |
|-----|------|------|--------|
| `/api/v1/pools` | GET | **获取所有代理池状态** | ⭐⭐⭐ |
| `/api/v1/status` | GET | 获取指定代理池状态 | ⭐⭐⭐ |
| `/api/v1/start` | POST | 启动代理池 | ⭐⭐⭐ |
| `/api/v1/stop` | POST | 停止代理池 | ⭐⭐⭐ |
| `/api/v1/config` | GET | 获取代理池配置 | ⭐⭐ |
| `/api/v1/metrics` | GET | 获取代理池指标 | ⭐⭐ |

### 🕐 调度器管理端点

| 端点 | 方法 | 描述 | 重要性 |
|-----|------|------|--------|
| `/api/v1/scheduler/status` | GET | 获取调度器状态 | ⭐⭐⭐ |
| `/api/v1/scheduler/force-start/{market}` | POST | 强制启动指定市场 | ⭐⭐ |
| `/api/v1/scheduler/force-stop/{market}` | POST | 强制停止指定市场 | ⭐⭐ |

### 📈 监控与告警端点

| 端点 | 方法 | 描述 | 重要性 |
|-----|------|------|--------|
| `/api/v1/monitoring/alerts` | GET | 获取告警列表 | ⭐⭐ |
| `/api/v1/monitoring/summary` | GET | 获取监控摘要 | ⭐⭐ |
| `/api/v1/monitoring/alerts/{alert_id}/acknowledge` | POST | 确认告警 | ⭐ |
| `/api/v1/monitoring/alerts/clear` | DELETE | 清理旧告警 | ⭐ |

### 🔧 高级功能端点

| 端点 | 方法 | 描述 | 重要性 |
|-----|------|------|--------|
| `/api/v1/backfill/start` | POST | 启动回填任务 | ⭐⭐ |
| `/api/v1/batch/start` | POST | 批量启动代理池 | ⭐⭐ |
| `/api/v1/batch/stop` | POST | 批量停止代理池 | ⭐⭐ |
| `/api/v1/rpc` | POST | RPC接口调用 | ⭐ |
| `/api/v1/config/hailiang/test` | POST | 测试海亮代理配置 | ⭐ |

### 🔍 系统端点

| 端点 | 方法 | 描述 | 重要性 |
|-----|------|------|--------|
| `/health` | GET | 服务健康检查 | ⭐⭐⭐ |
| `/` | GET | 管理界面首页 | ⭐⭐ |

## 🎯 三市场验证端点

### 核心端点测试
```bash
# 1. 所有代理池状态（显示三市场）
curl "http://192.168.8.168:8005/api/v1/pools"

# 2. 服务健康检查
curl "http://192.168.8.168:8005/health"

# 3. 各市场状态查询
curl "http://192.168.8.168:8005/api/v1/status?market=cn&mode=live"
curl "http://192.168.8.168:8005/api/v1/status?market=hk&mode=live"
curl "http://192.168.8.168:8005/api/v1/status?market=us&mode=live"
```

### 重要参数说明

**市场参数 (market)**:
- `cn` - 中国A股市场
- `hk` - 香港股市
- `us` - 美国股市

**模式参数 (mode)**:
- `live` - 实时交易模式
- `backfill` - 历史数据回填模式

## 📋 响应示例

### `/api/v1/pools` 响应
```json
{
  "pools": [
    {
      "key": "CN_live",
      "market": "CN",
      "mode": "live",
      "running": false,
      "status": {
        "running": false,
        "market": "cn",
        "mode": "live",
        "error": "Service not running"
      }
    },
    {
      "key": "HK_live",
      "market": "HK",
      "mode": "live",
      "running": false,
      "status": {
        "running": false,
        "market": "hk",
        "mode": "live",
        "error": "Service not running"
      }
    },
    {
      "key": "US_live",
      "market": "US",
      "mode": "live",
      "running": false,
      "status": {
        "running": false,
        "market": "us",
        "mode": "live",
        "error": "Service not running"
      }
    }
  ]
}
```

### `/health` 响应
```json
{
  "status": "partial",
  "service": "Saturn MouseHunter Proxy Pool Service",
  "version": "1.0.0",
  "proxy_pools": {
    "CN_live": false,
    "CN_backfill": false,
    "HK_live": false,
    "HK_backfill": false,
    "US_live": false,
    "US_backfill": false
  },
  "total_pools": 6,
  "running_pools": 0
}
```

## 🌐 访问地址

- **API文档**: http://192.168.8.168:8005/docs
- **完整OpenAPI规范**: http://192.168.8.168:8005/openapi.json
- **管理界面**: http://192.168.8.168:8005
- **健康检查**: http://192.168.8.168:8005/health

## 📁 本地文件

- **OpenAPI规范文件**: `/saturn-mousehunter-proxy-pool/docs/proxy_pool_openapi.json`
- **测试脚本**: `/saturn-mousehunter-proxy-pool/test_markets.sh`

---

**生成时间**: 2025-09-19
**服务状态**: ✅ 运行正常，三市场(CN/HK/US)已正确初始化