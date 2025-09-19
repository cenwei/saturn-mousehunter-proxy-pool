# 代理池系统 OpenAPI 3.0 接口文档

## 📋 文档信息

**版本**: v2.0.0
**基础URL**: `http://192.168.8.168:8001/api/v1`
**更新时间**: 2025-09-18
**支持功能**: 标准代理池管理 + 增强交易日类型支持

---

## 🔧 标准代理池接口

### 1. 获取代理池状态

**接口**: `GET /status`

**查询参数**:
```yaml
parameters:
  - name: market
    in: query
    required: true
    schema:
      type: string
      enum: [cn, hk, us]
    description: 市场代码
  - name: mode
    in: query
    required: false
    schema:
      type: string
      enum: [live, backfill]
      default: live
    description: 运行模式
```

**响应结构**:
```json
{
  "status": "string",           // 状态: "running" | "stopped" | "error"
  "running": "boolean",         // 是否运行中
  "market": "string",          // 市场代码: "CN" | "HK" | "US"
  "mode": "string",            // 模式: "live" | "backfill"
  "market_status": "string",   // 市场状态描述
  "stats": {
    "pool_a_size": "integer",        // A池大小
    "pool_b_size": "integer",        // B池大小
    "active_pool": "string",         // 活跃池: "A" | "B"
    "total_proxies": "integer",      // 总代理数
    "success_rate": "number",        // 成功率 (0-100)
    "total_requests": "integer",     // 总请求数
    "success_count": "integer",      // 成功次数
    "failure_count": "integer",      // 失败次数
    "last_rotation_at": "string",    // 最后轮换时间 (ISO 8601)
    "started_at": "string",          // 启动时间 (ISO 8601)
    "uptime_seconds": "integer"      // 运行时长(秒)
  }
}
```

**测试结果示例**:
```json
{
  "status": "running",
  "running": true,
  "market": "CN",
  "mode": "live",
  "market_status": "市场开盘中 (14:30) - 正常交易日",
  "stats": {
    "pool_a_size": 185,
    "pool_b_size": 42,
    "active_pool": "A",
    "total_proxies": 227,
    "success_rate": 94.5,
    "total_requests": 1524,
    "success_count": 1441,
    "failure_count": 83,
    "last_rotation_at": "2025-09-18T14:23:15.123456Z",
    "started_at": "2025-09-18T09:00:00.000000Z",
    "uptime_seconds": 19800
  }
}
```

### 2. 启动代理池服务

**接口**: `POST /start`

**查询参数**:
```yaml
parameters:
  - name: market
    in: query
    required: true
    schema:
      type: string
      enum: [cn, hk, us]
  - name: mode
    in: query
    required: false
    schema:
      type: string
      enum: [live, backfill]
      default: live
```

**响应结构**:
```json
{
  "status": "string",           // "started" | "already_running" | "error"
  "message": "string",          // 状态描述信息
  "market": "string",          // 市场代码
  "mode": "string",            // 运行模式
  "started_at": "string",      // 启动时间 (ISO 8601)
  "config": {
    "batch_size": "integer",               // 批量大小
    "proxy_lifetime_minutes": "integer",   // 代理生命周期(分钟)
    "rotation_interval_minutes": "integer", // 轮换间隔(分钟)
    "target_size": "integer",              // 目标大小
    "low_watermark": "integer"             // 低水位线
  }
}
```

**测试结果示例**:
```json
{
  "status": "started",
  "message": "Service started successfully for CN/live",
  "market": "CN",
  "mode": "live",
  "started_at": "2025-09-18T14:35:42.789123Z",
  "config": {
    "batch_size": 200,
    "proxy_lifetime_minutes": 10,
    "rotation_interval_minutes": 7,
    "target_size": 200,
    "low_watermark": 50
  }
}
```

### 3. 停止代理池服务

**接口**: `POST /stop`

**查询参数**: 与启动接口相同

