"""
Infrastructure层 - 代理池管理器
"""

from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime

from saturn_mousehunter_shared import get_logger
from domain import (
    MarketType, ProxyMode, ProxyPoolDomainService,
    ProxyPoolConfig, PoolStatus, ProxyPoolMode,
    IProxyPoolConfigRepository, IProxyPoolStatusRepository
)
from application import ProxyPoolApplicationService
from .market_clock import MarketClockService
from .proxy_fetchers import MockProxyFetcher, ExternalProxyFetcher, HailiangProxyFetcher
from .memory_proxy_repository import MemoryProxyRepository
from .database_repositories import DatabaseProxyPoolConfigRepository, DatabaseProxyPoolStatusRepository


class ProxyPoolManager:
    """代理池管理器 - 负责依赖注入和生命周期管理"""

    def __init__(self, market: str, mode: ProxyPoolMode = ProxyPoolMode.LIVE):
        self.market = market.lower()
        self.mode = mode
        self.logger = get_logger(f"proxy_pool_manager.{market}.{mode.value}")

        # 数据库仓储
        self._config_repo: IProxyPoolConfigRepository = DatabaseProxyPoolConfigRepository()
        self._status_repo: IProxyPoolStatusRepository = DatabaseProxyPoolStatusRepository()

        # 配置缓存
        self._cached_config: Optional[ProxyPoolConfig] = None

        # 创建依赖
        self._market_clock = MarketClockService()

        # 延迟初始化的组件
        self._fetcher = None
        self._repository = None
        self._domain_service = None
        self._application_service = None

        # 状态
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None

    async def _load_config(self) -> ProxyPoolConfig:
        """加载配置"""
        if self._cached_config:
            return self._cached_config

        config = await self._config_repo.get_config(self.market, self.mode)
        if not config:
            # 创建默认配置
            config = ProxyPoolConfig(
                market=self.market,
                mode=self.mode,
                hailiang_api_url="http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0",
                hailiang_enabled=True
            )
            config = await self._config_repo.save_config(config)
            self.logger.info(f"Created default config for {self.market}/{self.mode.value}")

        self._cached_config = config
        return config

    async def _invalidate_config_cache(self) -> None:
        """失效配置缓存"""
        self._cached_config = None

    async def _initialize_components(self) -> None:
        """初始化组件"""
        config = await self._load_config()

        # 选择代理获取器
        if config.hailiang_enabled and config.hailiang_api_url:
            self._fetcher = HailiangProxyFetcher(config.hailiang_api_url, config.market)
            self.logger.info("Using Hailiang proxy fetcher")
        else:
            self._fetcher = MockProxyFetcher(config.market)
            self.logger.info("Using mock proxy fetcher")

        # 创建代理仓储
        self._repository = MemoryProxyRepository(
            market=MarketType(config.market),
            mode=ProxyMode.LIVE if config.mode == ProxyPoolMode.LIVE else ProxyMode.MOCK,
            fetcher=self._fetcher,
            rotate_interval_sec=config.rotation_interval_seconds,
            low_watermark=config.low_watermark,
            target_size=config.target_size,
            min_refresh_secs=config.proxy_lifetime_seconds + 60,  # 比代理生命周期长1分钟
            batch_count=2  # A/B两个池
        )

        # 创建领域服务
        self._domain_service = ProxyPoolDomainService(
            proxy_repository=self._repository,
            market_clock=self._market_clock,
            market=MarketType(config.market),
            mode=ProxyMode.LIVE if config.mode == ProxyPoolMode.LIVE else ProxyMode.MOCK
        )

        # 创建应用服务
        self._application_service = ProxyPoolApplicationService(
            domain_service=self._domain_service
        )

        self.logger.info(f"Components initialized for {config.market}/{config.mode.value}")

    @property
    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self._running

    @property
    def config(self) -> Optional[ProxyPoolConfig]:
        """获取当前配置"""
        return self._cached_config

    def set_external_fetcher(self, fetch_func) -> None:
        """设置外部代理获取函数"""
        if not self._cached_config:
            raise RuntimeError("Configuration not loaded")

        self._fetcher = ExternalProxyFetcher(fetch_func, self._cached_config.market)
        self.logger.info("External proxy fetcher configured")

    async def start(self) -> None:
        """启动代理池服务"""
        if self._running:
            self.logger.warning("Service already running")
            return

        self.logger.info(f"Starting proxy pool manager for {self.market}/{self.mode.value}")

        # 初始化组件
        await self._initialize_components()

        # 启动应用服务
        await self._application_service.start_service()
        self._running = True

        # 更新状态到数据库
        await self._update_running_status(True)

        # 启动调度器（仅在live模式）
        if self.mode == ProxyPoolMode.LIVE:
            config = await self._load_config()
            if config.auto_start_enabled:
                self._scheduler_task = asyncio.create_task(self._trading_scheduler())

        self.logger.info(f"Proxy pool manager started for {self.market}/{self.mode.value}")

    async def stop(self) -> None:
        """停止代理池服务"""
        if not self._running:
            self.logger.warning("Service not running")
            return

        self.logger.info(f"Stopping proxy pool manager for {self.market}/{self.mode.value}")

        self._running = False

        # 取消调度任务
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # 取消监控任务
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # 停止应用服务
        if self._application_service:
            await self._application_service.stop_service()

        # 更新状态到数据库
        await self._update_running_status(False)

        self.logger.info(f"Proxy pool manager stopped for {self.market}/{self.mode.value}")

    async def start_manual(self, duration_hours: Optional[int] = None) -> None:
        """手动启动代理池（用于backfill模式）"""
        if self.mode != ProxyPoolMode.BACKFILL:
            raise ValueError("Manual start is only available for backfill mode")

        await self.start()

        if duration_hours:
            # 设置定时停止
            self._monitor_task = asyncio.create_task(self._auto_stop_after_duration(duration_hours))

    async def _auto_stop_after_duration(self, hours: int) -> None:
        """在指定时间后自动停止"""
        try:
            await asyncio.sleep(hours * 3600)
            self.logger.info(f"Auto-stopping after {hours} hours")
            await self.stop()
        except asyncio.CancelledError:
            pass

    async def get_proxy(self, proxy_type: str = "short") -> str | None:
        """获取代理地址"""
        if not self._running or not self._application_service:
            return None

        proxy = await self._application_service.get_proxy(proxy_type)

        # 记录请求统计
        await self._status_repo.increment_request_stats(
            self.market, self.mode, success=proxy is not None
        )

        return proxy

    async def report_failure(self, proxy_addr: str) -> None:
        """报告代理失败"""
        if not self._running or not self._application_service:
            return

        await self._application_service.report_failure(proxy_addr)

        # 记录失败统计
        await self._status_repo.increment_request_stats(
            self.market, self.mode, success=False
        )

    async def get_status(self) -> dict:
        """获取服务状态"""
        if not self._running or not self._application_service:
            return {
                "running": False,
                "market": self.market,
                "mode": self.mode.value,
                "error": "Service not running"
            }

        app_status = await self._application_service.get_status()

        # 获取数据库状态
        db_status = await self._status_repo.get_status(self.market, self.mode)

        status = {
            "running": self._running,
            "market": self.market,
            "mode": self.mode.value,
            "market_status": app_status.get("market_status", "unknown"),
            "stats": app_status.get("stats", {})
        }

        if db_status:
            status["stats"].update({
                "total_requests": db_status.total_requests,
                "success_count": db_status.success_count,
                "failure_count": db_status.failure_count,
                "success_rate": db_status.success_rate
            })

        return status

    async def _update_running_status(self, running: bool) -> None:
        """更新运行状态到数据库"""
        try:
            status = await self._status_repo.get_status(self.market, self.mode)
            if not status:
                status = PoolStatus(
                    market=self.market,
                    mode=self.mode,
                    is_running=running,
                    started_at=datetime.now() if running else None,
                    stopped_at=None if running else datetime.now()
                )
            else:
                status.is_running = running
                if running:
                    status.started_at = datetime.now()
                    status.stopped_at = None
                else:
                    status.stopped_at = datetime.now()

            await self._status_repo.save_status(status)
        except Exception as e:
            self.logger.error(f"Failed to update running status: {e}")

    async def _trading_scheduler(self) -> None:
        """交易日调度器"""
        try:
            config = await self._load_config()

            while self._running:
                # 检查是否应该开始交易时段
                should_start = self._market_clock.should_start_trading_session(
                    self.market, config.pre_market_start_minutes
                )

                # 检查是否应该停止交易时段
                should_stop = self._market_clock.should_stop_trading_session(
                    self.market, config.post_market_stop_minutes
                )

                if should_stop:
                    self.logger.info(f"Trading session ended for {self.market}, stopping service")
                    await self.stop()
                    break

                if should_start and not self._monitor_task:
                    # 启动监控任务
                    self._monitor_task = asyncio.create_task(self._monitor_loop())

                await asyncio.sleep(60)  # 每分钟检查一次

        except asyncio.CancelledError:
            self.logger.info("Trading scheduler cancelled")
        except Exception as e:
            self.logger.error(f"Error in trading scheduler: {e}")

    async def _monitor_loop(self) -> None:
        """监控循环 - 检查市场时间并自动关闭"""
        try:
            config = await self._load_config()

            while self._running:
                should_continue = await self._application_service.should_continue_running()
                if not should_continue:
                    self.logger.info(f"Market {self.market} closed, initiating shutdown")
                    await asyncio.sleep(config.post_market_stop_minutes * 60)
                    await self.stop()
                    break

                await asyncio.sleep(60)  # 每分钟检查一次
        except asyncio.CancelledError:
            self.logger.info("Monitor loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in monitor loop: {e}")

    async def update_config(self, **kwargs) -> bool:
        """更新配置"""
        try:
            config = await self._load_config()

            # 更新配置字段
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # 保存到数据库
            success = await self._config_repo.update_config(config)

            if success:
                # 失效缓存
                await self._invalidate_config_cache()

                # 如果正在运行，重新初始化组件
                if self._running:
                    await self.stop()
                    await self.start()

                self.logger.info(f"Updated config for {self.market}/{self.mode.value}")

            return success
        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False

    async def get_config_dict(self) -> dict:
        """获取配置字典"""
        config = await self._load_config()
        return {
            "id": config.id,
            "market": config.market,
            "mode": config.mode.value,
            "hailiang_api_url": config.hailiang_api_url,
            "hailiang_enabled": config.hailiang_enabled,
            "batch_size": config.batch_size,
            "proxy_lifetime_minutes": config.proxy_lifetime_minutes,
            "rotation_interval_minutes": config.rotation_interval_minutes,
            "low_watermark": config.low_watermark,
            "target_size": config.target_size,
            "auto_start_enabled": config.auto_start_enabled,
            "pre_market_start_minutes": config.pre_market_start_minutes,
            "post_market_stop_minutes": config.post_market_stop_minutes,
            "backfill_enabled": config.backfill_enabled,
            "backfill_duration_hours": config.backfill_duration_hours,
            "is_active": config.is_active
        }