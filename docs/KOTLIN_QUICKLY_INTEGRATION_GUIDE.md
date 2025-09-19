# Saturn MouseHunter 代理池系统 - Kotlin Quickly 完整集成指南

## 📋 项目信息

**客户端框架**: Kotlin Quickly Framework
**序列化库**: Kotlinx Serialization
**目标平台**: JVM/Android
**API基础URL**: http://192.168.8.168:8001/api/v1

## 🎯 重要说明

此集成指南专为Kotlin Quickly框架设计，提供完整的序列化对象定义，避免前端反复试错，提高开发效率。

## 📦 项目依赖配置

### build.gradle.kts
```kotlin
plugins {
    kotlin("jvm") version "1.9.10"
    kotlin("plugin.serialization") version "1.9.10"
}

dependencies {
    // Kotlinx Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")

    // Ktor Client (推荐用于HTTP请求)
    implementation("io.ktor:ktor-client-core:2.3.5")
    implementation("io.ktor:ktor-client-cio:2.3.5")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.5")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.5")

    // 或者使用OkHttp (备选方案)
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // 协程支持
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
}
```

### gradle.properties
```properties
kotlin.code.style=official
kotlin.serialization.json.useArrayPolymorphism=true
```

## 📁 文件结构

```
src/main/kotlin/
├── com/saturn/mousehunter/proxypool/
│   ├── api/
│   │   ├── ProxyPoolApiModels.kt           # 序列化数据类
│   │   ├── ProxyPoolApiClient.kt           # API客户端接口
│   │   └── ProxyPoolApiClientImpl.kt       # API客户端实现
│   ├── example/
│   │   └── KotlinClientUsageExample.kt     # 使用示例
│   └── utils/
│       ├── JsonUtils.kt                    # JSON工具类
│       └── ApiResponseHandler.kt           # 响应处理工具
```

## 🔧 核心文件说明

### 1. ProxyPoolApiModels.kt
包含所有API的序列化数据类：
- 47个@Serializable数据类
- 完整的枚举定义 (MarketCode, OperationStatus等)
- 精确的@SerialName映射
- 支持所有API端点的响应结构

### 2. KotlinClientUsageExample.kt
完整的使用示例，包括：
- API客户端实现
- 8个核心API调用示例
- 错误处理演示
- JSON序列化工具

## 🚀 快速开始

### 第一步：复制核心文件
```bash
# 复制序列化数据类
cp docs/ProxyPoolApiModels.kt src/main/kotlin/com/saturn/mousehunter/proxypool/api/

# 复制使用示例
cp docs/KotlinClientUsageExample.kt src/main/kotlin/com/saturn/mousehunter/proxypool/example/
```

### 第二步：基础API调用
```kotlin
import com.saturn.mousehunter.proxypool.api.*
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    val client = ProxyPoolApiClientExample()

    // 获取代理池状态
    val status = client.getProxyPoolStatus(MarketCode.CN)
    println("代理池状态: ${status.status}")
    println("成功率: ${status.stats.successRate}%")

    // 获取代理IP
    val proxyResponse = client.getProxy(MarketCode.CN)
    proxyResponse.proxy?.let { proxy ->
        println("获取到代理: $proxy")
    }

    client.close()
}
```

### 第三步：集成到Kotlin Quickly项目
```kotlin
// 在你的Kotlin Quickly服务中
class TradingService {
    private val proxyClient = ProxyPoolApiClientExample()

    suspend fun startTradingSession(market: MarketCode) {
        // 检查交易日类型
        val tradingInfo = proxyClient.getTradingDayInfo(market)

        when (tradingInfo.dayType) {
            TradingDayType.NORMAL -> {
                // 正常交易日，启动完整服务
                proxyClient.startProxyPoolService(market)
            }
            TradingDayType.HALF_DAY -> {
                // 半日交易，调整配置
                val config = ConfigUpdateRequest(
                    rotationIntervalMinutes = 5, // 缩短轮换间隔
                    proxyLifetimeMinutes = 8     // 缩短生命周期
                )
                proxyClient.updateConfig(market, config)
                proxyClient.startProxyPoolService(market)
            }
            TradingDayType.HOLIDAY, TradingDayType.WEEKEND -> {
                // 非交易日，不启动服务
                println("${tradingInfo.statusDescription}, 跳过代理池启动")
            }
        }
    }
}
```

## 📊 API端点覆盖清单

### ✅ 标准代理池接口 (已覆盖)
- [x] GET `/status` - ProxyPoolStatusResponse
- [x] POST `/start` - ServiceOperationResponse
- [x] POST `/stop` - ServiceStopResponse
- [x] POST `/rpc` - GetProxyResponse/ReportFailureResponse/RpcStatusResponse

### ✅ 增强交易日接口 (已覆盖)
- [x] GET `/enhanced/trading-day/{market}` - TradingDayInfo
- [x] GET `/enhanced/trading-day/{market}/status` - MarketRealtimeStatus
- [x] GET `/enhanced/scheduler/status` - EnhancedSchedulerStatus
- [x] POST `/enhanced/scheduler/force-start/{market}` - EnhancedForceOperationResponse
- [x] POST `/enhanced/scheduler/force-stop/{market}` - EnhancedForceOperationResponse
- [x] GET `/enhanced/macl/day-type/{market}` - MaclDayTypeResponse
- [x] GET `/enhanced/trading-modes/summary` - TradingModesSummary

### ✅ 批量操作接口 (已覆盖)
- [x] POST `/batch/start` - BatchOperationResponse
- [x] POST `/batch/stop` - BatchOperationResponse

