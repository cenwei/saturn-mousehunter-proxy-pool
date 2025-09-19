"""
Domain层 - 代理池配置实体和值对象
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class ProxyPoolMode(Enum):
    """代理池模式"""

    LIVE = "live"
    BACKFILL = "backfill"


@dataclass
class ProxyPoolConfig:
    """代理池配置实体"""

    id: Optional[int] = None
    market: str = "HK"
    mode: ProxyPoolMode = ProxyPoolMode.LIVE

    # 海量代理配置
    hailiang_api_url: str = ""
    hailiang_enabled: bool = True

    # 代理池参数
    batch_size: int = 400
    proxy_lifetime_minutes: int = 10
    rotation_interval_minutes: int = 7
    low_watermark: int = 50
    target_size: int = 200

    # 交易日配置
    auto_start_enabled: bool = True
    pre_market_start_minutes: int = 30
    post_market_stop_minutes: int = 30

    # backfill模式配置
    backfill_enabled: bool = False
    backfill_duration_hours: int = 2

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    @property
    def rotation_interval_seconds(self) -> int:
        """获取轮换间隔秒数"""
        return self.rotation_interval_minutes * 60

    @property
    def proxy_lifetime_seconds(self) -> int:
        """获取代理生命周期秒数"""
        return self.proxy_lifetime_minutes * 60


@dataclass
class ProxyPoolStatus:
    """代理池运行状态实体"""

    id: Optional[int] = None
    market: str = "HK"
    mode: ProxyPoolMode = ProxyPoolMode.LIVE

    # 运行状态
    is_running: bool = False
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_rotation_at: Optional[datetime] = None

    # 统计信息
    active_pool: str = "A"
    pool_a_size: int = 0
    pool_b_size: int = 0
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0

    # 元数据
    updated_at: Optional[datetime] = None

    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return round((self.success_count / self.total_requests) * 100, 2)


class IProxyPoolConfigRepository:
    """代理池配置仓储接口"""

    async def get_config(
        self, market: str, mode: ProxyPoolMode
    ) -> Optional[ProxyPoolConfig]:
        """获取配置"""
        raise NotImplementedError

    async def save_config(self, config: ProxyPoolConfig) -> ProxyPoolConfig:
        """保存配置"""
        raise NotImplementedError

    async def update_config(self, config: ProxyPoolConfig) -> bool:
        """更新配置"""
        raise NotImplementedError

    async def get_all_active_configs(self) -> list[ProxyPoolConfig]:
        """获取所有激活的配置"""
        raise NotImplementedError


class IProxyPoolStatusRepository:
    """代理池状态仓储接口"""

    async def get_status(
        self, market: str, mode: ProxyPoolMode
    ) -> Optional[ProxyPoolStatus]:
        """获取状态"""
        raise NotImplementedError

    async def save_status(self, status: ProxyPoolStatus) -> ProxyPoolStatus:
        """保存状态"""
        raise NotImplementedError

    async def update_status(self, status: ProxyPoolStatus) -> bool:
        """更新状态"""
        raise NotImplementedError

    async def update_pool_stats(
        self,
        market: str,
        mode: ProxyPoolMode,
        active_pool: str,
        pool_a_size: int,
        pool_b_size: int,
    ) -> bool:
        """更新池统计信息"""
        raise NotImplementedError

    async def increment_request_stats(
        self, market: str, mode: ProxyPoolMode, success: bool
    ) -> bool:
        """增加请求统计"""
        raise NotImplementedError
