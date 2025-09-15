"""
代理池轮换微服务 - 主应用文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from saturn_mousehunter_shared import get_logger
from typing import Optional
from infrastructure.config import get_app_config
from infrastructure.proxy_pool import ProxyPoolManager
from infrastructure.global_scheduler import GlobalScheduler
from infrastructure.monitoring import AlertManager, HealthMonitor
from domain.config_entities import ProxyPoolMode
from api.routes import proxy_pool_routes
import os

log = get_logger(__name__)

# 获取配置
app_config = get_app_config()

# 全局代理池管理器字典
proxy_pool_managers: dict[str, ProxyPoolManager] = {}

# 全局调度器
global_scheduler: Optional[GlobalScheduler] = None

# 监控系统
alert_manager: Optional[AlertManager] = None
health_monitor: Optional[HealthMonitor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global proxy_pool_managers, global_scheduler, alert_manager, health_monitor

    # 启动阶段
    log.info(f"启动代理池服务 - {app_config.app_name} v{app_config.version}")

    # 初始化监控系统
    alert_manager = AlertManager()
    health_monitor = HealthMonitor(alert_manager)

    alert_manager.alert_info(
        "Service Starting",
        f"{app_config.app_name} v{app_config.version} is starting up",
        component="SYSTEM"
    )

    # 从环境变量获取要启动的市场
    markets = os.getenv("MARKETS", "hk").split(",")

    for market in markets:
        market = market.strip().lower()

        # 创建live模式的代理池管理器
        live_manager = ProxyPoolManager(market, ProxyPoolMode.LIVE)
        proxy_pool_managers[f"{market}_live"] = live_manager

        # 创建backfill模式的代理池管理器
        backfill_manager = ProxyPoolManager(market, ProxyPoolMode.BACKFILL)
        proxy_pool_managers[f"{market}_backfill"] = backfill_manager

        log.info(f"Created proxy pool managers for market {market}")

        alert_manager.alert_info(
            "Market Initialized",
            f"Proxy pool managers created for market {market.upper()}",
            market.upper(),
            "INITIALIZATION"
        )

    # 启动全局调度器
    global_scheduler = GlobalScheduler(get_proxy_pool_manager)
    await global_scheduler.start()

    alert_manager.alert_info(
        "Scheduler Started",
        "Global scheduler started successfully",
        component="SCHEDULER"
    )

    log.info(f"代理池服务已启动 - {app_config.app_name} v{app_config.version}")

    yield

    # 关闭阶段
    log.info("正在关闭代理池服务...")

    alert_manager.alert_info(
        "Service Stopping",
        "代理池服务正在关闭",
        component="SYSTEM"
    )

    # 停止全局调度器
    if global_scheduler:
        await global_scheduler.stop()

    # 停止所有管理器
    for key, manager in proxy_pool_managers.items():
        if manager.is_running:
            try:
                await manager.stop()
                log.info(f"Stopped proxy pool manager: {key}")
            except Exception as e:
                log.error(f"Error stopping manager {key}: {e}")
                if alert_manager:
                    alert_manager.alert_error(
                        "Manager Stop Failed",
                        f"Failed to stop manager {key}: {str(e)}",
                        component="SHUTDOWN"
                    )

    proxy_pool_managers.clear()

    alert_manager.alert_info(
        "Service Stopped",
        "代理池服务已关闭",
        component="SYSTEM"
    )

    log.info("代理池服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=app_config.app_name,
    version=app_config.version,
    debug=app_config.debug,
    description="Saturn MouseHunter代理池轮换微服务 - 支持多市场自动调度",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors.allow_origins,
    allow_credentials=app_config.cors.allow_credentials,
    allow_methods=app_config.cors.allow_methods,
    allow_headers=app_config.cors.allow_headers,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def admin_interface():
    """管理界面"""
    return FileResponse("static/admin.html")


@app.get("/health")
async def health_check():
    """健康检查"""
    running_pools = {
        key: manager.is_running
        for key, manager in proxy_pool_managers.items()
    }

    any_running = any(running_pools.values())

    return {
        "status": "healthy" if any_running else "partial",
        "service": app_config.app_name,
        "version": app_config.version,
        "proxy_pools": running_pools,
        "total_pools": len(proxy_pool_managers),
        "running_pools": sum(running_pools.values())
    }


# 注册路由
app.include_router(proxy_pool_routes.router, prefix="/api/v1")


# 依赖注入工厂函数
def get_proxy_pool_manager(market: str, mode: str = "live") -> ProxyPoolManager:
    """获取代理池管理器"""
    key = f"{market.lower()}_{mode.lower()}"
    manager = proxy_pool_managers.get(key)
    if not manager:
        raise ValueError(f"Proxy pool manager not found for {market}/{mode}")
    return manager


def get_all_proxy_pool_managers() -> dict[str, ProxyPoolManager]:
    """获取所有代理池管理器"""
    return proxy_pool_managers


def main():
    """主函数"""
    import uvicorn
    uvicorn.run(
        "main:app",
        host=app_config.host,
        port=app_config.port,
        reload=app_config.reload,
        log_level=app_config.log_level.lower()
    )


if __name__ == "__main__":
    main()