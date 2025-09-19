"""
Domain层 - 初始化
"""

from .entities import (
    MarketType,
    ProxyMode,
    ProxyStatus,
    Proxy,
    ProxyPoolStats,
    IProxyRepository,
    IProxyFetcher,
    IMarketClock,
)
from .services import ProxyPoolDomainService
from .config_entities import (
    ProxyPoolConfig,
    ProxyPoolStatus as PoolStatus,
    ProxyPoolMode,
    IProxyPoolConfigRepository,
    IProxyPoolStatusRepository,
)

__all__ = [
    "MarketType",
    "ProxyMode",
    "ProxyStatus",
    "Proxy",
    "ProxyPoolStats",
    "IProxyRepository",
    "IProxyFetcher",
    "IMarketClock",
    "ProxyPoolDomainService",
    "ProxyPoolConfig",
    "PoolStatus",
    "ProxyPoolMode",
    "IProxyPoolConfigRepository",
    "IProxyPoolStatusRepository",
]
