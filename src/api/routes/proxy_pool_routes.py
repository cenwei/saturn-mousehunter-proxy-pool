"""
API层 - 代理池路由
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

from saturn_mousehunter_shared import get_logger
from infrastructure.proxy_pool import ProxyPoolManager
from infrastructure.proxy_fetchers import fetch_hailiang_proxy_ip

router = APIRouter(tags=["proxy_pool"])
log = get_logger("proxy_pool_routes")


class RpcRequest(BaseModel):
    """RPC请求模型"""

    event: str
    proxy_type: Optional[str] = "short"
    proxy_addr: Optional[str] = None
    market: Optional[str] = "HK"
    mode: Optional[str] = "live"


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""

    hailiang_api_url: Optional[str] = None
    hailiang_enabled: Optional[bool] = None
    batch_size: Optional[int] = None
    proxy_lifetime_minutes: Optional[int] = None
    rotation_interval_minutes: Optional[int] = None
    low_watermark: Optional[int] = None
    target_size: Optional[int] = None
    auto_start_enabled: Optional[bool] = None
    pre_market_start_minutes: Optional[int] = None
    post_market_stop_minutes: Optional[int] = None
    backfill_enabled: Optional[bool] = None
    backfill_duration_hours: Optional[int] = None


class BackfillStartRequest(BaseModel):
    """Backfill启动请求模型"""

    market: str
    duration_hours: Optional[int] = 2


class StatusResponse(BaseModel):
    """状态响应模型"""

    status: str
    running: bool
    market: str
    mode: str
    market_status: str
    stats: Dict[str, Any]


def get_proxy_pool_manager(
    market: str = Query(..., description="市场代码: CN/HK/US"),
    mode: str = Query("live", description="模式: live/backfill"),
) -> ProxyPoolManager:
    """获取代理池管理器依赖"""
    from infrastructure.dependencies import get_proxy_pool_manager as get_manager

    try:
        return get_manager(market, mode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def get_all_managers() -> dict[str, ProxyPoolManager]:
    """获取所有管理器依赖"""
    from infrastructure.dependencies import get_all_proxy_pool_managers

    return get_all_proxy_pool_managers()


def get_global_scheduler():
    """获取全局调度器依赖"""
    from infrastructure.dependencies import get_global_scheduler as get_scheduler

    return get_scheduler()


def get_alert_manager():
    """获取告警管理器依赖"""
    from infrastructure.dependencies import get_alert_manager as get_manager

    return get_manager()


def get_health_monitor():
    """获取健康监控器依赖"""
    from infrastructure.dependencies import get_health_monitor as get_monitor

    return get_monitor()


# ========== 监控告警接口 ==========


@router.get("/monitoring/alerts")
async def get_alerts(
    hours: int = Query(24, description="获取多少小时内的告警"),
    level: str = Query(None, description="告警级别过滤"),
    market: str = Query(None, description="市场过滤"),
    alert_manager=Depends(get_alert_manager),
):
    """获取告警列表"""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not available")

    try:
        from infrastructure.monitoring import AlertLevel

        # 过滤级别
        alert_level = None
        if level:
            try:
                alert_level = AlertLevel(level.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid alert level: {level}"
                )

        if market:
            alerts = alert_manager.get_alerts_by_market(market.lower(), hours)
            if alert_level:
                alerts = [a for a in alerts if a.level == alert_level]
        else:
            alerts = alert_manager.get_recent_alerts(hours, alert_level)

        # 转换为字典格式
        alert_list = []
        for alert in alerts:
            alert_list.append(
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "market": alert.market,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged,
                }
            )

        return {
            "alerts": alert_list,
            "total": len(alert_list),
            "filters": {"hours": hours, "level": level, "market": market},
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/monitoring/summary")
async def get_monitoring_summary(
    alert_manager=Depends(get_alert_manager), health_monitor=Depends(get_health_monitor)
):
    """获取监控摘要"""
    if not alert_manager or not health_monitor:
        raise HTTPException(status_code=503, detail="Monitoring system not available")

    try:
        alert_summary = alert_manager.get_alert_summary()
        health_summary = health_monitor.get_health_summary()

        return {
            "alerts": alert_summary,
            "health": health_summary,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get monitoring summary: {str(e)}"
        )


@router.post("/monitoring/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, alert_manager=Depends(get_alert_manager)):
    """确认告警"""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not available")

    try:
        success = alert_manager.acknowledge_alert(alert_id)
        if success:
            return {"status": "acknowledged", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.delete("/monitoring/alerts/clear")
async def clear_old_alerts(
    days: int = Query(7, description="清理多少天前的告警"),
    alert_manager=Depends(get_alert_manager),
):
    """清理旧告警"""
    if not alert_manager:
        raise HTTPException(status_code=503, detail="Alert manager not available")

    try:
        cleared_count = alert_manager.clear_old_alerts(days)
        return {"status": "cleared", "cleared_count": cleared_count, "days": days}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear alerts: {str(e)}")


# ========== 调度管理接口 ==========


@router.get("/scheduler/status")
async def get_scheduler_status(scheduler=Depends(get_global_scheduler)):
    """获取调度器状态"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Global scheduler not available")

    try:
        status = await scheduler.get_schedule_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get scheduler status: {str(e)}"
        )


