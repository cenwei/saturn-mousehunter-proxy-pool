"""
Infrastructure层 - 内存代理池仓储实现
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime
from typing import Dict, List, Optional

from saturn_mousehunter_shared import get_logger, measure
from domain import (
    IProxyRepository,
    IProxyFetcher,
    Proxy,
    ProxyPoolStats,
    ProxyStatus,
    MarketType,
    ProxyMode,
)
from .proxy_health_checker import ProxyHealthChecker


class MemoryProxyRepository(IProxyRepository):
    """
    内存A/B轮换代理池仓储实现
    - 维护两个池：A池（活跃）和B池（备用）
    - 定期刷新备用池，然后切换
    - 支持失败代理移除
    """

    def __init__(
        self,
        market: MarketType,
        mode: ProxyMode,
        fetcher: IProxyFetcher,
        rotate_interval_sec: int = 180,
        low_watermark: int = 5,
        target_size: int = 20,
        min_refresh_secs: int = 420,
        batch_count: int = 2,
        enable_health_check: bool = True,
        health_check_interval: int = 300,  # 5分钟检查一次
    ):
        self.market = market
        self.mode = mode
        self.fetcher = fetcher
        self.active_pool = "A"
        self.pools: Dict[str, List[Proxy]] = {"A": [], "B": []}

        # 配置
        self.rotate_interval_sec = rotate_interval_sec
        self.low_watermark = low_watermark
        self.target_size = target_size
        self.min_refresh_secs = min_refresh_secs
        self.batch_count = batch_count
        self.enable_health_check = enable_health_check
        self.health_check_interval = health_check_interval

        # 状态
        self._lock = asyncio.Lock()
        self._last_rotate_ts = time.time()
        self._start_time = time.time()
        self._maintain_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # 统计
        self._total_requests = 0
        self._success_count = 0
        self._failure_count = 0
        self._last_fetch_time: Optional[float] = None
        self._last_fetch_count = 0

        # 健康检查器
        self.health_checker = ProxyHealthChecker(market.value) if enable_health_check else None

        # 日志
        self.logger = get_logger(f"memory_proxy_repo.{market.value}.{mode.value}")

    @property
    def standby_pool(self) -> str:
        """获取备用池标识"""
        return "B" if self.active_pool == "A" else "A"

    @measure("proxy_repository_get_duration", ("market", "mode"))
    async def get_proxy_from_pool(self, proxy_type: str = "short") -> Optional[Proxy]:
        """从池中获取代理"""
        async with self._lock:
            self._total_requests += 1

            # 优先从活跃池获取
            active_proxies = [p for p in self.pools[self.active_pool] if p.is_healthy()]
            if active_proxies:
                proxy = random.choice(active_proxies)
                proxy.mark_used()
                self._success_count += 1
                return proxy

            # 活跃池为空，尝试备用池
            standby_proxies = [
                p for p in self.pools[self.standby_pool] if p.is_healthy()
            ]
            if standby_proxies:
                proxy = random.choice(standby_proxies)
                proxy.mark_used()
                self._success_count += 1
                return proxy

            # 两个池都为空
            self.logger.warning("Both pools are empty or unhealthy")
            return None

    async def mark_failure(self, proxy_addr: str) -> None:
        """标记代理失败并移除"""
        async with self._lock:
            self._failure_count += 1

            for pool_name in ("A", "B"):
                for proxy in self.pools[pool_name]:
                    if proxy.addr == proxy_addr:
                        proxy.mark_failure()
                        self.logger.debug(f"Marked proxy {proxy_addr} as failed")

                # 移除失败的代理
                self.pools[pool_name] = [
                    p for p in self.pools[pool_name] if p.addr != proxy_addr
                ]

    async def get_stats(self) -> ProxyPoolStats:
        """获取代理池统计信息"""
        async with self._lock:
            active_size = len(self.pools[self.active_pool])
            standby_size = len(self.pools[self.standby_pool])
            uptime_seconds = int(time.time() - self._start_time)

            return ProxyPoolStats(
                market=self.market.value,
                mode=self.mode.value,
                pool_type="memory_ab",
                active_pool=self.active_pool,
                standby_pool=self.standby_pool,
                active_pool_size=active_size,
                standby_pool_size=standby_size,
                total_pool_size=active_size + standby_size,
                last_switch_time=datetime.fromtimestamp(self._last_rotate_ts).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                switch_ago_seconds=int(time.time() - self._last_rotate_ts),
                uptime_seconds=uptime_seconds,
                uptime_hours=round(uptime_seconds / 3600, 2),
                total_requests=self._total_requests,
                success_count=self._success_count,
                failure_count=self._failure_count,
                success_rate=round(
                    self._success_count / max(self._total_requests, 1) * 100, 2
                ),
                last_fetch_time=(
                    datetime.fromtimestamp(self._last_fetch_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if self._last_fetch_time
                    else "未记录"
                ),
                last_fetch_count=self._last_fetch_count,
                status=self._get_health_status(active_size),
            )

    def _get_health_status(self, active_size: int) -> str:
        """获取健康状态"""
        if active_size >= self.low_watermark:
            return "healthy"
        elif active_size > 0:
            return "warning"
        else:
            return "critical"

    async def start_maintenance(self) -> None:
        """启动维护任务"""
        if self._maintain_task and not self._maintain_task.done():
            self.logger.warning("Maintenance task already running")
            return

        self.logger.info(f"Starting proxy pool maintenance for {self.market.value}")
        self._maintain_task = asyncio.create_task(self._maintenance_loop())

        # 启动健康检查任务
        if self.health_checker and self.enable_health_check:
            if self._health_check_task and not self._health_check_task.done():
                self.logger.warning("Health check task already running")
            else:
                self.logger.info("Starting proxy health check task")
                self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def stop_maintenance(self) -> None:
        """停止维护任务"""
        if self._maintain_task and not self._maintain_task.done():
            self._maintain_task.cancel()
            try:
                await self._maintain_task
            except asyncio.CancelledError:
                pass

        # 停止健康检查任务
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Proxy pool maintenance stopped")

    async def _maintenance_loop(self) -> None:
        """维护循环"""
        while True:
            try:
                # 刷新备用池
                await self._refresh_standby_pool()

                # 切换池
                await self._switch_pools()

                # 等待下次刷新
                await asyncio.sleep(self.min_refresh_secs)

            except asyncio.CancelledError:
                self.logger.info("Proxy pool maintenance cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in proxy pool maintenance: {e}")
                await asyncio.sleep(30)  # 错误后短暂等待

    async def _refresh_standby_pool(self) -> None:
        """刷新备用池"""
        async with self._lock:
            # 清空备用池
            standby = self.standby_pool
            self.pools[standby] = []

        # 获取新代理
        new_proxies: List[str] = []

        for batch_idx in range(self.batch_count):
            try:
                batch = await self.fetcher.fetch_proxies(self.target_size)
                if batch:
                    new_proxies.extend(batch)
                    self.logger.debug(
                        f"Fetched {len(batch)} proxies in batch {batch_idx + 1}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch proxies in batch {batch_idx + 1}: {e}"
                )

            # 批次间间隔
            if batch_idx < self.batch_count - 1:
                await asyncio.sleep(1)

        # 更新备用池
        async with self._lock:
            # 限制数量并创建代理对象
            proxies_to_add = new_proxies[: self.target_size]
            now = datetime.now()
            self.pools[standby] = [
                Proxy(addr=addr, status=ProxyStatus.ACTIVE, created_at=now)
                for addr in proxies_to_add
            ]

            # 更新统计
            self._last_fetch_time = time.time()
            self._last_fetch_count = len(proxies_to_add)

        self.logger.info(f"Refreshed standby pool with {len(proxies_to_add)} proxies")

        # 如果启用健康检查，立即检查新代理的健康状态
        if self.health_checker and self.enable_health_check and proxies_to_add:
            try:
                await self.health_checker.check_proxies_batch(self.pools[standby], max_concurrent=5)
                self.logger.info(f"Health check completed for {len(proxies_to_add)} new proxies")
            except Exception as e:
                self.logger.error(f"Failed to perform health check on new proxies: {e}")

    async def _switch_pools(self) -> None:
        """切换活跃池和备用池"""
        async with self._lock:
            old_active = self.active_pool
            self.active_pool = self.standby_pool
            self._last_rotate_ts = time.time()

            # 清空旧的活跃池（现在变成备用池）
            self.pools[old_active] = []

        self.logger.info(f"Switched active pool to {self.active_pool}")

    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while True:
            try:
                # 获取当前所有代理
                all_proxies = []
                async with self._lock:
                    for pool_name in ("A", "B"):
                        all_proxies.extend(self.pools[pool_name])

                if all_proxies and self.health_checker:
                    self.logger.debug(f"Starting health check for {len(all_proxies)} proxies")

                    # 执行健康检查
                    await self.health_checker.check_proxies_batch(all_proxies, max_concurrent=8)

                    # 移除不健康的代理
                    await self._remove_unhealthy_proxies()

                    # 记录健康状态摘要
                    health_summary = self.health_checker.get_health_summary()
                    self.logger.info(
                        f"Health check completed: {health_summary['healthy_proxies']}/{health_summary['total_proxies']} "
                        f"healthy ({health_summary['health_rate']:.1f}%), "
                        f"avg response time: {health_summary['avg_response_time']}ms"
                    )

                # 等待下次检查
                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                self.logger.info("Proxy health check cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in proxy health check: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟

    async def _remove_unhealthy_proxies(self) -> None:
        """移除不健康的代理"""
        if not self.health_checker:
            return

        removed_count = 0
        async with self._lock:
            for pool_name in ("A", "B"):
                original_count = len(self.pools[pool_name])

                # 过滤掉不健康的代理
                healthy_proxies = []
                for proxy in self.pools[pool_name]:
                    stats = self.health_checker.get_proxy_stats(proxy.addr)
                    if stats and stats.is_healthy:
                        healthy_proxies.append(proxy)
                    elif not stats:
                        # 没有统计信息的代理保留（可能是刚添加的）
                        healthy_proxies.append(proxy)
                    else:
                        # 不健康的代理被移除
                        removed_count += 1

                self.pools[pool_name] = healthy_proxies

                if len(self.pools[pool_name]) < original_count:
                    self.logger.info(
                        f"Removed {original_count - len(self.pools[pool_name])} unhealthy proxies from pool {pool_name}"
                    )

        if removed_count > 0:
            self.logger.info(f"Total unhealthy proxies removed: {removed_count}")

    def get_health_summary(self) -> Optional[Dict]:
        """获取健康检查摘要"""
        if self.health_checker:
            return self.health_checker.get_health_summary()
        return None