### ✅ 配置管理接口 (已覆盖)
- [x] GET `/config` - ConfigResponse
- [x] POST `/config` - ConfigUpdateResponse

### ✅ 错误处理 (已覆盖)
- [x] ErrorResponse - 统一错误响应格式
- [x] ApiResponse<T> - 通用响应包装器

## 🔍 关键序列化对象

### 核心枚举类型
```kotlin
@Serializable
enum class MarketCode {
    @SerialName("cn") CN,
    @SerialName("hk") HK,
    @SerialName("us") US
}

@Serializable
enum class TradingDayType {
    @SerialName("NORMAL") NORMAL,
    @SerialName("HALF_DAY") HALF_DAY,
    @SerialName("HOLIDAY") HOLIDAY,
    @SerialName("WEEKEND") WEEKEND
}
```

### 关键数据结构
```kotlin
@Serializable
data class TradingDayInfo(
    @SerialName("market") val market: MarketCodeUpper,
    @SerialName("date") val date: String,
    @SerialName("day_type") val dayType: TradingDayType,
    @SerialName("session_type") val sessionType: TradingSessionType,
    @SerialName("is_trading_day") val isTradingDay: Boolean,
    @SerialName("status_description") val statusDescription: String,
    @SerialName("trading_hours") val tradingHours: TradingHours? = null
)

@Serializable
data class ProxyPoolStats(
    @SerialName("pool_a_size") val poolASize: Int,
    @SerialName("pool_b_size") val poolBSize: Int,
    @SerialName("active_pool") val activePool: PoolName,
    @SerialName("total_proxies") val totalProxies: Int,
    @SerialName("success_rate") val successRate: Double,
    @SerialName("total_requests") val totalRequests: Int,
    @SerialName("success_count") val successCount: Int,
    @SerialName("failure_count") val failureCount: Int,
    @SerialName("last_rotation_at") val lastRotationAt: String,
    @SerialName("started_at") val startedAt: String,
    @SerialName("uptime_seconds") val uptimeSeconds: Int
)
```

## 🛠️ JSON处理工具

### 配置Json实例
```kotlin
val json = Json {
    ignoreUnknownKeys = true        // 忽略未知字段
    coerceInputValues = true        // 强制转换输入值
    prettyPrint = true              // 美化输出
    encodeDefaults = false          // 不编码默认值
}
```

### 序列化/反序列化示例
```kotlin
// 序列化请求对象
val request = RpcRequest(
    event = RpcEvent.GET_PROXY,
    proxyType = ProxyType.SHORT,
    market = MarketCode.CN
)
val requestJson = json.encodeToString(request)

// 反序列化响应对象
val responseJson = """{"status":"ok","proxy":"192.168.1.100:8080"}"""
val response = json.decodeFromString<GetProxyResponse>(responseJson)
```

## 📝 测试建议

### 单元测试示例
```kotlin
@Test
fun testTradingDayInfoSerialization() {
    val tradingInfo = TradingDayInfo(
        market = MarketCodeUpper.CN,
        date = "2024-12-25",
        dayType = TradingDayType.HOLIDAY,
        sessionType = TradingSessionType.FULL_DAY,
        isTradingDay = false,
        statusDescription = "圣诞节假期"
    )

    val json = Json.encodeToString(tradingInfo)
    val decoded = Json.decodeFromString<TradingDayInfo>(json)

    assertEquals(tradingInfo, decoded)
}
```

### 集成测试示例
```kotlin
@Test
fun testApiClientIntegration() = runBlocking {
    val client = ProxyPoolApiClientExample()

    try {
        val status = client.getProxyPoolStatus(MarketCode.CN)
        assertNotNull(status.stats)
        assertTrue(status.stats.totalProxies >= 0)
    } finally {
        client.close()
    }
}
```

## ⚡ 性能优化建议

### 1. 连接池复用
```kotlin
val client = HttpClient(CIO) {
    engine {
        maxConnectionsCount = 10
        endpoint {
            maxConnectionsPerRoute = 5
            pipelineMaxSize = 20
            keepAliveTime = 5000
            connectTimeout = 5000
            connectAttempts = 3
        }
    }
}
```

### 2. JSON解析优化
```kotlin
// 预编译序列化器
val statusSerializer = ProxyPoolStatusResponse.serializer()
val responseJson = client.get("$baseUrl/status").bodyAsText()
val status = json.decodeFromString(statusSerializer, responseJson)
```

### 3. 协程优化
```kotlin
// 并发获取多市场状态
val markets = listOf(MarketCode.CN, MarketCode.HK, MarketCode.US)
val statuses = markets.map { market ->
    async { client.getProxyPoolStatus(market) }
}.awaitAll()
```

## 🚨 常见问题解决

### Q1: 序列化失败
**问题**: `kotlinx.serialization.SerializationException`
**解决**: 检查@SerialName是否与API返回字段完全匹配

### Q2: 网络连接超时
**问题**: HTTP请求超时
**解决**: 调整客户端配置的超时设置

### Q3: 空值处理
**问题**: 可空字段反序列化失败
**解决**: 使用适当的可空类型和默认值

## 🎉 总结

此Kotlin序列化对象集完全适配Saturn MouseHunter代理池API，支持：

- ✅ **完整API覆盖**: 15个核心端点全部支持
- ✅ **精确字段映射**: @SerialName确保序列化兼容性
- ✅ **类型安全**: 强类型枚举和数据类
- ✅ **错误处理**: 完整的异常处理机制
- ✅ **使用示例**: 8个实际应用场景
- ✅ **生产就绪**: 支持连接池、超时、重试等

使用这些序列化对象，你的Kotlin Quickly客户端将避免反复试错，实现高效稳定的API集成。