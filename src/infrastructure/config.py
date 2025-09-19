"""
Infrastructure层 - 应用配置
"""

import os
from typing import List
from dataclasses import dataclass
from saturn_mousehunter_shared import get_logger
from saturn_mousehunter_shared.config.service_endpoints import get_service_config

log = get_logger(__name__)


@dataclass
class CORSConfig:
    """CORS配置"""

    allow_origins: List[str]
    allow_methods: List[str] = None
    allow_headers: List[str] = None
    allow_credentials: bool = True

    def __post_init__(self):
        if self.allow_methods is None:
            self.allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        if self.allow_headers is None:
            self.allow_headers = ["*"]


@dataclass
class ProxyPoolConfig:
    """代理池配置"""

    market: str = "hk"
    mode: str = "live"
    auto_start: bool = True
    pool_type: str = "memory_ab"

    # 池参数
    rotate_interval_sec: int = 180
    low_watermark: int = 5
    target_size: int = 20
    check_interval_sec: int = 60
    termination_grace_sec: int = 10

    # 获取参数
    single_batch_size: int = 200
    min_refresh_secs: int = 420
    batch_count: int = 2

    # 海量代理配置
    hailiang_api_url: str = ""
    hailiang_enabled: bool = False


@dataclass
class AppConfig:
    """应用配置"""

    app_name: str = "Saturn MouseHunter Proxy Pool Service"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
    log_level: str = "INFO"
    cors: CORSConfig = None
    proxy_pool: ProxyPoolConfig = None

    def __post_init__(self):
        if self.cors is None:
            self.cors = get_cors_config()
        if self.proxy_pool is None:
            self.proxy_pool = get_proxy_pool_config()


def get_cors_config() -> CORSConfig:
    """从环境变量获取CORS配置"""
    origins_str = os.getenv(
        "PROXY_POOL_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    )
    allow_origins = [
        origin.strip() for origin in origins_str.split(",") if origin.strip()
    ]

    return CORSConfig(
        allow_origins=allow_origins,
        allow_credentials=os.getenv("PROXY_POOL_CORS_CREDENTIALS", "true").lower()
        == "true",
    )


def get_proxy_pool_config() -> ProxyPoolConfig:
    """从环境变量获取代理池配置"""
    # 默认海量代理URL
    default_hailiang_url = "http://api.hailiangip.com:8422/api/getIp?type=1&num=20&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0"

    return ProxyPoolConfig(
        market=os.getenv("MARKET", "hk").lower(),
        mode=os.getenv("MODE", "live").lower(),
        auto_start=os.getenv("AUTO_RUN", "true").lower() == "true",
        pool_type=os.getenv("POOL_TYPE", "memory_ab"),
        rotate_interval_sec=int(os.getenv("ROTATE_INTERVAL_SEC", "180")),
        low_watermark=int(os.getenv("LOW_WATERMARK", "5")),
        target_size=int(os.getenv("TARGET_SIZE", "20")),
        check_interval_sec=int(os.getenv("CHECK_INTERVAL_SEC", "60")),
        termination_grace_sec=int(os.getenv("TERMINATION_GRACE_SEC", "10")),
        single_batch_size=int(os.getenv("SINGLE_BATCH_SIZE", "200")),
        min_refresh_secs=int(os.getenv("MIN_REFRESH_SECS", "420")),
        batch_count=int(os.getenv("BATCH_COUNT", "2")),
        hailiang_api_url=os.getenv("HAILIANG_API_URL", default_hailiang_url),
        hailiang_enabled=os.getenv("HAILIANG_ENABLED", "false").lower() == "true",
    )


def get_app_config() -> AppConfig:
    """从环境变量和服务端点配置获取应用配置"""
    # 获取环境变量
    environment = os.getenv("ENVIRONMENT", "development").lower()

    # 获取代理池服务的端点配置
    try:
        proxy_pool_config = get_service_config("proxy-pool-service", environment)
        default_host = proxy_pool_config["host"]
        default_port = proxy_pool_config["port"]
        log.info(
            "Using service endpoint config for %s: %s", environment, proxy_pool_config
        )
    except Exception as e:
        log.warning(f"Failed to load service endpoint config: {e}, using defaults")
        default_host = "0.0.0.0"
        default_port = 8080

    return AppConfig(
        app_name=os.getenv(
            "PROXY_POOL_APP_NAME", "Saturn MouseHunter Proxy Pool Service"
        ),
        version=os.getenv("PROXY_POOL_VERSION", "1.0.0"),
        debug=os.getenv("PROXY_POOL_DEBUG", "false").lower() == "true",
        host=os.getenv("HOST", default_host),
        port=int(os.getenv("PORT", str(default_port))),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
