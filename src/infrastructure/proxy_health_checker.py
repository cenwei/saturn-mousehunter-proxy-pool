"""
Infrastructure层 - 代理健康检查服务
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import httpx
from saturn_mousehunter_shared import get_logger, measure, retry
from domain.entities import Proxy, ProxyStatus


@dataclass
class ProxyHealthStats:
    """代理健康检查统计"""

    proxy_addr: str
    is_healthy: bool
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    last_check_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_checks: int = 0
    success_rate: float = 0.0


class ProxyHealthChecker:
    """代理健康检查器"""

    # 可靠的测试端点列表 - 返回简单响应的网站
    TEST_ENDPOINTS = [
        "http://httpbin.org/ip",  # 返回JSON格式的IP信息
        "http://icanhazip.com",   # 返回纯文本IP
        "http://ipinfo.io/ip",    # 返回纯文本IP
        "http://api.ipify.org",   # 返回纯文本IP
    ]

    def __init__(self, market: str = "HK"):
        self.market = market.lower()
        self.logger = get_logger(f"proxy_health_checker.{market}")

        # 健康检查配置
        self.check_timeout = 10.0  # 检查超时时间
        self.max_retries = 2       # 最大重试次数
        self.failure_threshold = 3  # 连续失败阈值
        self.success_threshold = 2  # 连续成功阈值

        # 统计数据
        self.health_stats: Dict[str, ProxyHealthStats] = {}
        self._check_count = 0
        self._last_check_time: Optional[datetime] = None

    @measure("proxy_health_check_duration", ("market",))
    @retry(times=2, delay=0.5)
    async def check_proxy_health(self, proxy: Proxy) -> ProxyHealthStats:
        """检查单个代理的健康状态"""
        start_time = time.time()
        stats = self.health_stats.get(proxy.addr)

        if not stats:
            stats = ProxyHealthStats(
                proxy_addr=proxy.addr,
                is_healthy=False
            )
            self.health_stats[proxy.addr] = stats

        # 选择测试端点
        test_url = self.TEST_ENDPOINTS[0]  # 默认使用httpbin

        try:
            # 配置代理
            proxy_config = {
                "http://": f"http://{proxy.addr}",
                "https://": f"http://{proxy.addr}",
            }

            async with httpx.AsyncClient(
                proxies=proxy_config,
                timeout=self.check_timeout,
                follow_redirects=True
            ) as client:

                response = await client.get(test_url)
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒

                # 判断响应是否成功
                is_success = 200 <= response.status_code < 300

                # 更新统计信息
                stats.response_time_ms = response_time
                stats.status_code = response.status_code
                stats.error_message = None
                stats.last_check_time = datetime.now()
                stats.total_checks += 1

                if is_success:
                    stats.consecutive_successes += 1
                    stats.consecutive_failures = 0
                    stats.is_healthy = True

                    # 更新代理状态
                    if proxy.status != ProxyStatus.ACTIVE:
                        proxy.status = ProxyStatus.ACTIVE
                        self.logger.info(f"Proxy {proxy.addr} recovered - response time: {response_time:.1f}ms")
                else:
                    stats.consecutive_failures += 1
                    stats.consecutive_successes = 0
                    stats.error_message = f"HTTP {response.status_code}"

                    # 连续失败超过阈值则标记为不健康
                    if stats.consecutive_failures >= self.failure_threshold:
                        stats.is_healthy = False
                        proxy.mark_failure()
                        self.logger.warning(f"Proxy {proxy.addr} marked as unhealthy - {stats.consecutive_failures} consecutive failures")

                # 计算成功率
                stats.success_rate = (stats.total_checks - stats.consecutive_failures) / stats.total_checks * 100

                self.logger.debug(
                    f"Health check for {proxy.addr}: "
                    f"status={response.status_code}, "
                    f"time={response_time:.1f}ms, "
                    f"healthy={stats.is_healthy}"
                )

        except Exception as e:
            # 处理检查异常
            response_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            stats.response_time_ms = response_time
            stats.status_code = None
            stats.error_message = error_msg
            stats.last_check_time = datetime.now()
            stats.total_checks += 1
            stats.consecutive_failures += 1
            stats.consecutive_successes = 0

            # 连续失败超过阈值则标记为不健康
            if stats.consecutive_failures >= self.failure_threshold:
                stats.is_healthy = False
                proxy.mark_failure()
                self.logger.warning(f"Proxy {proxy.addr} failed health check: {error_msg}")

            # 计算成功率
            if stats.total_checks > 0:
                success_count = stats.total_checks - stats.consecutive_failures
                stats.success_rate = success_count / stats.total_checks * 100

        return stats

    async def check_proxies_batch(self, proxies: List[Proxy], max_concurrent: int = 10) -> Dict[str, ProxyHealthStats]:
        """批量检查代理健康状态"""
        if not proxies:
            return {}

        self.logger.info(f"Starting health check for {len(proxies)} proxies")
        self._check_count += 1
        self._last_check_time = datetime.now()

        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_with_semaphore(proxy: Proxy) -> Tuple[str, ProxyHealthStats]:
            async with semaphore:
                stats = await self.check_proxy_health(proxy)
                return proxy.addr, stats

        # 并发执行健康检查
        tasks = [check_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        checked_stats = {}
        healthy_count = 0

        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Health check task failed: {result}")
                continue

            proxy_addr, stats = result
            checked_stats[proxy_addr] = stats
            if stats.is_healthy:
                healthy_count += 1

        self.logger.info(
            f"Health check completed: {healthy_count}/{len(proxies)} proxies healthy "
            f"({healthy_count/len(proxies)*100:.1f}%)"
        )

        return checked_stats

    def get_health_summary(self) -> Dict:
        """获取健康检查摘要"""
        if not self.health_stats:
            return {
                "total_proxies": 0,
                "healthy_proxies": 0,
                "unhealthy_proxies": 0,
                "health_rate": 0.0,
                "last_check_time": None,
                "total_checks": self._check_count,
                "avg_response_time": 0.0
            }

        healthy_count = sum(1 for stats in self.health_stats.values() if stats.is_healthy)
        total_count = len(self.health_stats)

        # 计算平均响应时间（只统计成功的请求）
        response_times = [
            stats.response_time_ms
            for stats in self.health_stats.values()
            if stats.response_time_ms is not None and stats.is_healthy
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        return {
            "total_proxies": total_count,
            "healthy_proxies": healthy_count,
            "unhealthy_proxies": total_count - healthy_count,
            "health_rate": healthy_count / total_count * 100 if total_count > 0 else 0.0,
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "total_checks": self._check_count,
            "avg_response_time": round(avg_response_time, 1)
        }

    def get_proxy_stats(self, proxy_addr: str) -> Optional[ProxyHealthStats]:
        """获取指定代理的统计信息"""
        return self.health_stats.get(proxy_addr)

    def clear_stats(self) -> None:
        """清除统计数据"""
        self.health_stats.clear()
        self._check_count = 0
        self._last_check_time = None
        self.logger.info("Health check statistics cleared")