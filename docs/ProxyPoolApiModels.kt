/**
 * Saturn MouseHunter 代理池系统 - Kotlin 序列化数据类
 *
 * 适用于 Kotlin Quickly 客户端
 * 使用 kotlinx.serialization 进行序列化
 *
 * @version 2.0.0
 * @generated 2025-09-18
 * @client Kotlin Quickly Framework
 */

package com.saturn.mousehunter.proxypool.api

import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName

// ============================================================================
// 基础枚举类型
// ============================================================================

@Serializable
enum class MarketCode {
    @SerialName("cn") CN,
    @SerialName("hk") HK,
    @SerialName("us") US
}

@Serializable
enum class MarketCodeUpper {
    @SerialName("CN") CN,
    @SerialName("HK") HK,
    @SerialName("US") US
}

@Serializable
enum class OperationMode {
    @SerialName("live") LIVE,
    @SerialName("backfill") BACKFILL
}

@Serializable
enum class PoolName {
    @SerialName("A") A,
    @SerialName("B") B
}

@Serializable
enum class ProxyType {
    @SerialName("short") SHORT,
    @SerialName("long") LONG
}

@Serializable
enum class OperationStatus {
    @SerialName("running") RUNNING,
    @SerialName("stopped") STOPPED,
    @SerialName("error") ERROR
}

@Serializable
enum class TradingDayType {
    @SerialName("NORMAL") NORMAL,
    @SerialName("HALF_DAY") HALF_DAY,
    @SerialName("HOLIDAY") HOLIDAY,
    @SerialName("WEEKEND") WEEKEND
}

@Serializable
enum class TradingSessionType {
    @SerialName("full_day") FULL_DAY,
    @SerialName("morning_only") MORNING_ONLY,
    @SerialName("afternoon_only") AFTERNOON_ONLY
}

@Serializable
enum class ServiceOperationStatus {
    @SerialName("started") STARTED,
    @SerialName("stopped") STOPPED,
    @SerialName("already_running") ALREADY_RUNNING,
    @SerialName("already_stopped") ALREADY_STOPPED,
    @SerialName("error") ERROR
}

@Serializable
enum class RpcEvent {
    @SerialName("get_proxy") GET_PROXY,
    @SerialName("report_failure") REPORT_FAILURE,
    @SerialName("get_status") GET_STATUS,
    @SerialName("ping") PING
}

@Serializable
enum class RpcResponseStatus {
    @SerialName("ok") OK,
    @SerialName("error") ERROR
}

@Serializable
enum class ActionTaken {
    @SerialName("marked_failed") MARKED_FAILED,
    @SerialName("removed") REMOVED
}

@Serializable
enum class AffectedPool {
    @SerialName("A") A,
    @SerialName("B") B,
    @SerialName("both") BOTH
}

@Serializable
enum class DataSource {
    @SerialName("macl") MACL,
    @SerialName("calendar_api") CALENDAR_API
}

// ============================================================================
// 核心数据结构
// ============================================================================

/**
 * 交易时间配置
 */
@Serializable
data class TradingHours(
    @SerialName("start") val start: String,
    @SerialName("end") val end: String,
    @SerialName("lunch_break") val lunchBreak: List<String>? = null
)

/**
 * 代理池统计信息
 */
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

/**
 * 交易日信息
 */
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

/**
 * 代理池配置信息
 */
@Serializable
data class ProxyPoolConfigData(
    @SerialName("batch_size") val batchSize: Int,
    @SerialName("proxy_lifetime_minutes") val proxyLifetimeMinutes: Int,
    @SerialName("rotation_interval_minutes") val rotationIntervalMinutes: Int,
    @SerialName("target_size") val targetSize: Int,
    @SerialName("low_watermark") val lowWatermark: Int
)

/**
 * 完整代理池配置
 */
