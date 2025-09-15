# Saturn MouseHunter 代理池服务 FastAPI 接口文档

> 专为 Kotlin 项目对接设计的代理池微服务 API 规范

## 📖 目录

- [服务概述](#服务概述)
- [基础配置](#基础配置)
- [核心接口](#核心接口)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [Kotlin 集成示例](#kotlin-集成示例)
- [最佳实践](#最佳实践)

## 服务概述

Saturn MouseHunter 代理池轮换微服务提供了完整的代理池管理功能，支持多市场（CN/HK/US）自动调度和智能轮换。

### 服务地址

| 环境 | 服务地址 | 端口 |
|------|----------|------|
| 开发环境 | `http://localhost:8080` | 8080 |
| 测试环境 | `http://proxy-pool-test.saturn.com:8080` | 8080 |
| 生产环境 | `http://proxy-pool.saturn.com:8080` | 8080 |

### 认证方式

目前服务采用内网访问，无需额外认证。如需添加认证，建议使用 JWT Token 或 API Key。

## 基础配置

### HTTP 请求头

```http
Content-Type: application/json
Accept: application/json
User-Agent: SaturnMouseHunter-Kotlin/1.0
```

### 响应格式

所有接口都返回标准化的 JSON 格式：

```json
{
  "status": "ok|error",
  "data": { ... },
  "message": "操作结果说明",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## 核心接口

### 1. 代理池管理接口

#### 1.1 获取代理 (RPC 风格)

**用途**: 获取可用代理地址，这是最常用的接口

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

**响应示例**:
```json
{
  "status": "ok",
  "proxy": "192.168.1.100:8080"
}
```

**Kotlin 调用示例**:
```kotlin
data class ProxyRequest(
    val event: String,
    val market: String = "hk",
    val mode: String = "live",
    val proxy_type: String = "short"
)

data class ProxyResponse(
    val status: String,
    val proxy: String?
)

// 使用 Retrofit
@POST("/api/v1/rpc")
suspend fun getProxy(@Body request: ProxyRequest): Response<ProxyResponse>
```

#### 1.2 报告代理失败

**用途**: 当代理不可用时报告给系统

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

**响应示例**:
```json
{
  "status": "ok",
  "message": "192.168.1.100:8080 marked as failure"
}
```

#### 1.3 健康检查

**用途**: 检查服务和代理池状态

```http
POST /api/v1/rpc
Content-Type: application/json

{
  "event": "ping",
  "market": "hk",
  "mode": "live"
}
```

**响应示例**:
```json
{
  "status": "ok",
  "message": "pong",
  "market": "hk",
  "mode": "live",
  "running": true,
  "market_status": "market_open"
}
```

### 2. 代理池状态接口

#### 2.1 获取所有代理池状态

```http
GET /api/v1/pools
```

**响应示例**:
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
          "active_pool": "A",
          "active_pool_size": 195,
          "standby_pool_size": 185,
          "total_requests": 15420,
          "success_count": 14680,
          "failure_count": 740
        },
        "market_status": "market_open"
      }
    }
  ]
}
```

#### 2.2 获取特定市场状态

```http
GET /api/v1/status?market=hk&mode=live
```

**响应示例**:
```json
{
  "status": "ok",
  "running": true,
  "market": "hk",
  "mode": "live",
  "market_status": "market_open",
  "stats": {
    "total_pool_size": 380,
    "success_rate": 95.2,
    "active_pool": "A",
    "total_requests": 15420,
    "success_count": 14680,
    "failure_count": 740
  }
}
```

#### 2.3 获取指标数据

```http
GET /api/v1/metrics?market=hk&mode=live
```

**响应示例**:
```json
{
  "running": 1,
  "active_pool": "A",
  "size_active": 195,
  "size_standby": 185,
  "total_pool_size": 380,
  "success_rate": 95.2,
  "total_requests": 15420,
  "success_count": 14680,
  "failure_count": 740
}
```

### 3. 代理池控制接口

#### 3.1 启动代理池

```http
POST /api/v1/start?market=hk&mode=live
```

**响应示例**:
```json
{
  "status": "started",
  "message": "Proxy pool service started for hk/live"
}
```

#### 3.2 停止代理池

```http
POST /api/v1/stop?market=hk&mode=live
```

**响应示例**:
```json
{
  "status": "stopped",
  "message": "Proxy pool service stopped for hk/live"
}
```

#### 3.3 批量启动

```http
POST /api/v1/batch/start
Content-Type: application/json

{
  "markets": ["cn", "hk", "us"],
  "mode": "live"
}
```

**响应示例**:
```json
{
  "results": {
    "cn": {"status": "started", "message": "Service started successfully"},
    "hk": {"status": "started", "message": "Service started successfully"},
    "us": {"status": "started", "message": "Service started successfully"}
  }
}
```

### 4. 配置管理接口

#### 4.1 获取配置

```http
GET /api/v1/config?market=hk&mode=live
```

**响应示例**:
```json
{
  "market": "hk",
  "mode": "live",
  "config": {
    "hailiang_api_url": "http://api.hailiangip.com:8422/api/getIp?...",
    "batch_size": 400,
    "proxy_lifetime_minutes": 10,
    "rotation_interval_minutes": 7,
    "low_watermark": 50,
    "target_size": 200,
    "auto_start_enabled": true,
    "pre_market_start_minutes": 2,
    "post_market_stop_minutes": 30
  },
  "backend": "database_driven"
}
```

#### 4.2 更新配置

```http
POST /api/v1/config?market=hk&mode=live
Content-Type: application/json

{
  "batch_size": 500,
  "rotation_interval_minutes": 5,
  "auto_start_enabled": true
}
```

### 5. 监控告警接口

#### 5.1 获取告警列表

```http
GET /api/v1/monitoring/alerts?hours=24&level=error&market=hk
```

**响应示例**:
```json
{
  "alerts": [
    {
      "id": "20240101_100030_001",
      "level": "error",
      "title": "API Error",
      "message": "Failed to fetch proxies from Hailiang API",
      "market": "hk",
      "component": "API",
      "timestamp": "2024-01-01T10:00:30Z",
      "acknowledged": false
    }
  ],
  "total": 1,
  "filters": {
    "hours": 24,
    "level": "error",
    "market": "hk"
  }
}
```

#### 5.2 获取监控摘要

```http
GET /api/v1/monitoring/summary
```

**响应示例**:
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
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### 6. 调度管理接口

#### 6.1 获取调度器状态

```http
GET /api/v1/scheduler/status
```

**响应示例**:
```json
{
  "scheduler_running": true,
  "markets": {
    "cn": {
      "next_start_time": "2024-01-02T09:28:00+08:00",
      "next_stop_time": "2024-01-02T15:40:00+08:00",
      "is_trading_day": true,
      "current_status": "stopped"
    },
    "hk": {
      "next_start_time": "2024-01-02T09:28:00+08:00",
      "next_stop_time": "2024-01-02T16:45:00+08:00",
      "is_trading_day": true,
      "current_status": "running"
    }
  }
}
```

## 数据模型

### ProxyPoolStatus (代理池状态)

```kotlin
data class ProxyPoolStatus(
    val key: String,                    // 代理池标识: "hk_live"
    val market: String,                 // 市场: "cn", "hk", "us"
    val mode: String,                   // 模式: "live", "backfill"
    val running: Boolean,               // 是否运行中
    val status: PoolStatusDetail
)

data class PoolStatusDetail(
    val stats: PoolStats,
    val marketStatus: String           // "market_open", "market_closed", "pre_market", "after_market"
)

data class PoolStats(
    val totalPoolSize: Int,            // 总代理数量
    val successRate: Double,           // 成功率 (0-100)
    val activePool: String,            // 当前活跃池: "A" 或 "B"
    val activePoolSize: Int,           // 活跃池大小
    val standbyPoolSize: Int,          // 备用池大小
    val totalRequests: Long,           // 总请求数
    val successCount: Long,            // 成功次数
    val failureCount: Long             // 失败次数
)
```

### ProxyConfig (代理池配置)

```kotlin
data class ProxyConfig(
    val market: String,                        // 市场代码
    val mode: String,                          // 模式
    val hailiangApiUrl: String,                // 海量代理API地址
    val hailiangEnabled: Boolean = true,       // 是否启用海量代理
    val batchSize: Int = 400,                  // 批量获取数量
    val proxyLifetimeMinutes: Int = 10,        // 代理生命周期(分钟)
    val rotationIntervalMinutes: Int = 7,      // 轮换间隔(分钟)
    val lowWatermark: Int = 50,                // 低水位线
    val targetSize: Int = 200,                 // 目标池大小
    val autoStartEnabled: Boolean = true,      // 自动启动
    val preMarketStartMinutes: Int = 2,        // 盘前启动时间(分钟)
    val postMarketStopMinutes: Int = 30        // 盘后停止时间(分钟)
)
```

### Alert (告警信息)

```kotlin
data class Alert(
    val id: String,                     // 告警ID
    val level: AlertLevel,              // 告警级别
    val title: String,                  // 告警标题
    val message: String,                // 告警详情
    val market: String?,                // 相关市场
    val component: String?,             // 组件名称
    val timestamp: String,              // 时间戳 (ISO 8601)
    val acknowledged: Boolean           // 是否已确认
)

enum class AlertLevel {
    INFO, WARNING, ERROR, CRITICAL
}
```

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 请求成功 | 正常处理响应数据 |
| 400 | 请求参数错误 | 检查请求参数格式 |
| 404 | 资源不存在 | 检查市场/模式参数是否正确 |
| 500 | 服务器内部错误 | 重试请求，记录错误日志 |
| 503 | 服务不可用 | 等待服务恢复，使用降级方案 |

### 错误响应格式

```json
{
  "status": "error",
  "error": {
    "code": "PROXY_POOL_NOT_FOUND",
    "message": "Proxy pool manager not found for hk/live",
    "details": {
      "market": "hk",
      "mode": "live"
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `PROXY_POOL_NOT_FOUND` | 代理池不存在 | 检查市场/模式参数 |
| `SERVICE_NOT_RUNNING` | 服务未运行 | 先启动服务 |
| `INVALID_MARKET` | 无效市场代码 | 使用 cn/hk/us |
| `INVALID_MODE` | 无效模式 | 使用 live/backfill |
| `NO_PROXY_AVAILABLE` | 无可用代理 | 等待代理池刷新 |
| `CONFIG_UPDATE_FAILED` | 配置更新失败 | 检查配置参数 |

## Kotlin 集成示例

### 1. Retrofit 接口定义

```kotlin
interface ProxyPoolService {

    @POST("/api/v1/rpc")
    suspend fun getProxy(@Body request: RpcRequest): Response<RpcResponse>

    @POST("/api/v1/rpc")
    suspend fun reportFailure(@Body request: RpcRequest): Response<RpcResponse>

    @POST("/api/v1/rpc")
    suspend fun ping(@Body request: RpcRequest): Response<PingResponse>

    @GET("/api/v1/pools")
    suspend fun getAllPools(): Response<PoolsResponse>

    @GET("/api/v1/status")
    suspend fun getStatus(
        @Query("market") market: String,
        @Query("mode") mode: String = "live"
    ): Response<StatusResponse>

    @GET("/api/v1/metrics")
    suspend fun getMetrics(
        @Query("market") market: String,
        @Query("mode") mode: String = "live"
    ): Response<MetricsResponse>

    @POST("/api/v1/start")
    suspend fun startService(
        @Query("market") market: String,
        @Query("mode") mode: String = "live"
    ): Response<OperationResponse>

    @POST("/api/v1/stop")
    suspend fun stopService(
        @Query("market") market: String,
        @Query("mode") mode: String = "live"
    ): Response<OperationResponse>
}
```

### 2. 数据类定义

```kotlin
// RPC 请求/响应
data class RpcRequest(
    val event: String,
    val market: String = "hk",
    val mode: String = "live",
    val proxy_type: String? = "short",
    val proxy_addr: String? = null
)

data class RpcResponse(
    val status: String,
    val proxy: String? = null,
    val message: String? = null
)

data class PingResponse(
    val status: String,
    val message: String,
    val market: String,
    val mode: String,
    val running: Boolean,
    val market_status: String
)

// 代理池列表响应
data class PoolsResponse(
    val pools: List<ProxyPoolInfo>
)

data class ProxyPoolInfo(
    val key: String,
    val market: String,
    val mode: String,
    val running: Boolean,
    val status: PoolStatusDetail
)

// 状态响应
data class StatusResponse(
    val status: String,
    val running: Boolean,
    val market: String,
    val mode: String,
    val market_status: String,
    val stats: PoolStats
)

// 指标响应
data class MetricsResponse(
    val running: Int,
    val active_pool: String?,
    val size_active: Int,
    val size_standby: Int,
    val total_pool_size: Int,
    val success_rate: Double,
    val total_requests: Long,
    val success_count: Long,
    val failure_count: Long
)

// 操作响应
data class OperationResponse(
    val status: String,
    val message: String
)
```

### 3. 代理池客户端实现

```kotlin
class ProxyPoolClient(
    private val baseUrl: String = "http://localhost:8080",
    private val httpClient: OkHttpClient = OkHttpClient()
) {

    private val retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .addConverterFactory(GsonConverterFactory.create())
        .client(httpClient)
        .build()

    private val service = retrofit.create(ProxyPoolService::class.java)

    /**
     * 获取可用代理
     */
    suspend fun getProxy(
        market: String = "hk",
        mode: String = "live",
        proxyType: String = "short"
    ): Result<String> {
        return try {
            val request = RpcRequest(
                event = "get_proxy",
                market = market,
                mode = mode,
                proxy_type = proxyType
            )

            val response = service.getProxy(request)
            if (response.isSuccessful) {
                val body = response.body()
                if (body?.status == "ok" && body.proxy != null) {
                    Result.success(body.proxy)
                } else {
                    Result.failure(Exception("No proxy available"))
                }
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 报告代理失败
     */
    suspend fun reportProxyFailure(
        proxyAddr: String,
        market: String = "hk",
        mode: String = "live"
    ): Result<String> {
        return try {
            val request = RpcRequest(
                event = "report_failure",
                market = market,
                mode = mode,
                proxy_addr = proxyAddr
            )

            val response = service.reportFailure(request)
            if (response.isSuccessful) {
                val body = response.body()
                Result.success(body?.message ?: "Reported successfully")
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 检查服务健康状态
     */
    suspend fun ping(market: String = "hk", mode: String = "live"): Result<PingResponse> {
        return try {
            val request = RpcRequest(
                event = "ping",
                market = market,
                mode = mode
            )

            val response = service.ping(request)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 获取所有代理池状态
     */
    suspend fun getAllPools(): Result<List<ProxyPoolInfo>> {
        return try {
            val response = service.getAllPools()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.pools)
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * 获取指定市场状态
     */
    suspend fun getMarketStatus(
        market: String,
        mode: String = "live"
    ): Result<StatusResponse> {
        return try {
            val response = service.getStatus(market, mode)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("HTTP ${response.code()}: ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### 4. 使用示例

```kotlin
class MarketDataCollector {

    private val proxyPoolClient = ProxyPoolClient("http://proxy-pool.saturn.com:8080")

    suspend fun collectData(market: String) {
        // 1. 检查代理池状态
        val status = proxyPoolClient.getMarketStatus(market).getOrNull()
        if (status?.running != true) {
            println("代理池未运行，无法采集数据")
            return
        }

        // 2. 获取代理
        val proxyResult = proxyPoolClient.getProxy(market)
        if (proxyResult.isFailure) {
            println("获取代理失败: ${proxyResult.exceptionOrNull()?.message}")
            return
        }

        val proxy = proxyResult.getOrNull()!!
        println("使用代理: $proxy")

        try {
            // 3. 使用代理采集数据
            val data = collectDataWithProxy(proxy)
            println("数据采集成功: $data")

        } catch (e: Exception) {
            // 4. 采集失败时报告代理问题
            println("数据采集失败: ${e.message}")
            proxyPoolClient.reportProxyFailure(proxy, market)
        }
    }

    private suspend fun collectDataWithProxy(proxy: String): String {
        // 模拟数据采集逻辑
        delay(1000)
        return "market data from $proxy"
    }
}

// 使用示例
fun main() = runBlocking {
    val collector = MarketDataCollector()

    // 采集香港市场数据
    collector.collectData("hk")

    // 采集美股数据
    collector.collectData("us")
}
```

### 5. 异常处理和重试机制

```kotlin
class RobustProxyPoolClient(
    private val client: ProxyPoolClient,
    private val maxRetries: Int = 3,
    private val retryDelayMs: Long = 1000
) {

    suspend fun getProxyWithRetry(
        market: String,
        mode: String = "live"
    ): String? {
        repeat(maxRetries) { attempt ->
            try {
                val result = client.getProxy(market, mode)
                if (result.isSuccess) {
                    return result.getOrNull()
                }

                // 如果不是最后一次尝试，等待后重试
                if (attempt < maxRetries - 1) {
                    delay(retryDelayMs * (attempt + 1)) // 指数退避
                }
            } catch (e: Exception) {
                println("获取代理失败 (尝试 ${attempt + 1}/$maxRetries): ${e.message}")
                if (attempt < maxRetries - 1) {
                    delay(retryDelayMs * (attempt + 1))
                }
            }
        }
        return null
    }

    suspend fun healthCheck(): Boolean {
        return try {
            val result = client.ping()
            result.isSuccess
        } catch (e: Exception) {
            false
        }
    }
}
```

## 最佳实践

### 1. 代理获取策略

```kotlin
// 推荐：使用缓存和轮换策略
class ProxyManager {
    private var currentProxy: String? = null
    private var lastProxyTime = 0L
    private val proxyTtlMs = 300_000L // 5分钟TTL

    suspend fun getValidProxy(market: String): String? {
        val now = System.currentTimeMillis()

        // 如果当前代理仍然有效，直接返回
        if (currentProxy != null && (now - lastProxyTime) < proxyTtlMs) {
            return currentProxy
        }

        // 获取新代理
        val newProxy = proxyPoolClient.getProxy(market).getOrNull()
        if (newProxy != null) {
            currentProxy = newProxy
            lastProxyTime = now
        }

        return newProxy
    }
}
```

### 2. 错误处理

```kotlin
// 优雅的错误处理
suspend fun safeGetProxy(market: String): String? {
    return try {
        proxyPoolClient.getProxy(market).getOrNull()
    } catch (e: SocketTimeoutException) {
        println("代理服务连接超时，使用备用方案")
        null
    } catch (e: ConnectException) {
        println("代理服务不可达，检查网络连接")
        null
    } catch (e: Exception) {
        println("获取代理时发生未知错误: ${e.message}")
        null
    }
}
```

### 3. 监控集成

```kotlin
// 集成应用监控
class MonitoredProxyClient(
    private val client: ProxyPoolClient,
    private val metrics: MetricsCollector
) {

    suspend fun getProxy(market: String): Result<String> {
        val startTime = System.currentTimeMillis()

        return try {
            val result = client.getProxy(market)
            val duration = System.currentTimeMillis() - startTime

            if (result.isSuccess) {
                metrics.recordProxyRequestSuccess(market, duration)
            } else {
                metrics.recordProxyRequestFailure(market, duration)
            }

            result
        } catch (e: Exception) {
            val duration = System.currentTimeMillis() - startTime
            metrics.recordProxyRequestError(market, duration, e)
            Result.failure(e)
        }
    }
}
```

### 4. 配置管理

```kotlin
// 配置驱动的客户端
data class ProxyPoolConfig(
    val baseUrl: String = "http://localhost:8080",
    val connectTimeoutMs: Long = 5000,
    val readTimeoutMs: Long = 10000,
    val maxRetries: Int = 3,
    val retryDelayMs: Long = 1000,
    val defaultMarket: String = "hk",
    val defaultMode: String = "live"
)

class ConfigurableProxyPoolClient(
    private val config: ProxyPoolConfig
) {
    private val client = ProxyPoolClient(
        baseUrl = config.baseUrl,
        httpClient = OkHttpClient.Builder()
            .connectTimeout(config.connectTimeoutMs, TimeUnit.MILLISECONDS)
            .readTimeout(config.readTimeoutMs, TimeUnit.MILLISECONDS)
            .build()
    )

    // 使用配置中的默认值
    suspend fun getProxy(): Result<String> {
        return client.getProxy(config.defaultMarket, config.defaultMode)
    }
}
```

---

## 总结

这份文档提供了完整的 FastAPI 代理池服务接口规范，包括：

1. **完整的 API 接口**：涵盖代理获取、状态查询、配置管理等所有功能
2. **详细的 Kotlin 集成示例**：包括 Retrofit 接口定义和客户端实现
3. **最佳实践指导**：错误处理、重试机制、监控集成等
4. **生产就绪的代码**：异常处理、配置管理、健康检查等

通过这份文档，Kotlin 项目可以快速集成代理池服务，实现高可用的代理获取和管理功能。