@router.post("/scheduler/force-start/{market}")
async def force_start_market(market: str, scheduler=Depends(get_global_scheduler)):
    """强制启动市场"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Global scheduler not available")

    try:
        result = await scheduler.force_start_market(market.lower())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to force start market: {str(e)}"
        )


@router.post("/scheduler/force-stop/{market}")
async def force_stop_market(market: str, scheduler=Depends(get_global_scheduler)):
    """强制停止市场"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Global scheduler not available")

    try:
        result = await scheduler.force_stop_market(market.lower())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to force stop market: {str(e)}"
        )


# ========== 服务管理接口 ==========


@router.get("/pools")
async def list_pools(managers: dict = Depends(get_all_managers)):
    """列出所有代理池"""
    pools = []
    for key, manager in managers.items():
        market, mode = key.split("_", 1)
        status = await manager.get_status()
        pools.append(
            {
                "key": key,
                "market": market,
                "mode": mode,
                "running": manager.is_running,
                "status": status,
            }
        )
    return {"pools": pools}


@router.get("/config")
async def get_config(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取配置信息"""
    config_dict = await manager.get_config_dict()
    return {
        "market": manager.market,
        "mode": manager.mode.value,
        "config": config_dict,
        "backend": "database_driven",
    }


@router.get("/status", response_model=StatusResponse)
async def get_status(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取服务状态"""
    service_status = await manager.get_status()

    return StatusResponse(
        status="ok",
        running=manager.is_running,
        market=manager.market,
        mode=manager.mode.value,
        market_status=service_status.get("market_status", "unknown"),
        stats=service_status.get("stats", {}),
    )


@router.get("/metrics")
async def get_metrics(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取指标数据"""
    if not manager.is_running:
        return {
            "running": 0,
            "active_pool": None,
            "size_active": 0,
            "size_standby": 0,
            "total_pool_size": 0,
            "success_rate": 0.0,
        }

    status = await manager.get_status()
    stats = status.get("stats", {})

    return {
        "running": int(manager.is_running),
        "active_pool": stats.get("active_pool"),
        "size_active": stats.get("active_pool_size", 0),
        "size_standby": stats.get("standby_pool_size", 0),
        "total_pool_size": stats.get("total_pool_size", 0),
        "success_rate": stats.get("success_rate", 0.0),
        "total_requests": stats.get("total_requests", 0),
        "success_count": stats.get("success_count", 0),
        "failure_count": stats.get("failure_count", 0),
    }


# ========== 服务控制接口 ==========


@router.post("/start")
async def start_service(
    force: bool = Query(False, description="强制启动，忽略市场时间限制（人工启动时使用）"),
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager)
):
    """启动服务

    Args:
        force: 是否强制启动
            - True: 人工启动，忽略市场时间限制
            - False: 自动启动，受市场时间限制（默认）
    """
    try:
        await manager.start(force=force)
        start_type = "manually" if force else "automatically"
        return {
            "status": "started",
            "message": f"Proxy pool service started {start_type} for {manager.market}/{manager.mode.value}",
        }
    except Exception as e:
        log.error(f"Failed to start service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_service(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """停止服务"""
    try:
        await manager.stop()
        return {
            "status": "stopped",
            "message": f"Proxy pool service stopped for {manager.market}/{manager.mode.value}",
        }
    except Exception as e:
        log.error(f"Failed to stop service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backfill/start")
async def start_backfill(
    request: BackfillStartRequest, managers: dict = Depends(get_all_managers)
):
    """启动backfill模式代理池"""
    key = f"{request.market.lower()}_backfill"
    manager = managers.get(key)

    if not manager:
        raise HTTPException(
            status_code=404,
            detail=f"Backfill manager not found for market {request.market}",
        )

    try:
        await manager.start_manual(request.duration_hours)
        return {
            "status": "started",
            "message": f"Backfill proxy pool started for {request.market}",
            "duration_hours": request.duration_hours,
        }
    except Exception as e:
        log.error(f"Failed to start backfill service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ========== 配置管理接口 ==========


@router.post("/config")
async def update_config(
    request: ConfigUpdateRequest,
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager),
):
    """更新配置"""
    try:
        # 构建更新字典，只包含非None的字段
        update_dict = {}
        for field, value in request.dict().items():
            if value is not None:
                update_dict[field] = value

        if not update_dict:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        success = await manager.update_config(**update_dict)

        if success:
            config_dict = await manager.get_config_dict()
            return {
                "status": "success",
                "message": f"Configuration updated for {manager.market}/{manager.mode.value}",
                "config": config_dict,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to update configuration"
            )

    except Exception as e:
        log.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/hailiang/test")
async def test_hailiang_api(
    api_url: str = Body(..., embed=True),
    market: str = Query("hk", description="市场代码"),
):
    """测试海量代理API"""
    try:
        proxies = await fetch_hailiang_proxy_ip(api_url)
        return {
            "status": "success",
            "message": f"Successfully fetched {len(proxies)} proxies",
            "proxy_count": len(proxies),
            "sample_proxies": proxies[:5] if proxies else [],
        }
    except Exception as e:
        log.error(f"Failed to test Hailiang API: {e}")
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")


# ========== RPC接口 ==========


@router.post("/rpc")
async def rpc_handler(
    request: RpcRequest = Body(...), managers: dict = Depends(get_all_managers)
):
    """RPC接口 - 兼容原ZMQ事件格式"""
    event = request.event.lower().strip()
    market = request.market or "hk"
    mode = request.mode or "live"

    key = f"{market.lower()}_{mode.lower()}"
    manager = managers.get(key)

    if not manager:
        raise HTTPException(
            status_code=404, detail=f"Manager not found for {market}/{mode}"
        )

    if not manager.is_running and event != "ping":
        raise HTTPException(
            status_code=400, detail=f"Service not running for {market}/{mode}"
        )

    if event == "get_proxy":
        proxy_addr = await manager.get_proxy(request.proxy_type or "short")
        return {"status": "ok", "proxy": proxy_addr}

    elif event == "report_failure":
        if not request.proxy_addr:
            raise HTTPException(status_code=400, detail="proxy_addr required")

        await manager.report_failure(request.proxy_addr)
        return {"status": "ok", "message": f"{request.proxy_addr} marked as failure"}

    elif event == "get_status":
        service_status = await manager.get_status()
        return {
            "status": "ok",
            "stats": service_status.get("stats", {}),
            "market_status": service_status.get("market_status", "unknown"),
            "service_mode": manager.mode.value,
        }

    elif event == "ping":
        status = (
            await manager.get_status()
            if manager.is_running
            else {"market_status": "stopped"}
        )
        return {
            "status": "ok",
            "message": "pong",
            "market": manager.market,
            "mode": manager.mode.value,
            "running": manager.is_running,
            "market_status": status.get("market_status", "unknown"),
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown event: {request.event}")


# ========== 代理获取接口 ==========


@router.get("/{market}/proxy")
async def get_proxy(
    market: str,
    proxy_type: str = Query("short", description="代理类型: short/long"),
    managers: dict = Depends(get_all_managers)
):
    """获取指定市场的代理IP"""
    request_id = f"get_proxy_{market}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # 记录请求参数（避免JSON转义问题）
    request_params_escaped = str({"market": market, "proxy_type": proxy_type}).replace("{", "{{").replace("}", "}}")
    log.info(f"[{request_id}] API Request - get_proxy", extra={
        "request_id": request_id,
        "endpoint": f"GET /{market}/proxy",
        "market": market,
        "proxy_type": proxy_type,
        "request_params_str": request_params_escaped
    })

    key = f"{market.upper()}_live"
    manager = managers.get(key)

    if not manager:
        error_msg = f"Manager not found for market {market}"
        log.error(f"[{request_id}] {error_msg}", extra={
            "request_id": request_id,
            "error_type": "manager_not_found",
            "market": market,
            "available_managers": list(managers.keys())
        })
        raise HTTPException(
            status_code=404,
            detail=error_msg
        )

    if not manager.is_running:
        error_msg = f"Proxy pool service not running for market {market}"
        log.error(f"[{request_id}] {error_msg}", extra={
            "request_id": request_id,
            "error_type": "service_not_running",
            "market": market,
            "manager_running": manager.is_running
        })
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )

    try:
        proxy_addr = await manager.get_proxy(proxy_type)

        response_data = {
            "proxy": proxy_addr,
            "market": market.lower(),
            "type": proxy_type,
            "timestamp": datetime.now().isoformat()
        }

        # 记录成功响应（避免JSON转义问题）
        response_data_escaped = str(response_data).replace("{", "{{").replace("}", "}}")
        log.info(f"[{request_id}] API Response - get_proxy SUCCESS", extra={
            "request_id": request_id,
            "response_status": "success",
            "proxy_returned": proxy_addr is not None,
            "proxy_addr": proxy_addr if proxy_addr else "None",
            "response_data_str": response_data_escaped
        })

        return response_data

    except Exception as e:
        error_msg = f"Failed to get proxy: {str(e)}"

        # 记录错误响应和堆栈
        log.error(f"[{request_id}] API Response - get_proxy ERROR: {error_msg}", extra={
            "request_id": request_id,
            "response_status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })

        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{market}/proxy/failure")
async def report_proxy_failure(
    market: str,
    proxy: str = Body(..., embed=True, description="失败的代理地址"),
    reason: str = Body("Connection failed", embed=True, description="失败原因"),
    managers: dict = Depends(get_all_managers)
):
    """报告代理失败"""
    request_id = f"report_failure_{market}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # 记录请求参数
    # 记录请求参数（避免JSON转义问题）
    request_params_escaped = str({"market": market, "proxy": proxy, "reason": reason}).replace("{", "{{").replace("}", "}}")
    log.info(f"[{request_id}] API Request - report_proxy_failure", extra={
        "request_id": request_id,
        "endpoint": f"POST /{market}/proxy/failure",
        "market": market,
        "proxy": proxy,
        "reason": reason,
        "request_params_str": request_params_escaped
    })

    key = f"{market.upper()}_live"
    manager = managers.get(key)

    if not manager:
        error_msg = f"Manager not found for market {market}"
        log.error(f"[{request_id}] {error_msg}", extra={
            "request_id": request_id,
            "error_type": "manager_not_found",
            "market": market,
            "available_managers": list(managers.keys())
        })
        raise HTTPException(
            status_code=404,
            detail=error_msg
        )

    if not manager.is_running:
        error_msg = f"Proxy pool service not running for market {market}"
        log.error(f"[{request_id}] {error_msg}", extra={
            "request_id": request_id,
            "error_type": "service_not_running",
            "market": market,
            "manager_running": manager.is_running
        })
        raise HTTPException(
            status_code=400,
            detail=error_msg
        )

    try:
        await manager.report_failure(proxy)

        response_data = {
            "status": "reported",
            "message": f"Proxy failure reported: {proxy}",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # 记录成功响应（避免JSON转义问题）
        response_data_escaped = str(response_data).replace("{", "{{").replace("}", "}}")
        log.info(f"[{request_id}] API Response - report_proxy_failure SUCCESS", extra={
            "request_id": request_id,
            "response_status": "success",
            "proxy_reported": proxy,
            "failure_reason": reason,
            "response_data_str": response_data_escaped
        })

        return response_data

    except Exception as e:
        error_msg = f"Failed to report failure: {str(e)}"

        # 记录错误响应和堆栈
        log.error(f"[{request_id}] API Response - report_proxy_failure ERROR: {error_msg}", extra={
            "request_id": request_id,
            "response_status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__,
            "proxy_addr": proxy,
            "traceback": traceback.format_exc()
        })

        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/{market}/proxies/list")
async def list_proxies(
    market: str,
    managers: dict = Depends(get_all_managers)
):
    """获取指定市场的代理池列表信息"""
    request_id = f"list_proxies_{market}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # 记录请求参数
    # 记录请求参数（避免JSON转义问题）
    request_params_escaped = str({"market": market}).replace("{", "{{").replace("}", "}}")
    log.info(f"[{request_id}] API Request - list_proxies", extra={
        "request_id": request_id,
        "endpoint": f"GET /{market}/proxies/list",
        "market": market,
        "request_params_str": request_params_escaped
    })

    key = f"{market.upper()}_live"
    manager = managers.get(key)

    if not manager:
        error_msg = f"Manager not found for market {market}"
        log.error(f"[{request_id}] {error_msg}", extra={
            "request_id": request_id,
            "error_type": "manager_not_found",
            "market": market,
            "available_managers": list(managers.keys())
        })
        raise HTTPException(
            status_code=404,
            detail=error_msg
        )

    if not manager.is_running:
        response_data = {
            "market": market.lower(),
            "mode": manager.mode.value,  # 客户端期望的字段
            "running": False,
            "pool_info": {
                "active_pool": None,
                "standby_pool": None,
                "total_count": 0,
                # Kotlin客户端期望的必需字段
                "pool_name": None,
                "current_size": 0,
                "target_size": 200,  # 默认目标大小
                "rotation_count": 0,
                "status": "stopped"
            },
            "proxies": {
                "active": [],
                "standby": []
            },
            "active_count": 0,
            "failed_count": 0,
            "active_pool": None,
            "standby_pool": None,
            "active_proxies": [],
            "standby_proxies": [],
            "total_count": 0
        }

        # 记录服务未运行的响应（避免JSON转义问题）
        response_data_escaped = str(response_data).replace("{", "{{").replace("}", "}}")
        log.info(f"[{request_id}] API Response - list_proxies NOT_RUNNING", extra={
            "request_id": request_id,
            "response_status": "not_running",
            "service_running": False,
            "response_data_str": response_data_escaped
        })

        return response_data

    try:
        # 获取内存代理仓储的详细信息
        status = await manager.get_status()
        stats = status.get("stats", {})

        # 记录获取状态的详细信息（避免JSON转义问题）
        manager_status_escaped = str(status).replace("{", "{{").replace("}", "}}")
        stats_escaped = str(stats).replace("{", "{{").replace("}", "}}")
        log.info(f"[{request_id}] Manager status retrieved", extra={
            "request_id": request_id,
            "manager_status_str": manager_status_escaped,
            "stats_str": stats_escaped
        })

        # 尝试获取代理池详细信息
        proxy_details = {}
        health_summary = {}
        if hasattr(manager, '_repository') and manager._repository:
            repo = manager._repository
            if hasattr(repo, 'pools') and hasattr(repo, 'active_pool'):
                active_pool = getattr(repo, 'active_pool', 'A')
                standby_pool = 'B' if active_pool == 'A' else 'A'

                # 获取代理列表
                active_proxies = []
                standby_proxies = []

                pools = getattr(repo, 'pools', {})
                if active_pool in pools:
                    active_proxies = [
                        {
                            "addr": proxy.addr,
                            "status": proxy.status.value,
                            "created_at": proxy.created_at.isoformat() if proxy.created_at else None,
                            "last_used": proxy.last_used.isoformat() if proxy.last_used else None,
                            "failure_count": getattr(proxy, 'failure_count', 0)
                        }
                        for proxy in pools[active_pool][:20]  # 限制返回数量
                    ]

                if standby_pool in pools:
                    standby_proxies = [
                        {
                            "addr": proxy.addr,
                            "status": proxy.status.value,
                            "created_at": proxy.created_at.isoformat() if proxy.created_at else None,
                            "last_used": proxy.last_used.isoformat() if proxy.last_used else None,
                            "failure_count": getattr(proxy, 'failure_count', 0)
                        }
                        for proxy in pools[standby_pool][:20]  # 限制返回数量
                    ]

                proxy_details = {
                    "active_pool": active_pool,
                    "standby_pool": standby_pool,
                    "active_proxies": active_proxies,
                    "standby_proxies": standby_proxies,
                    "total_count": len(pools.get(active_pool, [])) + len(pools.get(standby_pool, []))
                }

                # 获取健康检查统计信息
                if hasattr(repo, 'get_health_summary'):
                    health_summary = repo.get_health_summary() or {}

                # 记录代理池详细信息
                log.info(f"[{request_id}] Proxy pool details extracted", extra={
                    "request_id": request_id,
                    "active_pool": active_pool,
                    "standby_pool": standby_pool,
                    "active_count": len(active_proxies),
                    "standby_count": len(standby_proxies),
                    "total_pools_count": proxy_details["total_count"],
                    "health_check_enabled": bool(health_summary)
                })

        # 转换字段名以匹配客户端期望的格式
        enhanced_stats = {
            **stats,
            # 添加客户端期望的字段，使用服务器返回的对应字段
            "successful_requests": stats.get("success_count", 0),
            "failed_requests": stats.get("failure_count", 0),
            "avg_response_time": health_summary.get("avg_response_time", 150.0)  # 使用健康检查的平均响应时间
        }

        # 添加健康检查统计信息
        if health_summary:
            enhanced_stats.update({
                "health_check_enabled": True,
                "health_rate": health_summary.get("health_rate", 0.0),
                "healthy_proxies": health_summary.get("healthy_proxies", 0),
                "unhealthy_proxies": health_summary.get("unhealthy_proxies", 0),
                "last_health_check": health_summary.get("last_check_time"),
                "total_health_checks": health_summary.get("total_checks", 0),
            })
        else:
            enhanced_stats.update({
                "health_check_enabled": False,
                "health_rate": 0.0,
                "healthy_proxies": 0,
                "unhealthy_proxies": 0,
                "last_health_check": None,
                "total_health_checks": 0,
            })

        response_data = {
            "market": market.lower(),
            "mode": manager.mode.value,  # 客户端期望的字段
            "running": manager.is_running,
            "stats": enhanced_stats,
            # 客户端期望的字段格式 - 新增必需字段以解决序列化错误
            "pool_info": {
                "active_pool": proxy_details.get("active_pool"),
                "standby_pool": proxy_details.get("standby_pool"),
                "total_count": proxy_details.get("total_count", 0),
                # Kotlin客户端期望的新字段
                "pool_name": enhanced_stats.get("active_pool", "A"),
                "current_size": enhanced_stats.get("active_pool_size", 0),
                "target_size": enhanced_stats.get("total_pool_size", 200),  # 从配置获取或使用当前大小
                "rotation_count": max(0, enhanced_stats.get("uptime_hours", 0) * 24),  # 基于运行时间估算轮换次数
                "status": enhanced_stats.get("status", "unknown")
            },
            "proxies": {
                "active": proxy_details.get("active_proxies", []),
                "standby": proxy_details.get("standby_proxies", [])
            },
            "active_count": len(proxy_details.get("active_proxies", [])),
            "failed_count": enhanced_stats.get("failure_count", 0),
            **proxy_details,
            "timestamp": datetime.now().isoformat()
        }

        # 记录成功响应（避免JSON转义问题）
        stats_summary_escaped = str({
            "success_rate": enhanced_stats.get("success_rate", 0),
            "total_requests": enhanced_stats.get("total_requests", 0),
            "pool_size": enhanced_stats.get("total_pool_size", 0)
        }).replace("{", "{{").replace("}", "}}")
        log.info(f"[{request_id}] API Response - list_proxies SUCCESS", extra={
            "request_id": request_id,
            "response_status": "success",
            "service_running": manager.is_running,
            "active_proxies_count": len(proxy_details.get("active_proxies", [])),
            "standby_proxies_count": len(proxy_details.get("standby_proxies", [])),
            "total_count": proxy_details.get("total_count", 0),
            "stats_summary_str": stats_summary_escaped
        })

        return response_data

    except Exception as e:
        error_msg = f"Failed to list proxies: {str(e)}"

        # 记录错误响应和堆栈
        log.error(f"[{request_id}] API Response - list_proxies ERROR: {error_msg}", extra={
            "request_id": request_id,
            "response_status": "error",
            "error_message": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })

        raise HTTPException(status_code=500, detail=error_msg)


# ========== 批量操作接口 ==========


@router.post("/batch/start")
async def batch_start_services(
    markets: List[str] = Body(..., description="要启动的市场列表"),
    mode: str = Body("live", description="模式: live/backfill"),
    managers: dict = Depends(get_all_managers),
):
    """批量启动服务"""
    results = {}

    for market in markets:
        key = f"{market.lower()}_{mode.lower()}"
        manager = managers.get(key)

        if not manager:
            results[market] = {"status": "error", "message": "Manager not found"}
            continue

        try:
            await manager.start()
            results[market] = {
                "status": "started",
                "message": "Service started successfully",
            }
        except Exception as e:
            results[market] = {"status": "error", "message": str(e)}

    return {"results": results}


@router.post("/batch/stop")
async def batch_stop_services(
    markets: List[str] = Body(..., description="要停止的市场列表"),
    mode: str = Body("live", description="模式: live/backfill"),
    managers: dict = Depends(get_all_managers),
):
    """批量停止服务"""
    results = {}

    for market in markets:
        key = f"{market.lower()}_{mode.lower()}"
        manager = managers.get(key)

        if not manager:
            results[market] = {"status": "error", "message": "Manager not found"}
            continue

        try:
            await manager.stop()
            results[market] = {
                "status": "stopped",
                "message": "Service stopped successfully",
            }
        except Exception as e:
            results[market] = {"status": "error", "message": str(e)}

    return {"results": results}
