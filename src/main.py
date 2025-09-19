"""
代理池轮换微服务 - 主应用文件
集成交易日历服务模块
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from saturn_mousehunter_shared import get_logger

# 添加src目录到Python路径，解决模块导入问题
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 加载 .env 文件（必须在业务模块导入之前）
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env 文件已加载")
except ImportError:
    print("⚠️ python-dotenv 未安装，跳过 .env 文件加载")

# 导入业务模块（在路径设置和环境加载之后）
import api.routes.proxy_pool_routes as proxy_pool_routes  # noqa: E402
import domain.config_entities as config_entities  # noqa: E402
import infrastructure.dependencies as dependencies  # noqa: E402
import infrastructure.config as infrastructure_config  # noqa: E402
import infrastructure.global_scheduler as global_scheduler  # noqa: E402
import infrastructure.monitoring as monitoring  # noqa: E402
import infrastructure.proxy_pool as proxy_pool  # noqa: E402

# 创建模块别名以保持向后兼容
ProxyPoolMode = config_entities.ProxyPoolMode
get_app_config = infrastructure_config.get_app_config
GlobalScheduler = global_scheduler.GlobalScheduler
AlertManager = monitoring.AlertManager
HealthMonitor = monitoring.HealthMonitor
ProxyPoolManager = proxy_pool.ProxyPoolManager
proxy_pool_router = proxy_pool_routes.router

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
    log.info(f"服务配置 - Host: {app_config.host}, Port: {app_config.port}")

    # 获取环境信息
    environment = os.getenv("ENVIRONMENT", "development")
    log.info(f"运行环境: {environment}")

    # 初始化监控系统
    alert_manager = AlertManager()
    health_monitor = HealthMonitor(alert_manager)

    alert_manager.alert_info(
        "Service Starting",
        f"{app_config.app_name} v{app_config.version} is starting up",
        component="SYSTEM",
    )

    # 从环境变量获取要启动的市场
    markets = os.getenv("MARKETS", "CN").split(",")

    for market in markets:
        market = market.strip().upper()  # 改为大写，与dependencies保持一致

        # 创建live模式的代理池管理器
        live_manager = ProxyPoolManager(
            market, ProxyPoolMode.LIVE
        )  # 传入大写market，ProxyPoolManager内部会转小写用于标识
        proxy_pool_managers[f"{market}_live"] = live_manager

        # 创建backfill模式的代理池管理器
        backfill_manager = ProxyPoolManager(market, ProxyPoolMode.BACKFILL)
        proxy_pool_managers[f"{market}_backfill"] = backfill_manager

        log.info(f"Created proxy pool managers for market {market}")

        alert_manager.alert_info(
            "Market Initialized",
            f"Proxy pool managers created for market {market}",
            market,
            "INITIALIZATION",
        )

    # 启动全局调度器
    global_scheduler = GlobalScheduler(get_proxy_pool_manager)
    await global_scheduler.start()

    # 注册到依赖注入模块
    dependencies.set_proxy_pool_managers(proxy_pool_managers)
    dependencies.set_global_scheduler(global_scheduler)
    dependencies.set_alert_manager(alert_manager)
    dependencies.set_health_monitor(health_monitor)

    alert_manager.alert_info(
        "Scheduler Started",
        "Global scheduler started successfully",
        component="SCHEDULER",
    )

    log.info(f"代理池服务已启动 - {app_config.app_name} v{app_config.version}")

    yield

    # 关闭阶段
    log.info("正在关闭代理池服务...")

    alert_manager.alert_info(
        "Service Stopping", "代理池服务正在关闭", component="SYSTEM"
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
                        component="SHUTDOWN",
                    )

    proxy_pool_managers.clear()

    alert_manager.alert_info("Service Stopped", "代理池服务已关闭", component="SYSTEM")

    log.info("代理池服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=app_config.app_name,
    version=app_config.version,
    debug=app_config.debug,
    description="Saturn MouseHunter代理池轮换微服务 - 支持多市场自动调度",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors.allow_origins,
    allow_credentials=app_config.cors.allow_credentials,
    allow_methods=app_config.cors.allow_methods,
    allow_headers=app_config.cors.allow_headers,
)

# 注册路由
app.include_router(proxy_pool_router, prefix="/api/v1")

# 挂载静态文件
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def admin_interface():
    """管理界面"""
    return FileResponse("static/admin.html")


@app.get("/health")
async def health_check():
    """健康检查"""
    running_pools = {
        key: manager.is_running for key, manager in proxy_pool_managers.items()
    }

    any_running = any(running_pools.values())

    return {
        "status": "healthy" if any_running else "partial",
        "service": app_config.app_name,
        "version": app_config.version,
        "proxy_pools": running_pools,
        "total_pools": len(proxy_pool_managers),
        "running_pools": sum(running_pools.values()),
    }


# 依赖注入工厂函数
def get_proxy_pool_manager(market: str, mode: str = "live") -> ProxyPoolManager:
    """获取代理池管理器"""
    key = f"{market.upper()}_{mode.lower()}"  # 修改为与dependencies一致
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
        log_level=app_config.log_level.lower(),
    )


if __name__ == "__main__":
    main()
