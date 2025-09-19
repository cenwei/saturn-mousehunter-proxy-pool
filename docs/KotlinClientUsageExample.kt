/**
 * Saturn MouseHunter 代理池系统 - Kotlin客户端使用示例
 *
 * 适用于 Kotlin Quickly 框架
 * 展示如何使用序列化数据类进行API调用
 *
 * @version 2.0.0
 * @client Kotlin Quickly Framework
 */

package com.saturn.mousehunter.proxypool.example

import kotlinx.coroutines.runBlocking
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.http.*
import com.saturn.mousehunter.proxypool.api.*

/**
 * Kotlin Quickly 代理池API客户端示例
 */
class ProxyPoolApiClientExample {

    private val client = HttpClient(CIO) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                coerceInputValues = true
            })
        }
    }

    private val baseUrl = ProxyPoolConstants.API_BASE_URL

    /**
     * 示例1: 获取代理池状态
     */
    suspend fun getProxyPoolStatus(market: MarketCode, mode: OperationMode = OperationMode.LIVE): ProxyPoolStatusResponse {
        return client.get("$baseUrl/status") {
            parameter("market", market.name.lowercase())
            parameter("mode", mode.name.lowercase())
        }.body()
    }

    /**
     * 示例2: 启动代理池服务
     */
    suspend fun startProxyPoolService(market: MarketCode, mode: OperationMode = OperationMode.LIVE): ServiceOperationResponse {
        return client.post("$baseUrl/start") {
            parameter("market", market.name.lowercase())
            parameter("mode", mode.name.lowercase())
        }.body()
    }

    /**
     * 示例3: RPC获取代理IP
     */
    suspend fun getProxy(market: MarketCode, proxyType: ProxyType = ProxyType.SHORT): GetProxyResponse {
        val request = RpcRequest(
            event = RpcEvent.GET_PROXY,
            proxyType = proxyType,
            market = MarketCode.valueOf(market.name),
            mode = OperationMode.LIVE
        )

        return client.post("$baseUrl/rpc") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    /**
     * 示例4: 报告代理失败
     */
    suspend fun reportProxyFailure(proxyAddr: String, market: MarketCode): ReportFailureResponse {
        val request = RpcRequest(
            event = RpcEvent.REPORT_FAILURE,
            proxyAddr = proxyAddr,
            market = MarketCode.valueOf(market.name),
            mode = OperationMode.LIVE
        )

        return client.post("$baseUrl/rpc") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    /**
     * 示例5: 获取交易日信息
     */
    suspend fun getTradingDayInfo(market: MarketCode, date: String? = null): TradingDayInfo {
        return client.get("$baseUrl/enhanced/trading-day/${market.name.lowercase()}") {
            date?.let { parameter("date", it) }
        }.body()
    }

    /**
     * 示例6: 获取增强调度器状态
     */
    suspend fun getEnhancedSchedulerStatus(): EnhancedSchedulerStatus {
        return client.get("$baseUrl/enhanced/scheduler/status").body()
    }

    /**
     * 示例7: 批量启动服务
     */
    suspend fun batchStart(markets: List<MarketCode>, mode: OperationMode = OperationMode.LIVE): BatchOperationResponse {
        val request = BatchOperationRequest(
            markets = markets,
            mode = mode
        )

        return client.post("$baseUrl/batch/start") {
            contentType(ContentType.Application.Json)
            setBody(request)
        }.body()
    }

    /**
     * 示例8: 更新配置
     */
    suspend fun updateConfig(
        market: MarketCode,
        updates: ConfigUpdateRequest,
        mode: OperationMode = OperationMode.LIVE
    ): ConfigUpdateResponse {
        return client.post("$baseUrl/config") {
            parameter("market", market.name.lowercase())
            parameter("mode", mode.name.lowercase())
            contentType(ContentType.Application.Json)
            setBody(updates)
        }.body()
    }

    /**
     * 清理资源
     */
    fun close() {
        client.close()
    }
}

/**
 * 使用示例和测试
 */
object ProxyPoolApiUsageDemo {

    @JvmStatic
    fun main(args: Array<String>) = runBlocking {
        val apiClient = ProxyPoolApiClientExample()

        try {
            // 示例1: 获取中国市场状态
            println("=== 获取代理池状态 ===")
            val status = apiClient.getProxyPoolStatus(MarketCode.CN)
            println("状态: ${status.status}")
            println("运行中: ${status.running}")
            println("市场状态: ${status.marketStatus}")
            println("A池大小: ${status.stats.poolASize}")
            println("B池大小: ${status.stats.poolBSize}")
            println("活跃池: ${status.stats.activePool}")
            println("成功率: ${status.stats.successRate}%")

            // 示例2: 获取交易日信息
            println("\n=== 获取交易日信息 ===")
            val tradingInfo = apiClient.getTradingDayInfo(MarketCode.CN)
            println("市场: ${ProxyPoolConstants.MARKET_NAMES[tradingInfo.market]}")
            println("日期: ${tradingInfo.date}")
            println("交易日类型: ${ProxyPoolConstants.TRADING_DAY_TYPE_DESCRIPTIONS[tradingInfo.dayType]}")
            println("时段类型: ${ProxyPoolConstants.TRADING_SESSION_TYPE_DESCRIPTIONS[tradingInfo.sessionType]}")
            println("是否交易日: ${tradingInfo.isTradingDay}")
            println("状态描述: ${tradingInfo.statusDescription}")

            tradingInfo.tradingHours?.let { hours ->
                println("交易时间: ${hours.start} - ${hours.end}")
                hours.lunchBreak?.let { lunch ->
                    println("午休时间: ${lunch.joinToString(" - ")}")
                }
            }

            // 示例3: 获取代理IP
            println("\n=== 获取代理IP ===")
            val proxyResponse = apiClient.getProxy(MarketCode.CN, ProxyType.SHORT)
            if (proxyResponse.status == RpcResponseStatus.OK && proxyResponse.proxy != null) {
                println("获取到代理: ${proxyResponse.proxy}")
                proxyResponse.poolInfo?.let { poolInfo ->
                    println("来源池: ${poolInfo.activePool}")
                    println("池大小: ${poolInfo.poolSize}")
                    println("代理年龄: ${poolInfo.proxyAgeSeconds}秒")
                }
                proxyResponse.marketInfo?.let { marketInfo ->
                    println("市场: ${marketInfo.market}")
                    println("交易时间: ${marketInfo.isTradingTime}")
                    println("市场状态: ${marketInfo.marketStatus}")
                }
            } else {
                println("未能获取到可用代理")
            }

            // 示例4: 获取调度器状态
            println("\n=== 获取增强调度器状态 ===")
            val schedulerStatus = apiClient.getEnhancedSchedulerStatus()
            println("调度器运行: ${schedulerStatus.schedulerRunning}")
            println("增强功能: ${schedulerStatus.enhancedFeatures}")

            schedulerStatus.markets.forEach { (marketKey, marketInfo) ->
                println("\n市场 $marketKey:")
                println("  代理池运行: ${marketInfo.running}")
                println("  自动启动: ${marketInfo.autoStartEnabled}")
                println("  盘前启动: ${marketInfo.preMarketMinutes}分钟")
                println("  盘后停止: ${marketInfo.postMarketMinutes}分钟")
                println("  应该启动: ${marketInfo.shouldStart}")
                println("  应该停止: ${marketInfo.shouldStop}")
                println("  交易日类型: ${marketInfo.tradingDayType}")
                println("  状态描述: ${marketInfo.statusDescription}")
            }

            // 示例5: 错误处理演示
            println("\n=== 错误处理示例 ===")
            try {
                // 故意使用无效的代理地址进行失败报告
                val failureResponse = apiClient.reportProxyFailure("192.168.1.999:8080", MarketCode.CN)
                println("失败报告结果: ${failureResponse.message}")
                println("采取行动: ${failureResponse.actionTaken}")
                failureResponse.poolImpact?.let { impact ->
                    println("影响池: ${impact.affectedPool}")
                    println("剩余大小: ${impact.remainingSize}")
                }
            } catch (e: Exception) {
                println("API调用失败: ${e.message}")
            }

        } catch (e: Exception) {
            println("示例执行失败: ${e.message}")
            e.printStackTrace()
        } finally {
            apiClient.close()
        }
    }
}

/**
 * JSON序列化/反序列化工具类
 */
object JsonUtils {

    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
        prettyPrint = true
    }

    /**
     * 序列化对象到JSON字符串
     */
    inline fun <reified T> toJson(obj: T): String {
        return json.encodeToString(obj)
    }

    /**
     * 从JSON字符串反序列化对象
     */
    inline fun <reified T> fromJson(jsonString: String): T {
        return json.decodeFromString(jsonString)
    }

    /**
     * 美化打印JSON
     */
    inline fun <reified T> prettyPrint(obj: T): String {
        return json.encodeToString(obj)
    }
}

/**
 * API响应包装器处理工具
 */
object ApiResponseHandler {

    /**
     * 处理API响应包装器
     */
    fun <T> handleApiResponse(response: ApiResponse<T>): T {
        return when (response) {
            is ApiResponse.Success -> response.data
            is ApiResponse.Error -> throw RuntimeException("API错误: ${response.error.detail}")
        }
    }

    /**
     * 安全处理API响应
     */
    fun <T> safeHandleApiResponse(response: ApiResponse<T>): T? {
        return when (response) {
            is ApiResponse.Success -> response.data
            is ApiResponse.Error -> {
                println("API错误 [${response.error.statusCode}]: ${response.error.detail}")
                null
            }
        }
    }
}