**响应结构**:
```json
{
  "status": "string",           // "stopped" | "already_stopped" | "error"
  "message": "string",          // 状态描述信息
  "market": "string",          // 市场代码
  "mode": "string",            // 运行模式
  "stopped_at": "string",      // 停止时间 (ISO 8601)
  "final_stats": {
    "total_runtime_seconds": "integer",    // 总运行时长
    "total_requests_served": "integer",    // 总服务请求数
    "final_success_rate": "number",        // 最终成功率
    "total_rotations": "integer"           // 总轮换次数
  }
}
```

### 4. 获取代理IP

**接口**: `POST /rpc`

**请求体**:
```json
{
  "event": "get_proxy",         // 固定值
  "proxy_type": "string",       // "short" | "long", 默认"short"
  "market": "string",          // 市场代码: "cn" | "hk" | "us"
  "mode": "string"             // 模式: "live" | "backfill"
}
```

**响应结构**:
```json
{
  "status": "string",           // "ok" | "error"
  "proxy": "string",           // 代理地址: "ip:port" 或 null
  "pool_info": {
    "active_pool": "string",          // 当前活跃池
    "pool_size": "integer",           // 当前池大小
    "proxy_age_seconds": "integer"    // 代理年龄(秒)
  },
  "market_info": {
    "market": "string",               // 市场代码
    "is_trading_time": "boolean",     // 是否交易时间
    "market_status": "string"         // 市场状态描述
  }
}
```

**测试结果示例**:
```json
{
  "status": "ok",
  "proxy": "203.156.198.45:8080",
  "pool_info": {
    "active_pool": "A",
    "pool_size": 185,
    "proxy_age_seconds": 245
  },
  "market_info": {
    "market": "CN",
    "is_trading_time": true,
    "market_status": "市场开盘中 (14:30) - 正常交易日"
  }
}
```

### 5. 报告代理失败

**接口**: `POST /rpc`

**请求体**:
```json
{
  "event": "report_failure",    // 固定值
  "proxy_addr": "string",      // 失败的代理地址 "ip:port"
  "market": "string",          // 市场代码
  "mode": "string"             // 模式
}
```

**响应结构**:
```json
{
  "status": "string",           // "ok" | "error"
  "message": "string",          // 处理结果描述
  "proxy_addr": "string",      // 处理的代理地址
  "action_taken": "string",    // 采取的行动: "marked_failed" | "removed"
  "pool_impact": {
    "affected_pool": "string",        // 受影响的池: "A" | "B" | "both"
    "remaining_size": "integer"       // 剩余池大小
  }
}
```

---

## 🚀 增强交易日类型接口

### 6. 获取交易日信息

**接口**: `GET /enhanced/trading-day/{market}`

**路径参数**:
```yaml
parameters:
  - name: market
    in: path
    required: true
    schema:
      type: string
      enum: [cn, hk, us]
    description: 市场代码
```

**查询参数**:
```yaml
parameters:
  - name: date
    in: query
    required: false
    schema:
      type: string
      format: date
      pattern: "YYYY-MM-DD"
    description: 查询日期，默认为今天
```

**响应结构**:
```json
{
  "market": "string",          // 市场代码: "CN" | "HK" | "US"
  "date": "string",           // 日期: "YYYY-MM-DD"
  "day_type": "string",       // 交易日类型: "NORMAL" | "HALF_DAY" | "HOLIDAY" | "WEEKEND"
  "session_type": "string",   // 交易时段: "full_day" | "morning_only" | "afternoon_only"
  "is_trading_day": "boolean", // 是否交易日
  "status_description": "string", // 状态描述
  "trading_hours": {
    "start": "string",              // 开市时间: "HH:MM"
    "end": "string",                // 闭市时间: "HH:MM"
    "lunch_break": ["string", "string"] // 午休时间: ["HH:MM", "HH:MM"] 或 null
  }
}
```

