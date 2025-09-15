"""
代理池轮换微服务 - 主应用文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from saturn_mousehunter_shared import get_logger
from infrastructure.config import get_app_config
from infrastructure.proxy_pool import ProxyPoolManager
from domain.config_entities import ProxyPoolMode
from api.routes import proxy_pool_routes
import os

log = get_logger(__name__)

# 获取配置
app_config = get_app_config()

# 全局代理池管理器字典
proxy_pool_managers: dict[str, ProxyPoolManager] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global proxy_pool_managers

    # 启动阶段
    log.info(f"启动代理池服务 - {app_config.app_name} v{app_config.version}")

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

        # 如果配置为自动启动，则启动live模式
        if app_config.proxy_pool.auto_start:
            try:
                await live_manager.start()
                log.info(f"Auto-started live proxy pool for market {market}")
            except Exception as e:
                log.error(f"Failed to auto-start proxy pool for {market}: {e}")

    log.info(f"代理池服务已启动 - {app_config.app_name} v{app_config.version}")

    yield

    # 关闭阶段
    log.info("正在关闭代理池服务...")
    for key, manager in proxy_pool_managers.items():
        if manager.is_running:
            try:
                await manager.stop()
                log.info(f"Stopped proxy pool manager: {key}")
            except Exception as e:
                log.error(f"Error stopping manager {key}: {e}")

    proxy_pool_managers.clear()
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