"""
Domain层 - 代理池核心业务模型
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Protocol


class MarketType(str, enum.Enum):
    """市场类型枚举"""

    US = "US"
    HK = "HK"
    CN = "CN"
    SG = "SG"
    JP = "JP"
    KR = "KR"
    UK = "UK"
    EU = "EU"


class ProxyMode(str, enum.Enum):
    """代理池模式枚举"""

    LIVE = "live"
    TEST = "test"
    BACKTEST = "backtest"


class ProxyStatus(str, enum.Enum):
    """代理状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


@dataclass
class Proxy:
    """代理实体"""

    addr: str
    proxy_type: str = "short"
    status: ProxyStatus = ProxyStatus.ACTIVE
    failure_count: int = 0
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def mark_used(self) -> None:
        """标记为已使用"""
        self.last_used = datetime.now()

    def mark_failure(self) -> None:
        """标记失败"""
        self.failure_count += 1
        self.status = ProxyStatus.FAILED

    def is_healthy(self) -> bool:
        """检查代理是否健康"""
        return self.status == ProxyStatus.ACTIVE and self.failure_count < 3


@dataclass
class ProxyPoolStats:
    """代理池统计信息"""

    market: str
    mode: str
    pool_type: str
    active_pool: str
    standby_pool: str
    active_pool_size: int
    standby_pool_size: int
    total_pool_size: int
    last_switch_time: str
    switch_ago_seconds: int
    uptime_seconds: int
    uptime_hours: float
    total_requests: int
    success_count: int
    failure_count: int
    success_rate: float
    last_fetch_time: str
    last_fetch_count: int
    status: str


class IProxyRepository(ABC):
    """代理仓储接口"""

    @abstractmethod
    async def get_proxy_from_pool(self, proxy_type: str = "short") -> Optional[Proxy]:
        """从池中获取代理"""
        pass

    @abstractmethod
    async def mark_failure(self, proxy_addr: str) -> None:
        """标记代理失败"""
        pass

    @abstractmethod
    async def get_stats(self) -> ProxyPoolStats:
        """获取代理池统计信息"""
        pass

    @abstractmethod
    async def start_maintenance(self) -> None:
        """启动维护任务"""
        pass

    @abstractmethod
    async def stop_maintenance(self) -> None:
        """停止维护任务"""
        pass


class IProxyFetcher(Protocol):
    """代理获取器接口"""

    async def fetch_proxies(self, count: int = 20) -> List[str]:
        """获取代理列表"""
        pass


class IMarketClock(Protocol):
    """市场时钟接口"""

    def is_market_open(self, market: str) -> bool:
        """判断市场是否开盘"""
        pass

    def should_terminate_after_close(self, market: str) -> bool:
        """判断是否应该在收盘后终止"""
        pass

    def get_market_status_desc(self, market: str) -> str:
        """获取市场状态描述"""
        pass
