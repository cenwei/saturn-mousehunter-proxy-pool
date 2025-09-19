# 代理池管理系统 API 接口文档

## 基础信息
- **Base URL**: `http://192.168.8.168:8005`
- **Content-Type**: `application/json`
- **服务名称**: Saturn MouseHunter Proxy Pool Service
- **版本**: v1.0.0

---

## 1. 调度器状态接口

### GET `/api/v1/scheduler/status`
获取全局调度器和所有市场状态

**响应示例:**
```json
{
  "scheduler_running": true,
  "markets": {
    "cn": {
      "running": true,
      "auto_start_enabled": true,
      "pre_market_minutes": 2,
      "post_market_minutes": 30,
      "next_start": "2025-09-22T09:28:00+08:00",
      "next_stop": "2025-09-19T15:40:00+08:00",
      "is_trading_day": true,
      "market_status": "午休时间 (11:35)"
    },
    "hk": {
      "running": true,
      "auto_start_enabled": true,
      "pre_market_minutes": 2,
      "post_market_minutes": 30,
      "next_start": "2025-09-22T09:28:00+08:00",
      "next_stop": "2025-09-19T16:45:00+08:00",
      "is_trading_day": true,
      "market_status": "市场开盘中 (11:35)"
    },
    "us": {
      "running": false,
      "auto_start_enabled": true,
      "pre_market_minutes": 2,
      "post_market_minutes": 30,
      "next_start": "2025-09-19T09:28:00-04:00",
      "next_stop": null,
      "is_trading_day": true,
      "market_status": "已收盘 (23:35)"
    }
  }
}
```

---

## 2. 手动控制接口

### POST `/api/v1/scheduler/force-start/{market}`
强制启动指定市场（忽略交易时间限制）

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**成功响应:**
```json
{
  "status": "started",
  "message": "Market us started manually"
}
```

**已运行响应:**
```json
{
  "status": "already_running",
  "message": "Market us is already running"
}
```

**错误响应:**
```json
{
  "status": "error",
  "message": "Market configuration not found"
}
```

### POST `/api/v1/scheduler/force-stop/{market}`
强制停止指定市场

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**成功响应:**
```json
{
  "status": "stopped",
  "message": "Market us stopped manually"
}
```

**已停止响应:**
```json
{
  "status": "already_stopped",
  "message": "Market us is already stopped"
}
```

---

## 3. 市场详细状态接口

### GET `/api/v1/markets/{market}/status`
获取指定市场的详细状态信息

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**响应示例:**
```json
{
  "running": true,
  "market": "hk",
  "mode": "live",
  "market_status": "市场开盘中 (11:35)",
  "stats": {
    "active_proxies": 40,
    "standby_proxies": 20,
    "total_proxies": 60,
    "pool_rotation_count": 5,
    "last_refresh": "2025-09-19T11:40:12.802000+08:00",
    "total_requests": 150,
    "success_count": 145,
    "failure_count": 5,
    "success_rate": 0.967
  }
}
```

**服务未运行响应:**
```json
{
  "running": false,
  "market": "us",
  "mode": "live",
  "error": "Service not running"
}
```

---

## 4. 代理获取接口

### GET `/api/v1/markets/{market}/proxy`
获取指定市场的代理地址

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**查询参数:**
- `type`: 代理类型 (`short`, `long`) - 可选，默认 `short`

**成功响应:**
```json
{
  "proxy": "112.28.228.44:44437",
  "market": "hk",
  "type": "short",
  "timestamp": "2025-09-19T11:45:30+08:00"
}
```

**无代理可用:**
```json
{
  "proxy": null,
  "market": "hk",
  "message": "No proxy available"
}
```

---

## 5. 代理失败报告接口

### POST `/api/v1/markets/{market}/proxy/failure`
报告代理失败

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**请求体:**
```json
{
  "proxy": "112.28.228.44:44437",
  "reason": "Connection timeout"
}
```

**响应示例:**
```json
{
  "status": "reported",
  "message": "Proxy failure reported successfully"
}
```

---

## 6. 配置管理接口

### GET `/api/v1/markets/{market}/config`
获取市场配置

**响应示例:**
```json
{
  "id": 1,
  "market": "hk",
  "mode": "live",
  "hailiang_api_url": "http://api.hailiangip.com:8422/...",
  "hailiang_enabled": true,
  "batch_size": 20,
  "proxy_lifetime_minutes": 10,
  "rotation_interval_minutes": 5,
  "low_watermark": 5,
  "target_size": 40,
  "auto_start_enabled": true,
  "pre_market_start_minutes": 2,
  "post_market_stop_minutes": 30,
  "backfill_enabled": false,
  "backfill_duration_hours": 8,
  "is_active": true
}
```

