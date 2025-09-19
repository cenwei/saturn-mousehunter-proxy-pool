"""
Domain层 - 代理池业务服务
"""

from __future__ import annotations

from saturn_mousehunter_shared import get_logger, measure, retry
from .entities import IProxyRepository, IMarketClock, MarketType, ProxyMode


class ProxyPoolDomainService:
    """代理池领域服务"""

    def __init__(
        self,
        proxy_repository: IProxyRepository,
        market_clock: IMarketClock,
        market: MarketType,
        mode: ProxyMode,
    ):
        self.proxy_repository = proxy_repository
        self.market_clock = market_clock
        self.market = market
        self.mode = mode
        self.logger = get_logger(f"proxy_pool_domain.{market.value}.{mode.value}")

    @measure("proxy_get_duration", ("market", "mode"))
    @retry(times=3, delay=0.1)
    async def get_proxy(self, proxy_type: str = "short") -> str | None:
        """获取代理地址"""
        self.logger.debug(f"Requesting proxy of type: {proxy_type}")

        proxy = await self.proxy_repository.get_proxy_from_pool(proxy_type)
        if proxy:
            self.logger.debug(f"Retrieved proxy: {proxy.addr}")
            return proxy.addr

        self.logger.warning("No proxy available")
        return None

    @measure("proxy_failure_report_duration", ("market", "mode"))
    async def report_failure(self, proxy_addr: str) -> None:
        """报告代理失败"""
        self.logger.info(f"Reporting failure for proxy: {proxy_addr}")
        await self.proxy_repository.mark_failure(proxy_addr)

    async def get_status(self) -> dict:
        """获取服务状态"""
        stats = await self.proxy_repository.get_stats()
        market_status = self.market_clock.get_market_status_desc(self.market.value)

        return {
            "market": self.market.value,
            "mode": self.mode.value,
            "market_status": market_status,
            "stats": stats.__dict__ if stats else {},
        }

    async def should_continue_running(self) -> bool:
        """判断是否应该继续运行"""
        if self.mode != ProxyMode.LIVE:
            return True

        return not self.market_clock.should_terminate_after_close(self.market.value)

    async def start_service(self, force: bool = False) -> None:
        """启动服务

        Args:
            force: 是否强制启动，忽略市场时间检查
                - True: 人工启动，忽略市场时间限制
                - False: 自动启动，受市场时间限制（默认）
        """
        if self.mode == ProxyMode.LIVE and not force:
            # 只有自动启动时才检查市场时间限制
            # 人工启动（force=True）允许在市场关闭后启动
            if self.market_clock.should_terminate_after_close(self.market.value):
                raise RuntimeError(
                    f"Market {self.market.value} closed past termination time"
                )

        self.logger.info(
            f"Starting proxy pool service for {self.market.value} in {self.mode.value} mode"
            + (" (forced)" if force else "")
        )
        await self.proxy_repository.start_maintenance()

    async def stop_service(self) -> None:
        """停止服务"""
        self.logger.info("Stopping proxy pool service")
        await self.proxy_repository.stop_maintenance()