@Serializable
data class ProxyPoolConfig(
    @SerialName("hailiang_api_url") val hailiangApiUrl: String,
    @SerialName("hailiang_enabled") val hailiangEnabled: Boolean,
    @SerialName("batch_size") val batchSize: Int,
    @SerialName("proxy_lifetime_minutes") val proxyLifetimeMinutes: Int,
    @SerialName("rotation_interval_minutes") val rotationIntervalMinutes: Int,
    @SerialName("low_watermark") val lowWatermark: Int,
    @SerialName("target_size") val targetSize: Int,
    @SerialName("auto_start_enabled") val autoStartEnabled: Boolean,
    @SerialName("pre_market_start_minutes") val preMarketStartMinutes: Int,
    @SerialName("post_market_stop_minutes") val postMarketStopMinutes: Int,
    @SerialName("backfill_enabled") val backfillEnabled: Boolean,
    @SerialName("backfill_duration_hours") val backfillDurationHours: Int,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
    @SerialName("is_active") val isActive: Boolean
)

// ============================================================================
// API 请求数据类
// ============================================================================

/**
 * RPC请求
 */
@Serializable
data class RpcRequest(
    @SerialName("event") val event: RpcEvent,
    @SerialName("proxy_type") val proxyType: ProxyType? = ProxyType.SHORT,
    @SerialName("proxy_addr") val proxyAddr: String? = null,
    @SerialName("market") val market: MarketCode? = MarketCode.CN,
    @SerialName("mode") val mode: OperationMode? = OperationMode.LIVE
)

/**
 * 批量操作请求
 */
@Serializable
data class BatchOperationRequest(
    @SerialName("markets") val markets: List<MarketCode>,
    @SerialName("mode") val mode: OperationMode = OperationMode.LIVE
)

/**
 * 配置更新请求
 */
@Serializable
data class ConfigUpdateRequest(
    @SerialName("hailiang_api_url") val hailiangApiUrl: String? = null,
    @SerialName("hailiang_enabled") val hailiangEnabled: Boolean? = null,
    @SerialName("batch_size") val batchSize: Int? = null,
    @SerialName("proxy_lifetime_minutes") val proxyLifetimeMinutes: Int? = null,
    @SerialName("rotation_interval_minutes") val rotationIntervalMinutes: Int? = null,
    @SerialName("low_watermark") val lowWatermark: Int? = null,
    @SerialName("target_size") val targetSize: Int? = null,
    @SerialName("auto_start_enabled") val autoStartEnabled: Boolean? = null,
    @SerialName("pre_market_start_minutes") val preMarketStartMinutes: Int? = null,
    @SerialName("post_market_stop_minutes") val postMarketStopMinutes: Int? = null,
    @SerialName("backfill_enabled") val backfillEnabled: Boolean? = null,
    @SerialName("backfill_duration_hours") val backfillDurationHours: Int? = null
)

// ============================================================================
// API 响应数据类
// ============================================================================

/**
 * 代理池状态响应
 */
@Serializable
data class ProxyPoolStatusResponse(
    @SerialName("status") val status: OperationStatus,
    @SerialName("running") val running: Boolean,
    @SerialName("market") val market: String,
    @SerialName("mode") val mode: String,
    @SerialName("market_status") val marketStatus: String,
    @SerialName("stats") val stats: ProxyPoolStats
)

/**
 * 服务操作响应 (启动)
 */
@Serializable
data class ServiceOperationResponse(
    @SerialName("status") val status: ServiceOperationStatus,
    @SerialName("message") val message: String,
    @SerialName("market") val market: String,
    @SerialName("mode") val mode: String,
    @SerialName("started_at") val startedAt: String? = null,
    @SerialName("config") val config: ProxyPoolConfigData? = null
)

/**
 * 最终统计信息
 */
@Serializable
data class FinalStats(
    @SerialName("total_runtime_seconds") val totalRuntimeSeconds: Int,
    @SerialName("total_requests_served") val totalRequestsServed: Int,
    @SerialName("final_success_rate") val finalSuccessRate: Double,
    @SerialName("total_rotations") val totalRotations: Int
)

