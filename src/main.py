"""
代理池轮换微服务 - 主应用文件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from saturn_mousehunter_shared import get_logger
from infrastructure.config import get_app_config
from infrastructure.proxy_pool import ProxyPoolManager
from api.routes import proxy_pool_routes

log = get_logger(__name__)

# 获取配置
app_config = get_app_config()

# 全局代理池管理器
proxy_pool_manager: ProxyPoolManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global proxy_pool_manager

    # 启动阶段
    log.info(f"启动代理池服务 - {app_config.app_name} v{app_config.version}")
    proxy_pool_manager = ProxyPoolManager(app_config.proxy_pool)

    if app_config.proxy_pool.auto_start:
        await proxy_pool_manager.start()

    log.info(f"代理池服务已启动 - {app_config.app_name} v{app_config.version}")

    yield

    # 关闭阶段
    log.info("正在关闭代理池服务...")
    if proxy_pool_manager:
        await proxy_pool_manager.stop()
    log.info("代理池服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=app_config.app_name,
    version=app_config.version,
    debug=app_config.debug,
    description="Saturn MouseHunter代理池轮换微服务",
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
    pool_healthy = proxy_pool_manager.is_running if proxy_pool_manager else False
    stats = await proxy_pool_manager.get_status() if proxy_pool_manager else {}

    return {
        "status": "healthy" if pool_healthy else "unhealthy",
        "service": app_config.app_name,
        "version": app_config.version,
        "proxy_pool": "running" if pool_healthy else "stopped",
        "market": app_config.proxy_pool.market,
        "mode": app_config.proxy_pool.mode,
        "stats": stats.get("stats", {})
    }


# 注册路由
app.include_router(proxy_pool_routes.router, prefix="/api/v1")


# 依赖注入工厂函数
def get_proxy_pool_manager():
    return proxy_pool_manager


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