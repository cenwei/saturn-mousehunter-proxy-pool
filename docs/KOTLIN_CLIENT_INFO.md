# Saturn MouseHunter 代理池系统 - Kotlin客户端序列化对象

## 📋 客户端信息

**客户端类型**: Kotlin (Quickly Framework)
**序列化库**: Kotlinx Serialization
**目标平台**: JVM/Android
**API基础URL**: http://192.168.8.168:8001/api/v1

## 🎯 重要说明

客户端使用Kotlin Quickly框架，需要精确的序列化对象定义以避免反复试错，提高开发效率。所有API响应字段必须与服务端完全匹配，确保序列化/反序列化的成功。

---

## 📦 依赖配置

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
    implementation("io.ktor:ktor-client-core:2.3.0")
    implementation("io.ktor:ktor-client-cio:2.3.0")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.0")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.0")
}
```

---

## 🔧 基础类型定义

```kotlin
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName

/**
 * 市场代码枚举
 */
@Serializable
enum class MarketCode {
    @SerialName("cn") CN,
    @SerialName("hk") HK,
    @SerialName("us") US
}

/**
 * 市场代码（大写）枚举
 */
@Serializable
enum class MarketCodeUpper {
    @SerialName("CN") CN,
    @SerialName("HK") HK,
    @SerialName("US") US
}

/**
 * 运行模式枚举
 */
@Serializable
enum class OperationMode {
    @SerialName("live") LIVE,
    @SerialName("backfill") BACKFILL
}

/**
 * 代理池名称枚举
 */
@Serializable
enum class PoolName {
    @SerialName("A") A,
    @SerialName("B") B
}

/**
 * 代理类型枚举
 */
@Serializable
enum class ProxyType {
    @SerialName("short") SHORT,
    @SerialName("long") LONG
}

/**
 * 操作状态枚举
 */
@Serializable
enum class OperationStatus {
    @SerialName("running") RUNNING,
    @SerialName("stopped") STOPPED,
    @SerialName("error") ERROR
}

/**
 * 交易日类型枚举
 */
@Serializable
enum class TradingDayType {
    @SerialName("NORMAL") NORMAL,
    @SerialName("HALF_DAY") HALF_DAY,
    @SerialName("HOLIDAY") HOLIDAY,
    @SerialName("WEEKEND") WEEKEND
}

/**
 * 交易时段类型枚举
 */
@Serializable
enum class TradingSessionType {
    @SerialName("full_day") FULL_DAY,
    @SerialName("morning_only") MORNING_ONLY,
    @SerialName("afternoon_only") AFTERNOON_ONLY
}

/**
 * 服务操作状态枚举
 */
@Serializable
enum class ServiceOperationStatus {
    @SerialName("started") STARTED,
    @SerialName("stopped") STOPPED,
    @SerialName("already_running") ALREADY_RUNNING,
    @SerialName("already_stopped") ALREADY_STOPPED,
    @SerialName("error") ERROR
}

/**
 * RPC事件类型枚举
 */
@Serializable
enum class RpcEvent {
    @SerialName("get_proxy") GET_PROXY,
    @SerialName("report_failure") REPORT_FAILURE,
    @SerialName("get_status") GET_STATUS,
    @SerialName("ping") PING
}
```

这个文件将作为Kotlin客户端序列化的基础配置。接下来我将创建完整的Kotlin数据类定义。