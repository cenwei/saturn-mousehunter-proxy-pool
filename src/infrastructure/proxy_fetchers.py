"""
Infrastructure层 - 代理获取器实现
"""

from __future__ import annotations

import asyncio
import random
from typing import List, Optional

import httpx
from saturn_mousehunter_shared import get_logger, retry
from domain.entities import IProxyFetcher


class MockProxyFetcher(IProxyFetcher):
    """模拟代理获取器，用于测试和开发"""

    def __init__(self, market: str = "hk"):
        self.market = market.lower()
        self.logger = get_logger(f"mock_proxy_fetcher.{market}")

    @retry(times=3, delay=0.1)
    async def fetch_proxies(self, count: int = 20) -> List[str]:
        """生成模拟代理地址"""
        # 基于市场生成不同的IP段
        base_ip_map = {
            "cn": "http://cn-proxy",
            "hk": "http://hk-proxy",
            "us": "http://us-proxy",
            "sg": "http://sg-proxy",
            "jp": "http://jp-proxy",
            "kr": "http://kr-proxy",
            "uk": "http://uk-proxy",
            "eu": "http://eu-proxy",
        }

        base = base_ip_map.get(self.market, "http://proxy")
        proxies = []

        for _ in range(count):
            ip_suffix = random.randint(1, 254)
            port = random.randint(9000, 9999)
            proxy_addr = f"{base}-{ip_suffix}.example.com:{port}"
            proxies.append(proxy_addr)

        # 模拟网络延迟
        await asyncio.sleep(0.1)
        self.logger.debug(f"Generated {len(proxies)} mock proxies")
        return proxies


class HailiangProxyFetcher(IProxyFetcher):
    """海量代理IP获取器"""

    def __init__(self, api_url: str, market: str = "HK"):
        self.api_url = api_url
        self.market = market
        self.logger = get_logger(f"hailiang_proxy_fetcher.{market}")

    async def fetch_proxies(self, count: int = 20) -> List[str]:
        """获取海量代理IP"""
        return await fetch_hailiang_proxy_ip(self.api_url, self.logger)


class ExternalProxyFetcher(IProxyFetcher):
    """外部代理获取器包装器"""

    def __init__(self, fetch_func=None, market: str = "hk"):
        self.fetch_func = fetch_func
        self.market = market
        self.logger = get_logger(f"external_proxy_fetcher.{market}")
        self._fallback = MockProxyFetcher(market)

    @retry(times=2, delay=0.5)
    async def fetch_proxies(self, count: int = 20) -> List[str]:
        """调用外部代理获取函数"""
        if not self.fetch_func:
            self.logger.warning("No external fetch function configured, using fallback")
            return await self._fallback.fetch_proxies(count)

        try:
            # 调用外部代理获取函数
            if asyncio.iscoroutinefunction(self.fetch_func):
                result = await self.fetch_func()
            else:
                result = self.fetch_func()

            if isinstance(result, list):
                proxies = result[:count]
                self.logger.info(f"Fetched {len(proxies)} proxies from external source")
                return proxies
            elif isinstance(result, str):
                if result == "LIMIT_TOO_MANY_UNUSED":
                    self.logger.warning("External API rate limited")
                    return []
                self.logger.info("Fetched 1 proxy from external source")
                return [result]
            else:
                self.logger.warning(
                    "External fetch returned invalid data, using fallback"
                )
                return await self._fallback.fetch_proxies(count)

        except Exception as e:
            self.logger.error(f"External proxy fetch failed: {e}, using fallback")
            return await self._fallback.fetch_proxies(count)


async def fetch_hailiang_proxy_ip(url: str, logger: Optional = None) -> List[str]:
    """
    获取海量代理IP的静态函数

    Args:
        url: 海量代理API URL
        logger: 日志记录器，如果为None则创建默认的

    Returns:
        代理IP列表，格式为 ["ip:port", ...]
        如果遇到限流返回空列表
    """
    if logger is None:
        logger = get_logger("hailiang_proxy_ip")

    # 清理URL，移除可能的换行符和空白字符
    clean_url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '')

    if not clean_url:
        logger.error("URL为空")
        return []

    # 诊断URL内容，检查是否包含不可见字符
    if len(url) != len(clean_url):
        logger.warning(f"URL包含不可见字符，原长度: {len(url)}, 清理后长度: {len(clean_url)}")
        logger.warning(f"原始URL repr: {repr(url)}")
        logger.warning(f"清理后URL: {clean_url[:100]}...")

    logger.debug(f"请求海量代理API: {clean_url[:100]}...")  # 只显示URL前100个字符

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(clean_url)

            if response.status_code == 200:
                try:
                    content_type = response.headers.get("Content-Type", "")
                    if (
                        "application/json" in content_type
                        or response.text.strip().startswith("{")
                    ):
                        data = response.json()
                    else:
                        if "未使用的IP太多" in response.text:
                            logger.warning("海量代理API风控限流，主维护池需要休眠！")
                            return []
                        logger.error(
                            f"海量代理API返回非JSON内容: {response.text[:200]}"
                        )
                        return []
                except Exception as e:
                    if "未使用的IP太多" in response.text:
                        logger.warning("海量代理API风控限流，主维护池需要休眠！")
                        return []
                    logger.error(f"JSON解析失败: {e}, 原始内容: {response.text[:300]}")
                    return []

                if data.get("code") == 0 and isinstance(data.get("data"), list):
                    proxies = [
                        f"{item['ip']}:{item['port']}"
                        for item in data["data"]
                        if "ip" in item and "port" in item
                    ]
                    logger.info(f"成功获取海量代理 {len(proxies)} 个")
                    return proxies
                else:
                    # 使用 repr() 来安全地记录包含特殊字符的数据
                    logger.warning("海量代理API返回异常内容", response_data=data)
            else:
                # 增强重定向和状态码处理
                logger.warning(
                    f"fetch_hailiang_proxy_ip 状态码异常: {response.status_code}, URL: {response.url}"
                )
                if hasattr(response, 'history') and response.history:
                    logger.info(f"发生了 {len(response.history)} 次重定向")
                    for i, resp in enumerate(response.history):
                        logger.info(f"重定向 {i+1}: {resp.status_code} -> {resp.headers.get('location', 'N/A')}")

                # 对于302等重定向状态码，尝试输出响应内容以便调试
                if response.status_code in [301, 302, 303, 307, 308]:
                    logger.debug(f"重定向响应内容: {response.text[:200]}")
                elif response.text:
                    logger.debug(f"响应内容: {response.text[:200]}")

    except httpx.RequestError as e:
        logger.error(f"请求海量代理API异常: {e}")
    except Exception as e:
        logger.error(f"未知异常: {e}")

    return []
