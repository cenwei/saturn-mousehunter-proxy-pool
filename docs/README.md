# Saturn MouseHunter 代理池轮换微服务

> 多市场自动调度代理池管理系统，支持CN/HK/US三个市场的智能轮换和监控

## 📖 目录

- [概述](#概述)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [API文档](#api文档)
- [配置管理](#配置管理)
- [监控告警](#监控告警)
- [部署指南](#部署指南)
- [故障排除](#故障排除)

## 概述

Saturn MouseHunter 代理池轮换微服务是一个基于FastAPI的高性能代理池管理系统，专为多市场股票数据采集设计。系统采用DDD（领域驱动设计）架构，支持自动调度、智能轮换和全面监控。

### 核心业务流程

```
盘前2分钟 → 自动启动 → 获取400个代理 → A/B池7分钟轮换 → 盘后自动停止 → 第二天重复
```

## 核心特性

### 🌍 多市场支持
- **CN市场**：中国A股，09:30-15:10交易时间
- **HK市场**：香港股市，09:30-16:15交易时间
- **US市场**：美股，09:30-16:00交易时间
- **时区自适应**：自动处理各市场时区差异

### 🔄 智能轮换机制
- **A/B双池架构**：主备池无缝切换，保证服务连续性
- **7分钟轮换周期**：最优的代理刷新频率
- **400个代理批量获取**：满足高并发需求
- **10分钟代理生命周期**：平衡成本和可用性

### ⏰ 自动调度系统
- **交易日智能判断**：自动识别工作日和节假日
- **盘前2分钟启动**：精确时间控制，确保开盘前就绪
- **盘后30分钟停止**：节约资源，避免无效消耗
- **异常自动恢复**：网络故障、API异常等自动重试

### 📊 全面监控告警
- **实时健康检查**：成功率、池大小、延迟监控
- **多级别告警**：信息/警告/错误/严重四级告警
- **可视化界面**：Web管理界面，一目了然
- **历史数据分析**：趋势分析和性能优化

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- Redis (可选，用于缓存)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd saturn-mousehunter-proxy-pool
```

2. **安装依赖**
```bash
pip install -r requirements.txt
# 或使用 uv (推荐)
uv pip install -r pyproject.toml
```

3. **配置数据库**
```bash
# 编辑数据库连接配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=saturn_mousehunter
```

4. **初始化数据库**
```bash
python scripts/init_database.py
```

5. **启动服务**
```bash
# 启动单个市场
MARKETS=hk python src/main.py

# 启动多个市场
MARKETS=cn,hk,us python src/main.py
```

6. **访问管理界面**
```
浏览器打开: http://localhost:8080
```

## 架构设计

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web 管理界面   │    │   FastAPI 应用   │    │   全局调度器     │
│                │    │                │    │                │
│ • 实时监控      │◄──►│ • REST API     │◄──►│ • 交易日判断     │
│ • 配置管理      │    │ • 依赖注入     │    │ • 自动启停       │
│ • 批量操作      │    │ • 生命周期管理  │    │ • 错误恢复       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                │
                    ┌─────────────────┐
                    │  代理池管理器    │
                    │                │
                    │ • A/B池轮换    │
                    │ • 生命周期管理  │
                    │ • 状态追踪     │
                    └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  CN 市场     │    │  HK 市场     │    │  US 市场     │
│             │    │             │    │             │
│ • Live模式   │    │ • Live模式   │    │ • Live模式   │
│ • Backfill   │    │ • Backfill   │    │ • Backfill   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### DDD分层架构

```
src/
├── api/                    # API层 - 对外接口
│   └── routes/
│       └── proxy_pool_routes.py
├── application/            # 应用层 - 业务流程编排
│   └── services.py
├── domain/                 # 领域层 - 核心业务逻辑
│   ├── entities.py         # 实体和值对象
│   ├── services.py         # 领域服务
│   └── config_entities.py  # 配置领域模型
├── infrastructure/         # 基础设施层 - 技术实现
│   ├── config.py           # 配置管理
│   ├── proxy_pool.py       # 代理池管理器
│   ├── global_scheduler.py # 全局调度器
│   ├── monitoring.py       # 监控告警
│   ├── market_clock.py     # 市场时钟
│   ├── proxy_fetchers.py   # 代理获取器
│   ├── memory_proxy_repository.py  # 内存仓储
│   └── database_repositories.py    # 数据库仓储
└── main.py                 # 应用入口
```

## API文档

### 服务管理接口

#### 获取所有代理池状态
```http
GET /api/v1/pools
```

**响应示例:**
```json
{
  "pools": [
    {
      "key": "hk_live",
      "market": "hk",
      "mode": "live",
      "running": true,
      "status": {
        "stats": {
          "total_pool_size": 380,
          "success_rate": 95.2,
          "active_pool": "A"
        }
      }
    }
  ]
}
```

#### 启动代理池
```http
POST /api/v1/start?market=hk&mode=live
```

#### 停止代理池
```http
POST /api/v1/stop?market=hk&mode=live
```

### 配置管理接口

#### 获取配置
```http
GET /api/v1/config?market=hk&mode=live
```

#### 更新配置
```http
POST /api/v1/config?market=hk&mode=live
Content-Type: application/json

{
  "hailiang_api_url": "http://api.example.com/...",
  "rotation_interval_minutes": 7,
  "proxy_lifetime_minutes": 10,
  "batch_size": 400,
  "auto_start_enabled": true,
  "pre_market_start_minutes": 2
}
```

### RPC兼容接口

#### 获取代理
```http
POST /api/v1/rpc
Content-Type: application/json

{
  "event": "get_proxy",
  "market": "hk",
  "mode": "live",
  "proxy_type": "short"
}
```

**响应:**
```json
{
  "status": "ok",
  "proxy": "192.168.1.100:8080"
}
```

#### 报告代理失败
```http
POST /api/v1/rpc
Content-Type: application/json

{
  "event": "report_failure",
  "market": "hk",
  "mode": "live",
  "proxy_addr": "192.168.1.100:8080"
}
```

### 监控告警接口

#### 获取告警列表
```http
GET /api/v1/monitoring/alerts?hours=24&level=error&market=hk
```

#### 获取监控摘要
```http
GET /api/v1/monitoring/summary
```

**响应示例:**
```json
{
  "alerts": {
    "total_alerts": 25,
    "last_24h": {
      "total": 8,
      "critical": 0,
      "error": 2,
      "warning": 4,
      "info": 2
    }
  },
  "health": {
    "thresholds": {
      "success_rate_warning": 80.0,
      "success_rate_critical": 60.0
    }
  }
}
```

### 调度管理接口

#### 获取调度器状态
```http
GET /api/v1/scheduler/status
```

#### 强制启动市场
```http
POST /api/v1/scheduler/force-start/hk
```

#### 强制停止市场
```http
POST /api/v1/scheduler/force-stop/hk
```

## 配置管理

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|-------|------|
| `MARKETS` | `hk` | 启动的市场列表，逗号分隔 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8080` | 服务端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DB_HOST` | `localhost` | 数据库主机 |
| `DB_PORT` | `3306` | 数据库端口 |
| `DB_USER` | - | 数据库用户名 |
| `DB_PASSWORD` | - | 数据库密码 |
| `DB_NAME` | `saturn_mousehunter` | 数据库名 |

### 数据库配置

系统使用MySQL存储配置和状态信息：

#### 代理池配置表 (proxy_pool_config)
```sql
CREATE TABLE proxy_pool_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    market VARCHAR(10) NOT NULL,                    -- 市场代码
    mode VARCHAR(20) NOT NULL,                      -- 模式: live/backfill
    hailiang_api_url TEXT NOT NULL,                 -- 海量代理API URL
    hailiang_enabled BOOLEAN DEFAULT TRUE,          -- 是否启用海量代理
    batch_size INT DEFAULT 400,                     -- 批量获取数量
    proxy_lifetime_minutes INT DEFAULT 10,          -- 代理生命周期
    rotation_interval_minutes INT DEFAULT 7,        -- 轮换间隔
    auto_start_enabled BOOLEAN DEFAULT TRUE,        -- 自动启动
    pre_market_start_minutes INT DEFAULT 2,         -- 盘前启动时间
    post_market_stop_minutes INT DEFAULT 30,        -- 盘后停止时间
    -- 更多字段...
);
```

#### 代理池状态表 (proxy_pool_status)
```sql
CREATE TABLE proxy_pool_status (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    market VARCHAR(10) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    is_running BOOLEAN DEFAULT FALSE,               -- 运行状态
    active_pool VARCHAR(1) DEFAULT 'A',             -- 当前活跃池
    pool_a_size INT DEFAULT 0,                      -- A池大小
    pool_b_size INT DEFAULT 0,                      -- B池大小
    total_requests BIGINT DEFAULT 0,                -- 总请求数
    success_count BIGINT DEFAULT 0,                 -- 成功次数
    failure_count BIGINT DEFAULT 0,                 -- 失败次数
    success_rate DECIMAL(5,2) DEFAULT 0.00,         -- 成功率
    -- 更多字段...
);
```

### 默认配置值

```python
# 代理池配置
BATCH_SIZE = 400                    # 每次获取代理数量
PROXY_LIFETIME_MINUTES = 10         # 代理生命周期
ROTATION_INTERVAL_MINUTES = 7       # A/B池轮换间隔
LOW_WATERMARK = 50                  # 低水位线
TARGET_SIZE = 200                   # 目标池大小

# 调度配置
PRE_MARKET_START_MINUTES = 2        # 盘前启动时间
POST_MARKET_STOP_MINUTES = 30       # 盘后停止时间
AUTO_START_ENABLED = True           # 自动启动开关

# 监控配置
SUCCESS_RATE_WARNING = 80.0         # 成功率警告阈值
SUCCESS_RATE_CRITICAL = 60.0        # 成功率严重阈值
POOL_SIZE_WARNING = 10              # 池大小警告阈值
```

## 监控告警

### 告警级别

| 级别 | 描述 | 触发条件 | 处理建议 |
|------|------|----------|----------|
| **INFO** | 信息通知 | 服务启停、配置更新等 | 无需处理 |
| **WARNING** | 警告 | 成功率<80%、池大小<10 | 关注监控 |
| **ERROR** | 错误 | API失败、代理异常等 | 及时处理 |
| **CRITICAL** | 严重 | 成功率<60%、数据库异常 | 立即处理 |

### 健康检查指标

#### 代理池健康度
- **成功率监控**：实时计算请求成功率
- **池大小监控**：确保代理数量充足
- **轮换频率**：监控A/B池切换是否正常
- **API可用性**：海量代理API连通性检查

#### 调度器健康度
- **交易日识别**：确保交易日判断准确
- **时间同步**：各市场时区处理正确性
- **自动启停**：按时启动和停止验证

### 监控界面

Web管理界面提供实时监控功能：

- **概览仪表板**：关键指标一目了然
- **市场详情**：每个市场的详细状态
- **实时日志**：系统运行日志实时展示
- **告警中心**：告警列表和处理状态
- **统计图表**：历史趋势分析

## 部署指南

### Docker部署

1. **构建镜像**
```bash
docker build -t saturn-proxy-pool .
```

2. **运行容器**
```bash
docker run -d \
  --name proxy-pool \
  -p 8080:8080 \
  -e MARKETS=cn,hk,us \
  -e DB_HOST=mysql-host \
  -e DB_USER=username \
  -e DB_PASSWORD=password \
  saturn-proxy-pool
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: proxy-pool
spec:
  replicas: 1
  selector:
    matchLabels:
      app: proxy-pool
  template:
    metadata:
      labels:
        app: proxy-pool
    spec:
      containers:
      - name: proxy-pool
        image: saturn-proxy-pool:latest
        ports:
        - containerPort: 8080
        env:
        - name: MARKETS
          value: "cn,hk,us"
        - name: DB_HOST
          value: "mysql-service"
        # 更多环境变量...
```

### 生产环境配置

#### 负载均衡
```nginx
upstream proxy_pool {
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}

server {
    listen 80;
    server_name proxy-pool.company.com;

    location / {
        proxy_pass http://proxy_pool;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 数据库配置
```ini
# MySQL 优化配置
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
max_connections = 200
query_cache_type = 1
query_cache_size = 128M
```

## 故障排除

### 常见问题

#### 1. 服务无法启动
**症状**: 启动时出现端口占用或配置错误
```bash
# 检查端口占用
netstat -tulpn | grep 8080

# 检查配置
python -c "from infrastructure.config import get_app_config; print(get_app_config().__dict__)"
```

#### 2. 数据库连接失败
**症状**: 无法连接到MySQL数据库
```bash
# 测试数据库连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1"

# 检查防火墙
telnet $DB_HOST 3306
```

#### 3. 代理获取失败
**症状**: 海量代理API返回错误或超时
```bash
# 测试API连通性
curl -v "http://api.hailiangip.com:8422/api/getIp?..."

# 检查网络和DNS
nslookup api.hailiangip.com
ping api.hailiangip.com
```

#### 4. 调度器不工作
**症状**: 代理池未按时启动或停止
```bash
# 检查时区设置
timedatectl status

# 查看调度器日志
grep "scheduler" /var/log/proxy-pool.log
```

### 日志分析

#### 日志级别说明
```python
# 在代码中使用
log.debug("详细调试信息")      # 开发调试
log.info("一般信息")          # 正常运行
log.warning("警告信息")       # 需要关注
log.error("错误信息")         # 需要处理
log.critical("严重错误")      # 立即处理
```

#### 重要日志关键词
- `🚀 Starting market`: 市场启动
- `✅ Market started`: 市场启动成功
- `🛑 Stopping market`: 市场停止
- `❌ Failed to`: 各种失败场景
- `📅 Market next start`: 下次启动时间
- `⏰ Market will stop`: 预期停止时间

### 性能优化

#### 数据库优化
```sql
-- 创建必要索引
CREATE INDEX idx_market_mode ON proxy_pool_config(market, mode);
CREATE INDEX idx_running_status ON proxy_pool_status(is_running);
CREATE INDEX idx_updated_time ON proxy_pool_status(updated_at);
```

#### 内存优化
```python
# 在配置中调整池大小
TARGET_SIZE = 200           # 根据内存情况调整
LOW_WATERMARK = 50          # 低水位线
MAX_ALERTS = 1000           # 告警历史数量限制
```

#### 网络优化
```python
# HTTP客户端优化
TIMEOUT = 10.0              # 请求超时时间
MAX_RETRIES = 3             # 最大重试次数
CONN_POOL_SIZE = 100        # 连接池大小
```

---

## 技术支持

如果遇到问题或需要技术支持，请：

1. 查看本文档的故障排除章节
2. 检查系统日志和告警信息
3. 访问管理界面的监控面板
4. 联系开发团队获取帮助

**管理界面**: http://localhost:8080
**API文档**: http://localhost:8080/docs
**健康检查**: http://localhost:8080/health