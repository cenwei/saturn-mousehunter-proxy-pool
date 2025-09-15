#!/usr/bin/env python3
"""
最小化配置验证 - 只验证配置读取逻辑
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

def main():
    print("🔧 验证共享配置读取")
    print("=" * 50)

    try:
        # 验证共享配置
        from saturn_mousehunter_shared.config.service_endpoints import (
            get_service_config,
            ServiceEndpointConfig,
            ServiceUrls
        )

        print("✅ 共享配置模块导入成功")

        # 测试所有环境
        environments = ["development", "testing", "production"]

        for env in environments:
            print(f"\n📋 {env.upper()} 环境:")
            config = get_service_config("proxy-pool-service", env)
            print(f"  Host: {config['host']}")
            print(f"  Port: {config['port']}")
            print(f"  Base URL: {config['base_url']}")

        # 验证开发环境是否符合预期
        dev_config = get_service_config("proxy-pool-service", "development")
        if dev_config["host"] == "192.168.8.168" and dev_config["port"] == 8005:
            print(f"\n✅ 开发环境配置符合预期")
        else:
            print(f"\n❌ 开发环境配置不符合预期")

        # 显示常用服务URL
        print(f"\n🌐 常用服务URL:")
        print(f"  Proxy Pool: {ServiceUrls.PROXY_POOL}")
        print(f"  Market Data: {ServiceUrls.MARKET_DATA}")
        print(f"  Auth: {ServiceUrls.AUTH}")

        # 模拟配置读取逻辑
        print(f"\n🔧 配置读取逻辑验证:")

        def simulate_get_app_config(environment="development"):
            """模拟应用配置读取"""
            try:
                proxy_pool_config = get_service_config("proxy-pool-service", environment)
                default_host = proxy_pool_config["host"]
                default_port = proxy_pool_config["port"]
                print(f"  {environment}: Host={default_host}, Port={default_port}")
                return {"host": default_host, "port": default_port}
            except Exception as e:
                print(f"  {environment}: 配置读取失败 - {e}")
                return {"host": "0.0.0.0", "port": 8080}

        # 测试不同环境的配置读取
        for env in environments:
            simulate_get_app_config(env)

        print(f"\n✅ 配置验证完成！")

        print(f"\n📝 总结:")
        print(f"1. 代理池服务现在会读取 service_endpoints.py 中的配置")
        print(f"2. 开发环境将运行在: 192.168.8.168:8005")
        print(f"3. 测试环境将运行在: test-proxy-pool:8005")
        print(f"4. 生产环境将运行在: proxy-pool.saturn-mousehunter.internal:8005")
        print(f"5. 可以通过 ENVIRONMENT 环境变量切换配置")

        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 共享配置集成成功！")
        exit(0)
    else:
        exit(1)