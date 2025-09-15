"""
API层 - 代理池路由
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional

from saturn_mousehunter_shared import get_logger
from infrastructure.proxy_pool import ProxyPoolManager

router = APIRouter(tags=["proxy_pool"])
log = get_logger("proxy_pool_routes")


class RpcRequest(BaseModel):
    """RPC请求模型"""
    event: str
    proxy_type: Optional[str] = "short"
    proxy_addr: Optional[str] = None


class HailiangConfigRequest(BaseModel):
    """海量代理配置请求模型"""
    api_url: str
    enabled: bool = True


class HailiangConfigResponse(BaseModel):
    """海量代理配置响应模型"""
    api_url: str
    enabled: bool
    status: str
    message: str


class StatusResponse(BaseModel):
    """状态响应模型"""
    status: str
    running: bool
    market: str
    mode: str
    market_status: str
    stats: Dict[str, Any]


def get_proxy_pool_manager() -> ProxyPoolManager:
    """获取代理池管理器依赖"""
    from main import get_proxy_pool_manager
    manager = get_proxy_pool_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Proxy pool manager not available")
    return manager


@router.get("/config")
async def get_config(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取配置信息"""
    return {
        "market": manager.config.market,
        "mode": manager.config.mode,
        "config": manager.config.__dict__,
        "backend": "memory_ab_pool",
        "auto_start": manager.config.auto_start
    }


@router.get("/status", response_model=StatusResponse)
async def get_status(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取服务状态"""
    service_status = await manager.get_status()

    return StatusResponse(
        status="ok",
        running=manager.is_running,
        market=manager.config.market,
        mode=manager.config.mode,
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


@router.post("/start")
async def start_service(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """启动服务"""
    try:
        await manager.start()
        return {"status": "started", "message": "Proxy pool service started successfully"}
    except Exception as e:
        log.error(f"Failed to start service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
async def stop_service(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """停止服务"""
    try:
        await manager.stop()
        return {"status": "stopped", "message": "Proxy pool service stopped successfully"}
    except Exception as e:
        log.error(f"Failed to stop service: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rotate")
async def rotate_pool(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """手动轮换代理池"""
    if not manager.is_running:
        raise HTTPException(status_code=400, detail="Service not running")

    return {
        "status": "ok",
        "message": "Pool rotation is managed by the maintenance loop automatically"
    }


@router.get("/hailiang/config", response_model=HailiangConfigResponse)
async def get_hailiang_config(manager: ProxyPoolManager = Depends(get_proxy_pool_manager)):
    """获取海量代理配置"""
    config = await manager.get_hailiang_config()
    return HailiangConfigResponse(
        api_url=config["api_url"],
        enabled=config["enabled"],
        status="ok",
        message=f"Current fetcher: {config['current_fetcher']}"
    )


@router.post("/hailiang/config", response_model=HailiangConfigResponse)
async def update_hailiang_config(
    request: HailiangConfigRequest,
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager)
):
    """更新海量代理配置"""
    try:
        success = await manager.update_hailiang_config(request.api_url, request.enabled)

        if success:
            return HailiangConfigResponse(
                api_url=request.api_url,
                enabled=request.enabled,
                status="success",
                message="Hailiang proxy configuration updated successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to update Hailiang proxy configuration"
            )
    except Exception as e:
        log.error(f"Failed to update Hailiang config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hailiang/test")
async def test_hailiang_api(
    request: HailiangConfigRequest,
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager)
):
    """测试海量代理API"""
    from infrastructure.proxy_fetchers import fetch_hailiang_proxy_ip

    try:
        proxies = await fetch_hailiang_proxy_ip(request.api_url)
        return {
            "status": "success",
            "message": f"Successfully fetched {len(proxies)} proxies",
            "proxy_count": len(proxies),
            "sample_proxies": proxies[:5] if proxies else []
        }
    except Exception as e:
        log.error(f"Failed to test Hailiang API: {e}")
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")


@router.post("/rpc")
async def rpc_handler(
    request: RpcRequest = Body(...),
    manager: ProxyPoolManager = Depends(get_proxy_pool_manager)
):
    """RPC接口 - 兼容原ZMQ事件格式"""
    if not manager.is_running:
        raise HTTPException(status_code=400, detail="Service not running")

    event = request.event.lower().strip()

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
            "service_mode": manager.config.mode
        }

    elif event == "ping":
        return {
            "status": "ok",
            "message": "pong",
            "market": manager.config.market,
            "mode": manager.config.mode,
            "market_status": (await manager.get_status()).get("market_status", "unknown")
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown event: {request.event}")