### PUT `/api/v1/markets/{market}/config`
更新市场配置

**请求体示例:**
```json
{
  "auto_start_enabled": false,
  "pre_market_start_minutes": 5,
  "target_size": 60
}
```

**响应示例:**
```json
{
  "status": "updated",
  "message": "Configuration updated successfully"
}
```

---

## 7. 代理获取接口

### GET `/api/v1/{market}/proxy`
获取指定市场的代理IP地址

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**查询参数:**
- `proxy_type`: 代理类型 (`short`, `long`) - 可选，默认 `short`

**成功响应:**
```json
{
  "proxy": "112.28.228.66:41073",
  "market": "hk",
  "type": "short",
  "timestamp": "2025-09-19T12:07:48.313308"
}
```

**无代理可用:**
```json
{
  "proxy": null,
  "market": "hk",
  "type": "short",
  "message": "No proxy available",
  "timestamp": "2025-09-19T12:07:48.313308"
}
```

### POST `/api/v1/{market}/proxy/failure`
报告代理IP失败

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**请求体:**
```json
{
  "proxy": "112.28.228.66:41073",
  "reason": "Connection timeout"
}
```

**响应示例:**
```json
{
  "status": "reported",
  "message": "Proxy failure reported: 112.28.228.66:41073",
  "reason": "Connection timeout",
  "timestamp": "2025-09-19T12:07:48.313308"
}
```

### GET `/api/v1/{market}/proxies/list`
获取指定市场的代理池详细信息

**路径参数:**
- `market`: 市场代码 (`cn`, `hk`, `us`)

**响应示例:**
```json
{
  "market": "hk",
  "running": true,
  "stats": {
    "market": "HK",
    "mode": "live",
    "pool_type": "memory_ab",
    "active_pool": "B",
    "standby_pool": "A",
    "active_pool_size": 40,
    "standby_pool_size": 0,
    "total_pool_size": 40,
    "last_switch_time": "2025-09-19 12:06:54",
    "switch_ago_seconds": 54,
    "uptime_seconds": 56,
    "uptime_hours": 0.02,
    "total_requests": 0,
    "success_count": 0,
    "failure_count": 0,
    "success_rate": 0.0,
    "last_fetch_time": "2025-09-19 12:06:54",
    "last_fetch_count": 40,
    "status": "warning"
  },
  "active_pool": "B",
  "standby_pool": "A",
  "active_proxies": [
    {
      "addr": "112.28.228.67:36701",
      "status": "active",
      "created_at": "2025-09-19T12:06:54.166103",
      "last_used": null,
      "failure_count": 0
    },
    {
      "addr": "112.28.228.66:41073",
      "status": "active",
      "created_at": "2025-09-19T12:06:54.166103",
      "last_used": "2025-09-19T12:07:14.037687",
      "failure_count": 0
    }
  ],
  "standby_proxies": [],
  "total_count": 40,
  "timestamp": "2025-09-19T12:07:48.313308"
}
```

**服务未运行响应:**
```json
{
  "market": "hk",
  "running": false,
  "active_pool": null,
  "standby_pool": null,
  "active_proxies": [],
  "standby_proxies": [],
  "total_count": 0
}
```

---

## Kotlin Quickly 前端集成示例

### 1. 数据模型定义

```kotlin
// 市场状态数据类
data class MarketStatus(
    val running: Boolean,
    val autoStartEnabled: Boolean,
    val preMarketMinutes: Int,
    val postMarketMinutes: Int,
    val nextStart: String?,
    val nextStop: String?,
    val isTradingDay: Boolean,
    val marketStatus: String
)

// 调度器状态响应
data class SchedulerStatusResponse(
    val schedulerRunning: Boolean,
    val markets: Map<String, MarketStatus>
)

// 代理统计信息
data class ProxyStats(
    val activeProxies: Int,
    val standbyProxies: Int,
    val totalProxies: Int,
    val poolRotationCount: Int,
    val lastRefresh: String,
    val totalRequests: Int,
    val successCount: Int,
    val failureCount: Int,
    val successRate: Double
)

// 市场详细状态
data class MarketDetailStatus(
    val running: Boolean,
    val market: String,
    val mode: String,
    val marketStatus: String,
    val stats: ProxyStats?
)

// 代理信息
data class ProxyInfo(
    val addr: String,
    val status: String,
    val createdAt: String?,
    val lastUsed: String?,
    val failureCount: Int
)

// 代理池详情响应
data class ProxyPoolDetailResponse(
    val market: String,
    val running: Boolean,
    val stats: ProxyStats?,
    val activePool: String?,
    val standbyPool: String?,
    val activeProxies: List<ProxyInfo>,
    val standbyProxies: List<ProxyInfo>,
    val totalCount: Int,
    val timestamp: String
)

// 单个代理获取响应
data class ProxyResponse(
    val proxy: String?,
    val market: String,
    val type: String,
    val message: String?,
    val timestamp: String
)

// 代理失败报告请求
data class ProxyFailureRequest(
    val proxy: String,
    val reason: String
)

// 操作响应
data class OperationResponse(
    val status: String,
    val message: String
)
```

