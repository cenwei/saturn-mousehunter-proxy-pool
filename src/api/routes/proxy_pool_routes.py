"""
API层 - 代理池路由
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from saturn_mousehunter_shared import get_logger
from infrastructure.proxy_pool import ProxyPoolManager
from domain.config_entities import ProxyPoolMode

router = APIRouter(tags=["proxy_pool"])
log = get_logger("proxy_pool_routes")


class RpcRequest(BaseModel):
    """RPC请求模型"""
    event: str
    proxy_type: Optional[str] = "short"
    proxy_addr: Optional[str] = None
    market: Optional[str] = "hk"
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
    market: str = Query(..., description="市场代码: cn/hk/us"),
    mode: str = Query("live", description="模式: live/backfill")
) -> ProxyPoolManager:
    """获取代理池管理器依赖"""
    from main import get_proxy_pool_manager as get_manager
    try:
        return get_manager(market, mode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def get_all_managers() -> dict[str, ProxyPoolManager]:
    """获取所有管理器依赖"""
    from main import get_all_proxy_pool_managers
    return get_all_proxy_pool_managers()


# ========== 服务管理接口 ==========

@router.get("/pools")
async def list_pools(managers: dict = Depends(get_all_managers)):
    """列出所有代理池"""
    pools = []
    for key, manager in managers.items():
        market, mode = key.split("_", 1)
        status = await manager.get_status()
        pools.append({
            "key": key,
            "market": market,
            "mode": mode,
            "running": manager.is_running,
            "status": status
        })
    return {"pools": pools}


@router.get("/config")
async def get_config(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取配置信息"""
    config_dict = await manager.get_config_dict()
    return {
        "market": manager.market,
        "mode": manager.mode.value,
        "config": config_dict,
        "backend": "database_driven"
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
        stats=service_status.get("stats", {})
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
            "success_rate": 0.0
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
        "failure_count": stats.get("failure_count", 0)
    }


# ========== 服务控制接口 ==========

@router.post("/start")
async def start_service(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """启动服务"""
    try:
        await manager.start()
        return {
            "status": "started",
            "message": f"Proxy pool service started for {manager.market}/{manager.mode.value}"
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
            "message": f"Proxy pool service stopped for {manager.market}/{manager.mode.value}"
        }
    except Exception as e:
        log.error(f"Failed to stop service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backfill/start")
async def start_backfill(
    request: BackfillStartRequest,
    managers: dict = Depends(get_all_managers)
):
    """启动backfill模式代理池"""
    key = f"{request.market.lower()}_backfill"
    manager = managers.get(key)

    if not manager:
        raise HTTPException(status_code=404, detail=f"Backfill manager not found for market {request.market}")

    try:
        await manager.start_manual(request.duration_hours)
        return {
            "status": "started",
            "message": f"Backfill proxy pool started for {request.market}",
            "duration_hours": request.duration_hours
        }
    except Exception as e:
        log.error(f"Failed to start backfill service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ========== 配置管理接口 ==========

@router.post("/config")
async def update_config(
    request: ConfigUpdateRequest,
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager)
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
                "config": config_dict
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update configuration")

    except Exception as e:
        log.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/hailiang/test")
async def test_hailiang_api(
    api_url: str = Body(..., embed=True),
    market: str = Query("hk", description="市场代码")
):
    """测试海量代理API"""
    from infrastructure.proxy_fetchers import fetch_hailiang_proxy_ip

    try:
        proxies = await fetch_hailiang_proxy_ip(api_url)
        return {
            "status": "success",
            "message": f"Successfully fetched {len(proxies)} proxies",
            "proxy_count": len(proxies),
            "sample_proxies": proxies[:5] if proxies else []
        }
    except Exception as e:
        log.error(f"Failed to test Hailiang API: {e}")
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")


# ========== RPC接口 ==========

@router.post("/rpc")
async def rpc_handler(
    request: RpcRequest = Body(...),
    managers: dict = Depends(get_all_managers)
):
    """RPC接口 - 兼容原ZMQ事件格式"""
    event = request.event.lower().strip()
    market = request.market or "hk"
    mode = request.mode or "live"

    key = f"{market.lower()}_{mode.lower()}"
    manager = managers.get(key)

    if not manager:
        raise HTTPException(status_code=404, detail=f"Manager not found for {market}/{mode}")

    if not manager.is_running and event != "ping":
        raise HTTPException(status_code=400, detail=f"Service not running for {market}/{mode}")

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
            "service_mode": manager.mode.value
        }

    elif event == "ping":
        status = await manager.get_status() if manager.is_running else {"market_status": "stopped"}
        return {
            "status": "ok",
            "message": "pong",
            "market": manager.market,
            "mode": manager.mode.value,
            "running": manager.is_running,
            "market_status": status.get("market_status", "unknown")
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown event: {request.event}")


# ========== 批量操作接口 ==========

@router.post("/batch/start")
async def batch_start_services(
    markets: List[str] = Body(..., description="要启动的市场列表"),
    mode: str = Body("live", description="模式: live/backfill"),
    managers: dict = Depends(get_all_managers)
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
            results[market] = {"status": "started", "message": "Service started successfully"}
        except Exception as e:
            results[market] = {"status": "error", "message": str(e)}

    return {"results": results}


@router.post("/batch/stop")
async def batch_stop_services(
    markets: List[str] = Body(..., description="要停止的市场列表"),
    mode: str = Body("live", description="模式: live/backfill"),
    managers: dict = Depends(get_all_managers)
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
            results[market] = {"status": "stopped", "message": "Service stopped successfully"}
        except Exception as e:
            results[market] = {"status": "error", "message": str(e)}

    return {"results": results}