# FastAPI 代理池服务 - Kotlin 快速集成指南

> 快速上手指南：5分钟集成代理池服务到您的 Kotlin 项目

## 🚀 快速开始

### 1. 添加依赖

```kotlin
// build.gradle.kts
dependencies {
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
```

### 2. 核心接口定义

```kotlin
interface ProxyPoolApi {
    @POST("/api/v1/rpc")
    suspend fun getProxy(@Body request: ProxyRequest): Response<ProxyResponse>

    @POST("/api/v1/rpc")
    suspend fun reportFailure(@Body request: FailureRequest): Response<BaseResponse>

    @GET("/api/v1/status")
    suspend fun getStatus(@Query("market") market: String): Response<StatusResponse>
}

// 请求模型
data class ProxyRequest(
    val event: String = "get_proxy",
    val market: String = "hk",
    val mode: String = "live",
    val proxy_type: String = "short"
)

data class FailureRequest(
    val event: String = "report_failure",
    val market: String,
    val mode: String = "live",
    val proxy_addr: String
)

// 响应模型
data class ProxyResponse(
    val status: String,
    val proxy: String?
)

data class BaseResponse(
    val status: String,
    val message: String?
)

data class StatusResponse(
    val status: String,
    val running: Boolean,
    val market: String,
    val stats: ProxyStats
)

data class ProxyStats(
    val total_pool_size: Int,
    val success_rate: Double,
    val active_pool: String
)
```

### 3. 客户端实现

```kotlin
class ProxyPoolClient(baseUrl: String = "http://localhost:8080") {

    private val api = Retrofit.Builder()
        .baseUrl(baseUrl)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(ProxyPoolApi::class.java)

    /**
     * 获取可用代理 - 最常用方法
     */
    suspend fun getProxy(market: String = "hk"): String? {
        return try {
            val response = api.getProxy(ProxyRequest(market = market))
            if (response.isSuccessful && response.body()?.status == "ok") {
                response.body()?.proxy
            } else null
        } catch (e: Exception) {
            println("获取代理失败: ${e.message}")
            null
        }
    }

    /**
     * 报告代理失败 - 重要！代理不可用时必须调用
     */
    suspend fun reportFailure(proxyAddr: String, market: String = "hk"): Boolean {
        return try {
            val response = api.reportFailure(
                FailureRequest(market = market, proxy_addr = proxyAddr)
            )
            response.isSuccessful
        } catch (e: Exception) {
            false
        }
    }

    /**
     * 检查服务状态
     */
    suspend fun isServiceHealthy(market: String = "hk"): Boolean {
        return try {
            val response = api.getStatus(market)
            response.isSuccessful && response.body()?.running == true
        } catch (e: Exception) {
            false
        }
    }
}
```

### 4. 实际使用示例

```kotlin
class DataCollector {
    private val proxyClient = ProxyPoolClient("http://proxy-pool.saturn.com:8080")

    suspend fun collectMarketData(market: String = "hk") {
        // 1. 获取代理
        val proxy = proxyClient.getProxy(market)
        if (proxy == null) {
            println("无可用代理")
            return
        }

        try {
            // 2. 使用代理请求数据
            val data = requestDataWithProxy(proxy)
            println("数据采集成功: $data")

        } catch (e: Exception) {
            // 3. 失败时报告代理问题（重要！）
            proxyClient.reportFailure(proxy, market)
            println("代理失败已报告: $proxy")
        }
    }

    private suspend fun requestDataWithProxy(proxy: String): String {
        // 您的数据请求逻辑，使用 proxy 作为代理地址
        // 例如: HttpClient.newBuilder().proxy(ProxySelector.of(proxy))
        return "mock data"
    }
}
```

## 🎯 最重要的3个接口

### 1. 获取代理 (最常用)

```http
POST /api/v1/rpc
{
  "event": "get_proxy",
  "market": "hk",
  "mode": "live",
  "proxy_type": "short"
}

Response:
{
  "status": "ok",
  "proxy": "192.168.1.100:8080"
}
```

### 2. 报告失败 (必须调用)

```http
POST /api/v1/rpc
{
  "event": "report_failure",
  "market": "hk",
  "mode": "live",
  "proxy_addr": "192.168.1.100:8080"
}

Response:
{
  "status": "ok",
  "message": "192.168.1.100:8080 marked as failure"
}
```

### 3. 健康检查

```http
GET /api/v1/status?market=hk

Response:
{
  "status": "ok",
  "running": true,
  "market": "hk",
  "stats": {
    "total_pool_size": 380,
    "success_rate": 95.2,
    "active_pool": "A"
  }
}
```

## 📋 支持的市场

| 市场代码 | 说明 | 交易时间 |
|----------|------|----------|
| `cn` | 中国A股 | 09:30-15:10 |
| `hk` | 香港股市 | 09:30-16:15 |
| `us` | 美股 | 09:30-16:00 |

## ⚠️ 重要注意事项

1. **必须报告失败**: 当代理不可用时，务必调用 `reportFailure` 接口
2. **自动轮换**: 系统每7分钟自动轮换代理池，无需手动管理
3. **交易时间**: 服务会在交易时间自动启动，非交易时间自动停止
4. **重试机制**: 建议实现重试机制，网络异常时重试2-3次

## 🔧 故障排除

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `No proxy available` | 代理池为空 | 等待1-2分钟后重试 |
| `Service not running` | 服务未启动 | 检查是否在交易时间 |
| `Invalid market` | 市场代码错误 | 使用 cn/hk/us |

### 健康检查

```kotlin
// 推荐：使用前检查服务状态
suspend fun safeGetProxy(market: String): String? {
    if (!proxyClient.isServiceHealthy(market)) {
        println("服务不健康，跳过代理获取")
        return null
    }
    return proxyClient.getProxy(market)
}
```

## 🌐 环境地址

| 环境 | 地址 |
|------|------|
| 开发 | `http://localhost:8080` |
| 测试 | `http://proxy-pool-test.saturn.com:8080` |
| 生产 | `http://proxy-pool.saturn.com:8080` |

---

**这就是全部！** 使用这4个核心方法就能完整集成代理池服务：
- `getProxy()` - 获取代理
- `reportFailure()` - 报告失败
- `isServiceHealthy()` - 健康检查
- 在 try-catch 中使用代理