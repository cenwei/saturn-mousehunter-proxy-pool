"""
Application层 - 代理池应用服务
"""

from __future__ import annotations

from saturn_mousehunter_shared import get_logger, cache_with_ttl, cache_invalidate
from domain.services import ProxyPoolDomainService


class ProxyPoolApplicationService:
    """代理池应用服务"""

    def __init__(self, domain_service: ProxyPoolDomainService):
        self.domain_service = domain_service
        self.logger = get_logger("proxy_pool_application")

    async def get_proxy(self, proxy_type: str = "short") -> str | None:
        """获取代理地址"""
        return await self.domain_service.get_proxy(proxy_type)

    async def report_failure(self, proxy_addr: str) -> None:
        """报告代理失败"""
        # 清除相关缓存
        await self._invalidate_status_cache()
        await self.domain_service.report_failure(proxy_addr)

    @cache_with_ttl(30)
    async def get_status(self) -> dict:
        """获取服务状态（带缓存）"""
        return await self.domain_service.get_status()

    @cache_invalidate("proxy_pool_status_*")
    async def _invalidate_status_cache(self) -> None:
        """清除状态缓存"""
        pass

    async def start_service(self, force: bool = False) -> None:
        """启动服务

        Args:
            force: 是否强制启动，忽略市场时间检查
        """
        await self.domain_service.start_service(force=force)
        await self._invalidate_status_cache()

    async def stop_service(self) -> None:
        """停止服务"""
        await self.domain_service.stop_service()
        await self._invalidate_status_cache()

    async def should_continue_running(self) -> bool:
        """判断是否应该继续运行"""
        return await self.domain_service.should_continue_running()