/**
 * 服务停止响应
 */
@Serializable
data class ServiceStopResponse(
    @SerialName("status") val status: ServiceOperationStatus,
    @SerialName("message") val message: String,
    @SerialName("market") val market: String,
    @SerialName("mode") val mode: String,
    @SerialName("stopped_at") val stoppedAt: String? = null,
    @SerialName("final_stats") val finalStats: FinalStats? = null
)

/**
 * 池信息
 */
@Serializable
data class PoolInfo(
    @SerialName("active_pool") val activePool: PoolName,
    @SerialName("pool_size") val poolSize: Int,
    @SerialName("proxy_age_seconds") val proxyAgeSeconds: Int
)

/**
 * 市场信息
 */
@Serializable
data class MarketInfo(
    @SerialName("market") val market: String,
    @SerialName("is_trading_time") val isTradingTime: Boolean,
    @SerialName("market_status") val marketStatus: String
)

/**
 * 获取代理响应
 */
@Serializable
data class GetProxyResponse(
    @SerialName("status") val status: RpcResponseStatus,
    @SerialName("proxy") val proxy: String? = null,
    @SerialName("pool_info") val poolInfo: PoolInfo? = null,
    @SerialName("market_info") val marketInfo: MarketInfo? = null
)

/**
 * 池影响信息
 */
@Serializable
data class PoolImpact(
    @SerialName("affected_pool") val affectedPool: AffectedPool,
    @SerialName("remaining_size") val remainingSize: Int
)

/**
 * 报告失败响应
 */
@Serializable
data class ReportFailureResponse(
    @SerialName("status") val status: RpcResponseStatus,
    @SerialName("message") val message: String,
    @SerialName("proxy_addr") val proxyAddr: String,
    @SerialName("action_taken") val actionTaken: ActionTaken,
    @SerialName("pool_impact") val poolImpact: PoolImpact? = null
)

/**
 * RPC状态响应
 */
@Serializable
data class RpcStatusResponse(
    @SerialName("status") val status: RpcResponseStatus,
    @SerialName("stats") val stats: Map<String, String>? = null,
    @SerialName("market_status") val marketStatus: String? = null,
    @SerialName("service_mode") val serviceMode: String? = null
)

/**
 * 市场实时状态响应
 */
@Serializable
data class MarketRealtimeStatus(
    @SerialName("market") val market: MarketCodeUpper,
    @SerialName("date") val date: String,
    @SerialName("day_type") val dayType: TradingDayType,
    @SerialName("session_type") val sessionType: TradingSessionType,
    @SerialName("is_trading_day") val isTradingDay: Boolean,
    @SerialName("status_description") val statusDescription: String,
    @SerialName("trading_hours") val tradingHours: TradingHours? = null,
    @SerialName("current_time") val currentTime: String,
    @SerialName("is_market_open") val isMarketOpen: Boolean,
    @SerialName("should_start_session") val shouldStartSession: Boolean,
    @SerialName("should_stop_session") val shouldStopSession: Boolean
)

/**
 * 市场调度器信息
 */
@Serializable
data class MarketSchedulerInfo(
    @SerialName("running") val running: Boolean,
    @SerialName("auto_start_enabled") val autoStartEnabled: Boolean,
    @SerialName("pre_market_minutes") val preMarketMinutes: Int,
    @SerialName("post_market_minutes") val postMarketMinutes: Int,
    @SerialName("trading_summary") val tradingSummary: TradingDayInfo,
    @SerialName("should_start") val shouldStart: Boolean,
    @SerialName("should_stop") val shouldStop: Boolean,
    @SerialName("trading_day_type") val tradingDayType: String,
    @SerialName("session_type") val sessionType: String,
    @SerialName("status_description") val statusDescription: String,
    @SerialName("trading_hours") val tradingHours: TradingHours
)

/**
 * 增强调度器状态响应
 */
