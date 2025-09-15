#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理池轮换微服务测试示例
"""

import asyncio
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saturn_mousehunter_shared import get_logger
from infrastructure.proxy_pool import ProxyPoolManager
from infrastructure.config import get_proxy_pool_config


async def test_proxy_pool_service():
    """测试代理池服务"""
    logger = get_logger("proxy_pool_test")

    # 创建配置
    config = get_proxy_pool_config()
    config.market = "hk"
    config.mode = "test"
    config.target_size = 10
    config.min_refresh_secs = 30

    # 创建管理器
    manager = ProxyPoolManager(config)

    try:
        logger.info("启动代理池服务测试...")

        # 启动服务
        await manager.start()
        logger.info("服务启动成功")

        # 等待一些代理被加载
        await asyncio.sleep(2)

        # 测试获取代理
        for i in range(5):
            proxy = await manager.get_proxy()
            logger.info(f"获取代理 #{i+1}: {proxy}")

            if proxy:
                # 模拟失败报告
                if i % 2 == 0:
                    await manager.report_failure(proxy)
                    logger.info(f"报告代理失败: {proxy}")

        # 获取状态
        status = await manager.get_status()
        logger.info(f"服务状态: {status['running']}")
        logger.info(f"代理池统计: {status['stats']}")

        # 等待一个轮换周期
        logger.info("等待代理池轮换...")
        await asyncio.sleep(35)

        # 再次获取状态
        status = await manager.get_status()
        logger.info(f"轮换后统计: {status['stats']}")

    except Exception as e:
        logger.error(f"测试失败: {e}")
    finally:
        # 停止服务
        await manager.stop()
        logger.info("服务已停止")


async def test_api_client():
    """测试API客户端"""
    import httpx

    logger = get_logger("api_client_test")

    try:
        async with httpx.AsyncClient() as client:
            # 健康检查
            response = await client.get("http://localhost:8080/health")
            logger.info(f"健康检查: {response.json()}")

            # 获取配置
            response = await client.get("http://localhost:8080/api/v1/config")
            logger.info(f"配置信息: {response.json()}")

            # RPC调用 - 获取代理
            response = await client.post(
                "http://localhost:8080/api/v1/rpc",
                json={"event": "get_proxy", "proxy_type": "short"}
            )
            proxy_data = response.json()
            logger.info(f"RPC获取代理: {proxy_data}")

            # RPC调用 - ping
            response = await client.post(
                "http://localhost:8080/api/v1/rpc",
                json={"event": "ping"}
            )
            ping_data = response.json()
            logger.info(f"RPC ping: {ping_data}")

            # 如果有代理，测试失败报告
            if proxy_data.get("proxy"):
                response = await client.post(
                    "http://localhost:8080/api/v1/rpc",
                    json={
                        "event": "report_failure",
                        "proxy_addr": proxy_data["proxy"]
                    }
                )
                logger.info(f"报告失败: {response.json()}")

    except Exception as e:
        logger.error(f"API测试失败: {e}")


def test_external_fetch_function():
    """测试外部代理获取函数"""
    def custom_fetch_func():
        """自定义代理获取函数"""
        return [
            "http://custom-proxy-1.example.com:8080",
            "http://custom-proxy-2.example.com:8080",
            "http://custom-proxy-3.example.com:8080"
        ]

    # 创建配置
    config = get_proxy_pool_config()
    config.market = "hk"
    config.mode = "test"
    config.auto_start = False

    # 创建管理器并设置自定义获取函数
    manager = ProxyPoolManager(config)
    manager.set_external_fetcher(custom_fetch_func)

    print("外部代理获取函数设置成功")

    # 返回用于uvicorn启动的应用
    from main import app
    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="代理池测试")
    parser.add_argument(
        "--mode",
        choices=["service", "client", "external"],
        default="service",
        help="测试模式"
    )

    args = parser.parse_args()

    if args.mode == "service":
        asyncio.run(test_proxy_pool_service())
    elif args.mode == "client":
        asyncio.run(test_api_client())
    elif args.mode == "external":
        app = test_external_fetch_function()
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8081)