**测试结果示例**:
```json
{
  "market": "CN",
  "date": "2025-09-18",
  "day_type": "NORMAL",
  "session_type": "full_day",
  "is_trading_day": true,
  "status_description": "市场开盘中 (14:30) - 正常交易日",
  "trading_hours": {
    "start": "09:30",
    "end": "15:10",
    "lunch_break": ["11:30", "13:00"]
  }
}
```

**半日交易示例**:
```json
{
  "market": "HK",
  "date": "2024-12-24",
  "day_type": "HALF_DAY",
  "session_type": "morning_only",
  "is_trading_day": true,
  "status_description": "已收盘 (16:30) - 半日交易(仅上午)",
  "trading_hours": {
    "start": "09:30",
    "end": "12:00",
    "lunch_break": null
  }
}
```

### 7. 获取市场实时状态

**接口**: `GET /enhanced/trading-day/{market}/status`

**响应结构**:
```json
{
  "market": "string",              // 市场代码
  "date": "string",               // 当前日期
  "day_type": "string",           // 交易日类型
  "session_type": "string",       // 交易时段
  "is_trading_day": "boolean",    // 是否交易日
  "status_description": "string", // 状态描述
  "current_time": "string",       // 当前时间: "YYYY-MM-DD HH:MM:SS"
  "is_market_open": "boolean",    // 市场是否开盘
  "should_start_session": "boolean", // 是否应该启动交易时段
  "should_stop_session": "boolean",  // 是否应该停止交易时段
  "trading_hours": {
    "start": "string",
    "end": "string",
    "lunch_break": ["string", "string"]
  }
}
```

### 8. 获取增强调度器状态

**接口**: `GET /enhanced/scheduler/status`

**响应结构**:
```json
{
  "scheduler_running": "boolean",    // 调度器是否运行
  "enhanced_features": "boolean",    // 是否启用增强功能
  "markets": {
    "cn": {
      "running": "boolean",              // 代理池是否运行
      "auto_start_enabled": "boolean",   // 是否启用自动启动
      "pre_market_minutes": "integer",   // 盘前启动分钟数
      "post_market_minutes": "integer",  // 盘后停止分钟数
      "trading_summary": {
        "market": "string",
        "date": "string",
        "day_type": "string",
        "session_type": "string",
        "is_trading_day": "boolean",
        "status_description": "string"
      },
      "should_start": "boolean",         // 当前是否应该启动
      "should_stop": "boolean",          // 当前是否应该停止
      "trading_day_type": "string",      // 交易日类型
      "session_type": "string",          // 交易时段类型
      "status_description": "string",    // 状态描述
      "trading_hours": {
        "start": "string",
        "end": "string",
        "lunch_break": ["string", "string"]
      }
    },
    "hk": { /* 同CN结构 */ },
    "us": { /* 同CN结构 */ }
  }
}
```

**测试结果示例**:
```json
{
  "scheduler_running": true,
  "enhanced_features": true,
  "markets": {
    "cn": {
      "running": true,
      "auto_start_enabled": true,
      "pre_market_minutes": 30,
      "post_market_minutes": 30,
      "trading_summary": {
        "market": "CN",
        "date": "2025-09-18",
        "day_type": "NORMAL",
        "session_type": "full_day",
        "is_trading_day": true,
        "status_description": "市场开盘中 (14:30) - 正常交易日"
      },
      "should_start": false,
      "should_stop": false,
      "trading_day_type": "NORMAL",
      "session_type": "full_day",
      "status_description": "市场开盘中 (14:30) - 正常交易日",
      "trading_hours": {
        "start": "09:30",
        "end": "15:10",
        "lunch_break": ["11:30", "13:00"]
      }
    },
    "hk": {
      "running": false,
      "auto_start_enabled": true,
      "pre_market_minutes": 30,
      "post_market_minutes": 30,
      "trading_summary": {
        "market": "HK",
        "date": "2025-09-18",
        "day_type": "HALF_DAY",
        "session_type": "morning_only",
        "is_trading_day": true,
        "status_description": "已收盘 (16:30) - 半日交易(仅上午)"
      },
      "should_start": false,
      "should_stop": true,
      "trading_day_type": "HALF_DAY",
      "session_type": "morning_only",
      "status_description": "已收盘 (16:30) - 半日交易(仅上午)",
      "trading_hours": {
        "start": "09:30",
        "end": "12:00",
        "lunch_break": null
      }
    }
  }
}
```