@Serializable
data class EnhancedSchedulerStatus(
    @SerialName("scheduler_running") val schedulerRunning: Boolean,
    @SerialName("enhanced_features") val enhancedFeatures: Boolean,
    @SerialName("markets") val markets: Map<String, MarketSchedulerInfo>
)

/**
 * 增强强制操作响应
 */
@Serializable
data class EnhancedForceOperationResponse(
    @SerialName("status") val status: ServiceOperationStatus,
    @SerialName("message") val message: String,
    @SerialName("trading_info") val tradingInfo: TradingDayInfo? = null
)

/**
 * MACL交易日类型响应
 */
@Serializable
data class MaclDayTypeResponse(
    @SerialName("market") val market: String,
    @SerialName("date") val date: String,
    @SerialName("day_type") val dayType: TradingDayType,
    @SerialName("session_type") val sessionType: TradingSessionType,
    @SerialName("is_trading_day") val isTradingDay: Boolean,
    @SerialName("trading_hours") val tradingHours: TradingHours,
    @SerialName("data_source") val dataSource: DataSource
)

/**
 * 市场错误信息
 */
@Serializable
data class MarketError(
    @SerialName("error") val error: String,
    @SerialName("market") val market: String,
    @SerialName("date") val date: String
)

/**
 * 交易模式总结响应
 */
@Serializable
data class TradingModesSummary(
    @SerialName("date") val date: String,
    @SerialName("markets") val markets: Map<String, TradingDayInfo>
)

/**
 * 批量操作结果项
 */
@Serializable
data class BatchOperationResult(
    @SerialName("status") val status: String,
    @SerialName("message") val message: String
)

/**
 * 批量操作响应
 */
@Serializable
data class BatchOperationResponse(
    @SerialName("results") val results: Map<String, BatchOperationResult>
)

/**
 * 配置响应
 */
@Serializable
data class ConfigResponse(
    @SerialName("market") val market: String,
    @SerialName("mode") val mode: String,
    @SerialName("config") val config: ProxyPoolConfig
)

/**
 * 配置更新响应
 */
@Serializable
data class ConfigUpdateResponse(
    @SerialName("status") val status: String,
    @SerialName("message") val message: String,
    @SerialName("market") val market: String,
    @SerialName("mode") val mode: String,
    @SerialName("config") val config: ProxyPoolConfig
)

/**
 * 错误响应
 */
@Serializable
data class ErrorResponse(
    @SerialName("detail") val detail: String,
    @SerialName("status_code") val statusCode: Int,
    @SerialName("timestamp") val timestamp: String,
    @SerialName("request_id") val requestId: String? = null,
    @SerialName("error_code") val errorCode: String? = null
)

// ============================================================================
// 响应包装器
// ============================================================================

/**
 * API响应包装器
 */
@Serializable
sealed class ApiResponse<out T> {
    @Serializable
    @SerialName("success")
    data class Success<T>(val data: T) : ApiResponse<T>()

    @Serializable
    @SerialName("error")
    data class Error(val error: ErrorResponse) : ApiResponse<Nothing>()
}

// ============================================================================
// 常量定义
// ============================================================================

object ProxyPoolConstants {
    const val API_BASE_URL = "http://192.168.8.168:8001/api/v1"

    val MARKET_NAMES = mapOf(
        MarketCodeUpper.CN to "中国A股",
        MarketCodeUpper.HK to "香港股市",
        MarketCodeUpper.US to "美国股市"
    )

    val TRADING_DAY_TYPE_DESCRIPTIONS = mapOf(
        TradingDayType.NORMAL to "正常交易日",
        TradingDayType.HALF_DAY to "半日交易",
        TradingDayType.HOLIDAY to "假期",
        TradingDayType.WEEKEND to "周末"
    )

    val TRADING_SESSION_TYPE_DESCRIPTIONS = mapOf(
        TradingSessionType.FULL_DAY to "全日交易",
        TradingSessionType.MORNING_ONLY to "仅上午交易",
        TradingSessionType.AFTERNOON_ONLY to "仅下午交易"
    )
}