### 2. API 服务类

```kotlin
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

class ProxyPoolApiService(private val baseUrl: String = "http://localhost:8005") {

    // 获取调度器状态
    suspend fun getSchedulerStatus(): SchedulerStatusResponse {
        return httpGet("$baseUrl/api/v1/scheduler/status")
    }

    // 强制启动市场
    suspend fun forceStartMarket(market: String): OperationResponse {
        return httpPost("$baseUrl/api/v1/scheduler/force-start/$market")
    }

    // 强制停止市场
    suspend fun forceStopMarket(market: String): OperationResponse {
        return httpPost("$baseUrl/api/v1/scheduler/force-stop/$market")
    }

    // 获取市场详细状态
    suspend fun getMarketStatus(market: String): MarketDetailStatus {
        return httpGet("$baseUrl/api/v1/markets/$market/status")
    }

    // 获取单个代理IP
    suspend fun getProxy(market: String, type: String = "short"): ProxyResponse {
        return httpGet("$baseUrl/api/v1/$market/proxy?proxy_type=$type")
    }

    // 获取代理池详细信息
    suspend fun getProxyPoolDetails(market: String): ProxyPoolDetailResponse {
        return httpGet("$baseUrl/api/v1/$market/proxies/list")
    }

    // 报告代理失败
    suspend fun reportProxyFailure(market: String, proxy: String, reason: String): OperationResponse {
        val requestBody = ProxyFailureRequest(proxy, reason)
        return httpPost("$baseUrl/api/v1/$market/proxy/failure", requestBody)
    }

    // 获取所有代理池状态
    suspend fun getAllPools(): Map<String, Any> {
        return httpGet("$baseUrl/api/v1/pools")
    }
}
```

### 3. 状态管理组件

```kotlin
class ProxyPoolViewModel {
    private val apiService = ProxyPoolApiService()
    private var statusUpdateJob: Job? = null

    // 状态数据
    var schedulerStatus by mutableStateOf<SchedulerStatusResponse?>(null)
        private set

    var currentProxyPoolDetails by mutableStateOf<ProxyPoolDetailResponse?>(null)
        private set

    var currentMarket by mutableStateOf("hk")
        private set

    var isLoading by mutableStateOf(false)
        private set

    var errorMessage by mutableStateOf<String?>(null)
        private set

    // 开始定时更新状态
    fun startStatusUpdates() {
        statusUpdateJob?.cancel()
        statusUpdateJob = CoroutineScope(Dispatchers.IO).launch {
            while (isActive) {
                try {
                    schedulerStatus = apiService.getSchedulerStatus()
                    // 同时更新当前市场的代理池详情
                    updateProxyPoolDetails(currentMarket)
                    errorMessage = null
                } catch (e: Exception) {
                    errorMessage = "获取状态失败: ${e.message}"
                }
                delay(30000) // 30秒更新一次
            }
        }
    }

    // 停止状态更新
    fun stopStatusUpdates() {
        statusUpdateJob?.cancel()
    }

    // 更新代理池详情
    suspend fun updateProxyPoolDetails(market: String) {
        try {
            currentMarket = market
            currentProxyPoolDetails = apiService.getProxyPoolDetails(market)
        } catch (e: Exception) {
            errorMessage = "获取代理池详情失败: ${e.message}"
        }
    }

    // 获取单个代理
    suspend fun getProxy(market: String, type: String = "short"): ProxyResponse? {
        return try {
            isLoading = true
            val response = apiService.getProxy(market, type)
            // 获取代理后刷新代理池状态
            updateProxyPoolDetails(market)
            response
        } catch (e: Exception) {
            errorMessage = "获取代理失败: ${e.message}"
            null
        } finally {
            isLoading = false
        }
    }

    // 报告代理失败
    suspend fun reportProxyFailure(market: String, proxy: String, reason: String): Boolean {
        return try {
            isLoading = true
            val response = apiService.reportProxyFailure(market, proxy, reason)
            // 报告失败后刷新代理池状态
            updateProxyPoolDetails(market)
            response.status == "reported"
        } catch (e: Exception) {
            errorMessage = "报告代理失败错误: ${e.message}"
            false
        } finally {
            isLoading = false
        }
    }

    // 强制启动市场
    suspend fun forceStartMarket(market: String): Boolean {
        return try {
            isLoading = true
            val response = apiService.forceStartMarket(market)
            response.status == "started"
        } catch (e: Exception) {
            errorMessage = "启动失败: ${e.message}"
            false
        } finally {
            isLoading = false
        }
    }

    // 强制停止市场
    suspend fun forceStopMarket(market: String): Boolean {
        return try {
            isLoading = true
            val response = apiService.forceStopMarket(market)
            response.status == "stopped"
        } catch (e: Exception) {
            errorMessage = "停止失败: ${e.message}"
            false
        } finally {
            isLoading = false
        }
    }
}
```