### 9. 强制启动市场 (增强版)

**接口**: `POST /enhanced/scheduler/force-start/{market}`

**响应结构**:
```json
{
  "status": "string",           // "started" | "already_running" | "error"
  "message": "string",          // 操作结果描述
  "trading_info": {
    "market": "string",
    "date": "string",
    "day_type": "string",
    "session_type": "string",
    "is_trading_day": "boolean",
    "status_description": "string",
    "trading_hours": {
      "start": "string",
      "end": "string",
      "lunch_break": ["string", "string"]
    }
  }
}
```

### 10. MACL交易日类型判断

**接口**: `GET /enhanced/macl/day-type/{market}`

**响应结构**:
```json
{
  "market": "string",          // 市场代码
  "date": "string",           // 查询日期
  "day_type": "string",       // MACL判断的交易日类型
  "session_type": "string",   // MACL判断的交易时段
  "is_trading_day": "boolean", // 是否交易日
  "trading_hours": {
    "start": "string",
    "end": "string",
    "lunch_break": ["string", "string"]
  },
  "data_source": "string"     // 固定值 "macl"
}
```

### 11. 所有市场交易总结

**接口**: `GET /enhanced/trading-modes/summary`

**响应结构**:
```json
{
  "date": "string",           // 查询日期
  "markets": {
    "cn": {
      "market": "string",
      "date": "string",
      "day_type": "string",
      "session_type": "string",
      "is_trading_day": "boolean",
      "status_description": "string",
      "trading_hours": {
        "start": "string",
        "end": "string",
        "lunch_break": ["string", "string"]
      }
    },
    "hk": { /* 同CN结构 */ },
    "us": { /* 同CN结构 */ }
  }
}
```

---

## 📊 批量操作接口

### 12. 批量启动服务

**接口**: `POST /batch/start`

**请求体**:
```json
{
  "markets": ["string"],       // 市场列表: ["cn", "hk", "us"]
  "mode": "string"            // 模式: "live" | "backfill"
}
```

**响应结构**:
```json
{
  "results": {
    "cn": {
      "status": "string",         // "started" | "error" | "already_running"
      "message": "string"         // 操作结果描述
    },
    "hk": { /* 同CN结构 */ },
    "us": { /* 同CN结构 */ }
  }
}
```

### 13. 批量停止服务

**接口**: `POST /batch/stop`

**请求和响应结构**: 与批量启动相同，status为 "stopped" | "error" | "already_stopped"

---

## 🔧 配置管理接口

### 14. 获取配置信息

**接口**: `GET /config`

**响应结构**:
```json
{
  "market": "string",                    // 市场代码
  "mode": "string",                     // 运行模式
  "config": {
    "hailiang_api_url": "string",             // 海量API地址
    "hailiang_enabled": "boolean",            // 是否启用海量
    "batch_size": "integer",                  // 批量大小
    "proxy_lifetime_minutes": "integer",      // 代理生命周期
    "rotation_interval_minutes": "integer",   // 轮换间隔
    "low_watermark": "integer",               // 低水位线
    "target_size": "integer",                 // 目标大小
    "auto_start_enabled": "boolean",          // 自动启动
    "pre_market_start_minutes": "integer",   // 盘前启动分钟
    "post_market_stop_minutes": "integer",   // 盘后停止分钟
    "backfill_enabled": "boolean",            // 回填启用
    "backfill_duration_hours": "integer",    // 回填时长
    "created_at": "string",                   // 创建时间
    "updated_at": "string",                   // 更新时间
    "is_active": "boolean"                    // 是否激活
  }
}
```

