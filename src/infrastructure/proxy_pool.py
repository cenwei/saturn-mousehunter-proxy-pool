"""
Infrastructure层 - 代理池管理器
"""

from __future__ import annotations

import asyncio
from typing import Optional

from saturn_mousehunter_shared import get_logger
from domain import (
    MarketType, ProxyMode, ProxyPoolDomainService
)
from application import ProxyPoolApplicationService
from .config import ProxyPoolConfig
from .market_clock import MarketClockService
from .proxy_fetchers import MockProxyFetcher, ExternalProxyFetcher, HailiangProxyFetcher
from .memory_proxy_repository import MemoryProxyRepository


class ProxyPoolManager:
    """代理池管理器 - 负责依赖注入和生命周期管理"""

    def __init__(self, config: ProxyPoolConfig):
        self.config = config
        self.logger = get_logger("proxy_pool_manager")

        # 创建依赖
        self._market_clock = MarketClockService()

        # 选择代理获取器
        if config.hailiang_enabled and config.hailiang_api_url:
            self._fetcher = HailiangProxyFetcher(config.hailiang_api_url, config.market)
            self.logger.info("Using Hailiang proxy fetcher")
        else:
            self._fetcher = MockProxyFetcher(config.market)
            self.logger.info("Using mock proxy fetcher")
        self._repository = MemoryProxyRepository(
            market=MarketType(config.market),
            mode=ProxyMode(config.mode),
            fetcher=self._fetcher,
            rotate_interval_sec=config.rotate_interval_sec,
            low_watermark=config.low_watermark,
            target_size=config.target_size,
            min_refresh_secs=config.min_refresh_secs,
            batch_count=config.batch_count
        )

        # 创建服务层
        self._domain_service = ProxyPoolDomainService(
            proxy_repository=self._repository,
            market_clock=self._market_clock,
            market=MarketType(config.market),
            mode=ProxyMode(config.mode)
        )

        self._application_service = ProxyPoolApplicationService(
            domain_service=self._domain_service
        )

        # 状态
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        """检查服务是否运行中"""
        return self._running

    def set_external_fetcher(self, fetch_func) -> None:
        """设置外部代理获取函数"""
        self._fetcher = ExternalProxyFetcher(fetch_func, self.config.market)

        # 重新创建仓储以使用新的获取器
        self._repository = MemoryProxyRepository(
            market=MarketType(self.config.market),
            mode=ProxyMode(self.config.mode),
            fetcher=self._fetcher,
            rotate_interval_sec=self.config.rotate_interval_sec,
            low_watermark=self.config.low_watermark,
            target_size=self.config.target_size,
            min_refresh_secs=self.config.min_refresh_secs,
            batch_count=self.config.batch_count
        )

        # 重新创建领域服务
        self._domain_service = ProxyPoolDomainService(
            proxy_repository=self._repository,
            market_clock=self._market_clock,
            market=MarketType(self.config.market),
            mode=ProxyMode(self.config.mode)
        )

        # 重新创建应用服务
        self._application_service = ProxyPoolApplicationService(
            domain_service=self._domain_service
        )

        self.logger.info("External proxy fetcher configured")

    async def start(self) -> None:
        """启动代理池服务"""
        if self._running:
            self.logger.warning("Service already running")
            return

        self.logger.info("Starting proxy pool manager")

        await self._application_service.start_service()
        self._running = True

        # 启动监控任务（仅在live模式）
        if self.config.mode == "live":
            self._monitor_task = asyncio.create_task(self._monitor_loop())

        self.logger.info("Proxy pool manager started successfully")

    async def stop(self) -> None:
        """停止代理池服务"""
        if not self._running:
            self.logger.warning("Service not running")
            return

        self.logger.info("Stopping proxy pool manager")

        self._running = False

        # 取消监控任务
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        await self._application_service.stop_service()
        self.logger.info("Proxy pool manager stopped")

    async def get_proxy(self, proxy_type: str = "short") -> str | None:
        """获取代理地址"""
        if not self._running:
            return None
        return await self._application_service.get_proxy(proxy_type)

    async def report_failure(self, proxy_addr: str) -> None:
        """报告代理失败"""
        if not self._running:
            return
        await self._application_service.report_failure(proxy_addr)

    async def get_status(self) -> dict:
        """获取服务状态"""
        if not self._running:
            return {
                "running": False,
                "market": self.config.market,
                "mode": self.config.mode,
                "error": "Service not running"
            }

        status = await self._application_service.get_status()
        status["running"] = self._running
        return status

    async def _monitor_loop(self) -> None:
        """监控循环 - 检查市场时间并自动关闭"""
        try:
            while self._running:
                should_continue = await self._application_service.should_continue_running()
                if not should_continue:
                    self.logger.info(f"Market {self.config.market} closed, initiating shutdown")
                    await asyncio.sleep(self.config.termination_grace_sec)
                    await self.stop()
                    break

                await asyncio.sleep(self.config.check_interval_sec)
        except asyncio.CancelledError:
            self.logger.info("Monitor loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in monitor loop: {e}")

    async def update_hailiang_config(self, api_url: str, enabled: bool) -> bool:
        """更新海量代理配置"""
        try:
            # 更新配置
            self.config.hailiang_api_url = api_url
            self.config.hailiang_enabled = enabled

            # 重新创建获取器
            if enabled and api_url:
                self._fetcher = HailiangProxyFetcher(api_url, self.config.market)
                self.logger.info(f"Updated to Hailiang proxy fetcher: {api_url}")
            else:
                self._fetcher = MockProxyFetcher(self.config.market)
                self.logger.info("Updated to mock proxy fetcher")

            # 重新创建仓储
            await self._recreate_repository()

            self.logger.info("Hailiang proxy configuration updated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update Hailiang config: {e}")
            return False

    async def get_hailiang_config(self) -> dict:
        """获取海量代理配置"""
        return {
            "api_url": self.config.hailiang_api_url,
            "enabled": self.config.hailiang_enabled,
            "current_fetcher": "hailiang" if self.config.hailiang_enabled else "mock"
        }

    async def _recreate_repository(self) -> None:
        """重新创建仓储以使用新的获取器"""
        was_running = self._running

        # 如果正在运行，先停止
        if was_running:
            await self.stop()

        # 重新创建仓储
        self._repository = MemoryProxyRepository(
            market=MarketType(self.config.market),
            mode=ProxyMode(self.config.mode),
            fetcher=self._fetcher,
            rotate_interval_sec=self.config.rotate_interval_sec,
            low_watermark=self.config.low_watermark,
            target_size=self.config.target_size,
            min_refresh_secs=self.config.min_refresh_secs,
            batch_count=self.config.batch_count
        )

        # 重新创建服务层
        self._domain_service = ProxyPoolDomainService(
            proxy_repository=self._repository,
            market_clock=self._market_clock,
            market=MarketType(self.config.market),
            mode=ProxyMode(self.config.mode)
        )

        self._application_service = ProxyPoolApplicationService(
            domain_service=self._domain_service
        )

        # 如果之前在运行，重新启动
        if was_running:
            await self.start()