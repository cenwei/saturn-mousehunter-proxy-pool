"""
代理池服务测试脚本
"""

import asyncio
import httpx
import json
import sys
import os
from typing import Dict, Any

# 添加shared模块路径
sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

from saturn_mousehunter_shared.config.service_endpoints import (
    get_service_url,
    ApiEndpoints,
    ServiceEndpointConfig
)


class ProxyPoolTester:
    """代理池服务测试器"""

    def __init__(self, environment: str = "development"):
        """初始化测试器"""
        self.config = ServiceEndpointConfig(environment)
        self.base_url = self.config.get_service_url("proxy-pool-service")
        self.client = httpx.AsyncClient(timeout=30.0)
        print(f"🔗 测试环境: {environment}")
        print(f"🔗 服务地址: {self.base_url}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def get_endpoint_url(self, endpoint: str) -> str:
        """获取端点完整URL"""
        return self.config.get_service_url("proxy-pool-service", endpoint)

    async def test_health_check(self) -> Dict[str, Any]:
        """测试健康检查"""
        print("\n🔍 测试健康检查...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            result = response.json()
            print(f"✅ 健康检查成功: {result}")
            return result
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            raise

    async def test_list_pools(self) -> Dict[str, Any]:
        """测试列出所有代理池"""
        print("\n🔍 测试列出代理池...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.POOLS)
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 列出代理池成功:")
            for pool in result.get("pools", []):
                print(f"   - {pool['key']}: {pool['market']}/{pool['mode']} (运行: {pool['running']})")
            return result
        except Exception as e:
            print(f"❌ 列出代理池失败: {e}")
            raise

    async def test_get_config(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试获取配置"""
        print(f"\n🔍 测试获取配置 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.CONFIG)
            params = {"market": market, "mode": mode}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 获取配置成功:")
            print(f"   - 市场: {result.get('market')}")
            print(f"   - 模式: {result.get('mode')}")
            print(f"   - 后端: {result.get('backend')}")
            config = result.get('config', {})
            if config:
                print(f"   - 海量代理: {'启用' if config.get('hailiang_enabled') else '禁用'}")
                print(f"   - 批量大小: {config.get('batch_size')}")
                print(f"   - 轮换间隔: {config.get('rotation_interval_minutes')}分钟")
                print(f"   - 代理生命周期: {config.get('proxy_lifetime_minutes')}分钟")
            return result
        except Exception as e:
            print(f"❌ 获取配置失败: {e}")
            raise

    async def test_get_status(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试获取状态"""
        print(f"\n🔍 测试获取状态 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.STATUS)
            params = {"market": market, "mode": mode}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 获取状态成功:")
            print(f"   - 状态: {result.get('status')}")
            print(f"   - 运行中: {result.get('running')}")
            print(f"   - 市场状态: {result.get('market_status')}")
            stats = result.get('stats', {})
            if stats:
                print(f"   - 总请求: {stats.get('total_requests', 0)}")
                print(f"   - 成功率: {stats.get('success_rate', 0)}%")
            return result
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")
            raise

    async def test_start_service(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试启动服务"""
        print(f"\n🔍 测试启动服务 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.START)
            params = {"market": market, "mode": mode}
            response = await self.client.post(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 启动服务成功: {result.get('message')}")
            return result
        except Exception as e:
            print(f"❌ 启动服务失败: {e}")
            raise

    async def test_get_metrics(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试获取指标"""
        print(f"\n🔍 测试获取指标 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.METRICS)
            params = {"market": market, "mode": mode}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 获取指标成功:")
            print(f"   - 运行状态: {result.get('running')}")
            print(f"   - 活跃池: {result.get('active_pool')}")
            print(f"   - 活跃池大小: {result.get('size_active')}")
            print(f"   - 备用池大小: {result.get('size_standby')}")
            print(f"   - 总池大小: {result.get('total_pool_size')}")
            print(f"   - 成功率: {result.get('success_rate')}%")
            return result
        except Exception as e:
            print(f"❌ 获取指标失败: {e}")
            raise

    async def test_update_config(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试更新配置"""
        print(f"\n🔍 测试更新配置 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.CONFIG_UPDATE)
            params = {"market": market, "mode": mode}
            data = {
                "rotation_interval_minutes": 7,
                "proxy_lifetime_minutes": 10,
                "batch_size": 400
            }
            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 更新配置成功: {result.get('message')}")
            return result
        except Exception as e:
            print(f"❌ 更新配置失败: {e}")
            raise

    async def test_hailiang_api(self) -> Dict[str, Any]:
        """测试海量代理API"""
        print("\n🔍 测试海量代理API...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.CONFIG_HAILIANG_TEST)
            test_url = "http://api.hailiangip.com:8422/api/getIp?type=1&num=5&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0"
            data = {"api_url": test_url}
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 测试海量代理API成功:")
            print(f"   - 状态: {result.get('status')}")
            print(f"   - 获取数量: {result.get('proxy_count')}")
            print(f"   - 示例代理: {result.get('sample_proxies', [])[:3]}")
            return result
        except Exception as e:
            print(f"❌ 测试海量代理API失败: {e}")
            raise

    async def test_rpc_interface(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试RPC接口"""
        print(f"\n🔍 测试RPC接口 ({market}/{mode})...")

        # 测试ping
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.RPC)
            data = {
                "event": "ping",
                "market": market,
                "mode": mode
            }
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            print(f"✅ RPC Ping成功:")
            print(f"   - 消息: {result.get('message')}")
            print(f"   - 市场: {result.get('market')}")
            print(f"   - 模式: {result.get('mode')}")
            print(f"   - 运行状态: {result.get('running')}")
            print(f"   - 市场状态: {result.get('market_status')}")
            return result
        except Exception as e:
            print(f"❌ RPC接口测试失败: {e}")
            raise

    async def test_stop_service(self, market: str = "hk", mode: str = "live") -> Dict[str, Any]:
        """测试停止服务"""
        print(f"\n🔍 测试停止服务 ({market}/{mode})...")
        try:
            url = self.get_endpoint_url(ApiEndpoints.ProxyPool.STOP)
            params = {"market": market, "mode": mode}
            response = await self.client.post(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 停止服务成功: {result.get('message')}")
            return result
        except Exception as e:
            print(f"❌ 停止服务失败: {e}")
            raise

    async def run_comprehensive_test(self, market: str = "hk"):
        """运行综合测试"""
        print(f"\n🚀 开始综合测试 (市场: {market})")
        print("=" * 60)

        try:
            # 1. 健康检查
            await self.test_health_check()

            # 2. 列出代理池
            await self.test_list_pools()

            # 3. 获取配置
            await self.test_get_config(market, "live")

            # 4. 获取状态
            await self.test_get_status(market, "live")

            # 5. 启动服务
            await self.test_start_service(market, "live")

            # 6. 等待一下服务启动
            await asyncio.sleep(2)

            # 7. 获取指标
            await self.test_get_metrics(market, "live")

            # 8. 更新配置
            await self.test_update_config(market, "live")

            # 9. 测试海量代理API
            await self.test_hailiang_api()

            # 10. 测试RPC接口
            await self.test_rpc_interface(market, "live")

            # 11. 停止服务
            await self.test_stop_service(market, "live")

            print("\n🎉 所有测试完成!")

        except Exception as e:
            print(f"\n💥 测试失败: {e}")
            raise


async def main():
    """主函数"""
    environment = os.getenv("ENVIRONMENT", "development")
    market = os.getenv("MARKET", "hk")

    print("🧪 Saturn MouseHunter 代理池服务测试")
    print("=" * 60)

    async with ProxyPoolTester(environment) as tester:
        await tester.run_comprehensive_test(market)


if __name__ == "__main__":
    asyncio.run(main())