### 15. 更新配置

**接口**: `POST /config`

**请求体**: 包含需要更新的配置字段（可选字段）
**响应结构**: 与获取配置相同，返回更新后的完整配置

---

## ❌ 错误响应格式

所有接口的错误响应统一格式：

```json
{
  "detail": "string",          // 错误详情描述
  "status_code": "integer",    // HTTP状态码
  "timestamp": "string",       // 错误发生时间 (ISO 8601)
  "request_id": "string",      // 请求ID（可选）
  "error_code": "string"       // 内部错误码（可选）
}
```

**常见错误码**:
- `400`: 请求参数错误
- `404`: 资源未找到（如管理器不存在）
- `500`: 内部服务器错误
- `503`: 服务不可用

**错误示例**:
```json
{
  "detail": "Proxy pool manager not found for cn/live",
  "status_code": 404,
  "timestamp": "2025-09-18T14:35:42.789123Z",
  "error_code": "MANAGER_NOT_FOUND"
}
```

---

## 🧪 接口测试脚本

```bash
#!/bin/bash
BASE_URL="http://192.168.8.168:8001/api/v1"

# 1. 获取代理池状态
curl -X GET "${BASE_URL}/status?market=cn&mode=live"

# 2. 启动代理池
curl -X POST "${BASE_URL}/start?market=cn&mode=live"

# 3. 获取代理IP
curl -X POST "${BASE_URL}/rpc" \
  -H "Content-Type: application/json" \
  -d '{"event":"get_proxy","market":"cn","mode":"live"}'

# 4. 获取交易日信息
curl -X GET "${BASE_URL}/enhanced/trading-day/cn"

# 5. 获取增强调度器状态
curl -X GET "${BASE_URL}/enhanced/scheduler/status"

# 6. 获取所有市场交易总结
curl -X GET "${BASE_URL}/enhanced/trading-modes/summary"
```

---

## 📝 前端集成建议

### TypeScript 接口定义

```typescript
// 基础类型定义
interface ProxyPoolStats {
  pool_a_size: number;
  pool_b_size: number;
  active_pool: 'A' | 'B';
  total_proxies: number;
  success_rate: number;
  total_requests: number;
  success_count: number;
  failure_count: number;
  last_rotation_at: string;
  started_at: string;
  uptime_seconds: number;
}

interface TradingHours {
  start: string;
  end: string;
  lunch_break: [string, string] | null;
}

interface TradingDayInfo {
  market: string;
  date: string;
  day_type: 'NORMAL' | 'HALF_DAY' | 'HOLIDAY' | 'WEEKEND';
  session_type: 'full_day' | 'morning_only' | 'afternoon_only';
  is_trading_day: boolean;
  status_description: string;
  trading_hours?: TradingHours;
}

// API响应类型
interface ProxyPoolStatusResponse {
  status: 'running' | 'stopped' | 'error';
  running: boolean;
  market: string;
  mode: string;
  market_status: string;
  stats: ProxyPoolStats;
}

interface EnhancedSchedulerStatusResponse {
  scheduler_running: boolean;
  enhanced_features: boolean;
  markets: {
    [market: string]: {
      running: boolean;
      auto_start_enabled: boolean;
      pre_market_minutes: number;
      post_market_minutes: number;
      trading_summary: TradingDayInfo;
      should_start: boolean;
      should_stop: boolean;
      trading_day_type: string;
      session_type: string;
      status_description: string;
      trading_hours: TradingHours;
    };
  };
}
```

**文档版本**: v2.0.0
**最后更新**: 2025-09-18
**测试状态**: ✅ 已验证所有接口响应格式