### 4. UI 组件示例

```kotlin
@Composable
fun MarketControlPanel(market: String, status: MarketStatus, viewModel: ProxyPoolViewModel) {
    val scope = rememberCoroutineScope()

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // 市场名称和状态
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = market.uppercase(),
                    style = MaterialTheme.typography.h6
                )

                StatusIndicator(
                    running = status.running,
                    marketStatus = status.marketStatus
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 状态信息
            Text(
                text = "状态: ${status.marketStatus}",
                style = MaterialTheme.typography.body2
            )

            if (status.nextStart != null) {
                Text(
                    text = "下次启动: ${formatDateTime(status.nextStart)}",
                    style = MaterialTheme.typography.body2
                )
            }

            if (status.nextStop != null) {
                Text(
                    text = "下次停止: ${formatDateTime(status.nextStop)}",
                    style = MaterialTheme.typography.body2
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 控制按钮
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = {
                        scope.launch {
                            viewModel.forceStartMarket(market)
                        }
                    },
                    enabled = !status.running && !viewModel.isLoading,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = MaterialTheme.colors.primary
                    )
                ) {
                    Text("强制启动")
                }

                Button(
                    onClick = {
                        scope.launch {
                            viewModel.forceStopMarket(market)
                        }
                    },
                    enabled = status.running && !viewModel.isLoading,
                    colors = ButtonDefaults.buttonColors(
                        backgroundColor = MaterialTheme.colors.error
                    )
                ) {
                    Text("强制停止")
                }

                Button(
                    onClick = {
                        scope.launch {
                            viewModel.updateProxyPoolDetails(market)
                        }
                    },
                    enabled = !viewModel.isLoading
                ) {
                    Text("查看代理")
                }
            }
        }
    }
}

@Composable
fun ProxyPoolDetailPanel(
    details: ProxyPoolDetailResponse,
    viewModel: ProxyPoolViewModel
) {
    val scope = rememberCoroutineScope()

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // 代理池概览
            Text(
                text = "${details.market.uppercase()} 代理池详情",
                style = MaterialTheme.typography.h6
            )

            Spacer(modifier = Modifier.height(8.dp))

            details.stats?.let { stats ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    StatCard("活跃代理", stats.activeProxies.toString())
                    StatCard("备用代理", stats.standbyProxies.toString())
                    StatCard("成功率", "${(stats.successRate * 100).toInt()}%")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 代理获取按钮
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = {
                        scope.launch {
                            val proxy = viewModel.getProxy(details.market, "short")
                            // 处理获取到的代理
                        }
                    },
                    enabled = details.running && !viewModel.isLoading
                ) {
                    Text("获取短期代理")
                }

                Button(
                    onClick = {
                        scope.launch {
                            val proxy = viewModel.getProxy(details.market, "long")
                            // 处理获取到的代理
                        }
                    },
                    enabled = details.running && !viewModel.isLoading
                ) {
                    Text("获取长期代理")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 活跃代理列表
            if (details.activeProxies.isNotEmpty()) {
                Text(
                    text = "活跃代理 (前10个):",
                    style = MaterialTheme.typography.subtitle1
                )

                LazyColumn(
                    modifier = Modifier.height(200.dp)
                ) {
                    items(details.activeProxies.take(10)) { proxy ->
                        ProxyItem(
                            proxy = proxy,
                            onReportFailure = { proxyAddr, reason ->
                                scope.launch {
                                    viewModel.reportProxyFailure(details.market, proxyAddr, reason)
                                }
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ProxyItem(
    proxy: ProxyInfo,
    onReportFailure: (String, String) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        elevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .padding(8.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = proxy.addr,
                    style = MaterialTheme.typography.body2,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "失败次数: ${proxy.failureCount}",
                    style = MaterialTheme.typography.caption
                )
                proxy.lastUsed?.let {
                    Text(
                        text = "最后使用: ${formatDateTime(it)}",
                        style = MaterialTheme.typography.caption
                    )
                }
            }

            Button(
                onClick = {
                    onReportFailure(proxy.addr, "手动报告失败")
                },
                colors = ButtonDefaults.buttonColors(
                    backgroundColor = MaterialTheme.colors.error
                ),
                modifier = Modifier.size(width = 80.dp, height = 32.dp)
            ) {
                Text("报告失败", fontSize = 10.sp)
            }
        }
    }
}

@Composable
fun StatCard(title: String, value: String) {
    Card(
        modifier = Modifier.padding(4.dp),
        elevation = 2.dp
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = value,
                style = MaterialTheme.typography.h5,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = title,
                style = MaterialTheme.typography.caption
            )
        }
    }
}

@Composable
fun StatusIndicator(running: Boolean, marketStatus: String) {
    val color = when {
        running -> Color.Green
        marketStatus.contains("已收盘") -> Color.Red
        marketStatus.contains("午休") -> Color.Orange
        else -> Color.Gray
    }

    Box(
        modifier = Modifier
            .size(12.dp)
            .background(color, CircleShape)
    )
}

// 时间格式化工具函数
fun formatDateTime(dateTimeStr: String): String {
    // 根据需要格式化时间字符串
    return dateTimeStr.substringBefore('T').replace('-', '/') +
           " " + dateTimeStr.substringAfter('T').substringBefore('.')
}
```

