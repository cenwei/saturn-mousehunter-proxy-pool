# 多市场并行运行指南

> Saturn MouseHunter 代理池服务完全支持多个市场并行运行

## 🌍 支持的市场

| 市场 | 代码 | 交易时间 | 时区 | 午休时间 |
|------|------|----------|------|----------|
| 中国A股 | `cn` | 09:30-11:30, 13:00-15:10 | Asia/Shanghai | 11:30-13:00 |
| 香港股市 | `hk` | 09:30-12:00, 13:00-16:15 | Asia/Hong_Kong | 12:00-13:00 |
| 美股 | `us` | 09:30-16:00 | America/New_York | 无 |

## 🚀 多市场启动方式

### 1. 同时启动多个市场（推荐）

```bash
# 启动所有主要市场
ENVIRONMENT=development MARKETS=cn,hk,us ./start.sh

# 或手动启动
ENVIRONMENT=development MARKETS=cn,hk,us python src/main.py
```

### 2. 指定部分市场

```bash
# 只启动中港市场
ENVIRONMENT=development MARKETS=cn,hk ./start.sh

# 只启动港股
ENVIRONMENT=development MARKETS=hk ./start.sh
```

## 🏗️ 架构说明

### 多市场管理器架构

每个市场都有独立的管理器：

```
代理池服务
├── cn_live       (中国A股 Live模式)
├── cn_backfill   (中国A股 Backfill模式)
├── hk_live       (香港股市 Live模式)
├── hk_backfill   (香港股市 Backfill模式)
├── us_live       (美股 Live模式)
└── us_backfill   (美股 Backfill模式)
```

### 独立的A/B池轮换

每个市场都有独立的：
- **A池和B池**：主备池无缝切换
- **轮换机制**：7分钟自动轮换周期
- **代理生命周期**：10分钟代理有效期
- **批量获取**：每次获取400个代理

### 自动调度机制

**全局调度器**会同时管理所有市场：

1. **开盘前2分钟自动启动**
   - 中国A股：09:28 启动
   - 香港股市：09:28 启动
   - 美股：09:28 启动 (纽约时间)

2. **收市后自动停止**
   - 中国A股：15:40 停止 (收盘后30分钟)
   - 香港股市：16:45 停止 (收盘后30分钟)
   - 美股：16:30 停止 (收盘后30分钟)

3. **跨时区支持**
   - 每个市场使用各自的时区
   - 自动处理夏令时切换
   - 独立的交易日判断

## 📊 多市场监控

### API接口支持

所有接口都支持多市场：

```bash
# 获取所有市场状态
GET /api/v1/pools

# 获取特定市场代理
POST /api/v1/rpc
{
  "event": "get_proxy",
  "market": "cn",    # 可以是 cn/hk/us
  "mode": "live"
}

# 获取特定市场状态
GET /api/v1/status?market=hk

# 批量启动所有市场
POST /api/v1/batch/start
{
  "markets": ["cn", "hk", "us"],
  "mode": "live"
}
```

### Web管理界面

访问管理界面可以看到所有市场：
- **开发环境**: http://192.168.8.168:8005
- 显示所有市场的实时状态
- 支持单独控制每个市场

## 🔧 实际运行示例

### 启动日志示例

```
🚀 启动代理池服务 - Saturn MouseHunter Proxy Pool Service v1.0.0
服务配置 - Host: 192.168.8.168, Port: 8005
运行环境: development

✅ Created proxy pool managers for market cn
✅ Created proxy pool managers for market hk
✅ Created proxy pool managers for market us

🕘 全局调度器已启动
  - CN市场: 下次启动时间 2024-01-02 09:28:00+08:00
  - HK市场: 下次启动时间 2024-01-02 09:28:00+08:00
  - US市场: 下次启动时间 2024-01-02 09:28:00-05:00

📊 监控系统已就绪
```

### 运行时状态

```bash
# 查看所有市场状态
curl http://192.168.8.168:8005/api/v1/pools

# 响应示例
{
  "pools": [
    {
      "key": "cn_live",
      "market": "cn",
      "mode": "live",
      "running": true,
      "status": {
        "stats": {
          "total_pool_size": 380,
          "success_rate": 95.2,
          "active_pool": "A"
        }
      }
    },
    {
      "key": "hk_live",
      "market": "hk",
      "mode": "live",
      "running": true,
      "status": {
        "stats": {
          "total_pool_size": 395,
          "success_rate": 96.8,
          "active_pool": "B"
        }
      }
    },
    {
      "key": "us_live",
      "market": "us",
      "mode": "live",
      "running": false,
      "status": {
        "market_status": "market_closed"
      }
    }
  ]
}
```

## ⏰ 时间表示例

假设现在是 **2024年1月2日**：

| 时间 (北京时间) | CN市场 | HK市场 | US市场 (EST) |
|-----------------|--------|--------|--------------|
| 09:28 | 🟡 准备启动 | 🟡 准备启动 | 😴 未到时间 |
| 09:30 | 🟢 交易中 | 🟢 交易中 | 😴 收盘状态 |
| 12:00 | 🟡 午休 | 🟡 午休 | 😴 收盘状态 |
| 13:00 | 🟢 交易中 | 🟢 交易中 | 😴 收盘状态 |
| 15:10 | 🔴 收盘 | 🟢 交易中 | 😴 收盘状态 |
| 16:15 | 🔴 已停止 | 🔴 收盘 | 😴 收盘状态 |
| 22:28 | 😴 休息 | 😴 休息 | 🟡 准备启动 |
| 22:30 | 😴 休息 | 😴 休息 | 🟢 交易中 |

## 🎯 最佳实践

### 1. 生产环境推荐配置

```bash
# 同时启动所有主要市场
ENVIRONMENT=production MARKETS=cn,hk,us ./start.sh
```

### 2. 资源监控

- **CPU使用率**：每个市场约消耗5-10% CPU
- **内存使用**：每个市场约消耗100-200MB内存
- **网络带宽**：每个市场约1-2Mbps

### 3. 故障隔离

- 单个市场故障不影响其他市场
- 每个市场有独立的代理池和配置
- 支持单独重启特定市场

### 4. 监控告警

```bash
# 检查所有市场健康状态
curl http://192.168.8.168:8005/api/v1/monitoring/summary

# 获取特定市场告警
curl "http://192.168.8.168:8005/api/v1/monitoring/alerts?market=hk&hours=1"
```

## 🔍 常见问题

### Q: 可以动态增减市场吗？
A: 当前需要重启服务，通过修改 `MARKETS` 环境变量实现。

### Q: 不同市场的代理池大小可以不同吗？
A: 可以，每个市场在数据库中有独立的配置，可以设置不同的 `batch_size` 和 `target_size`。

### Q: 如何单独控制某个市场？
A: 使用API接口：
```bash
# 停止港股市场
POST /api/v1/stop?market=hk&mode=live

# 启动美股市场
POST /api/v1/start?market=us&mode=live
```

---

**现在您可以通过 `MARKETS=cn,hk,us` 同时运行所有市场，每个市场都有独立的A/B池轮换机制！** 🚀