### 5. 主界面集成

```kotlin
@Composable
fun ProxyPoolDashboard() {
    val viewModel = remember { ProxyPoolViewModel() }

    LaunchedEffect(Unit) {
        viewModel.startStatusUpdates()
    }

    DisposableEffect(Unit) {
        onDispose {
            viewModel.stopStatusUpdates()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "代理池管理系统",
            style = MaterialTheme.typography.h4,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        if (viewModel.isLoading) {
            CircularProgressIndicator()
        }

        viewModel.errorMessage?.let { error ->
            Card(
                backgroundColor = MaterialTheme.colors.error.copy(alpha = 0.1f),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp)
            ) {
                Text(
                    text = error,
                    color = MaterialTheme.colors.error,
                    modifier = Modifier.padding(16.dp)
                )
            }
        }

        viewModel.schedulerStatus?.let { status ->
            LazyColumn {
                items(status.markets.entries.toList()) { (market, marketStatus) ->
                    MarketControlPanel(
                        market = market,
                        status = marketStatus,
                        viewModel = viewModel
                    )
                }

                // 代理池详情面板
                item {
                    viewModel.currentProxyPoolDetails?.let { details ->
                        ProxyPoolDetailPanel(
                            details = details,
                            viewModel = viewModel
                        )
                    }
                }
            }
        }
    }
}

// 使用示例
@Composable
fun MainScreen() {
    MaterialTheme {
        ProxyPoolDashboard()
    }
}
```

---

## 快速测试命令

### 获取代理池详情
```bash
curl -s "http://localhost:8005/api/v1/hk/proxies/list" | python -m json.tool
```

### 获取单个代理
```bash
curl -s "http://localhost:8005/api/v1/hk/proxy?proxy_type=short" | python -m json.tool
```

### 报告代理失败
```bash
curl -X POST "http://localhost:8005/api/v1/hk/proxy/failure" \
  -H "Content-Type: application/json" \
  -d '{"proxy": "112.28.228.66:41073", "reason": "Connection timeout"}' | python -m json.tool
```

### 获取调度器状态
```bash
curl -s "http://localhost:8005/api/v1/scheduler/status" | python -m json.tool
```

### 强制启动市场
```bash
curl -X POST "http://localhost:8005/api/v1/scheduler/force-start/us" | python -m json.tool
```

---

## 错误码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | 成功 | 请求成功处理 |
| 400 | 请求错误 | 参数错误或格式不正确 |
| 404 | 未找到 | 市场或资源不存在 |
| 500 | 服务器错误 | 内部服务器错误 |

## 状态值说明

### 市场状态 (market_status)
- `市场开盘中` - 交易时间内
- `已收盘` - 非交易时间
- `午休时间` - 中午休市时间
- `盘前准备` - 开盘前准备时间

### 操作状态 (status)
- `started` - 成功启动
- `stopped` - 成功停止
- `already_running` - 已在运行
- `already_stopped` - 已停止
- `error` - 操作失败

---

*文档更新时间: 2025-09-19*
*API版本: v1.0.0*