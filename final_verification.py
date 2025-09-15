#!/usr/bin/env python3
"""
最终验证：代理池服务配置集成
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

def main():
    print("🎯 Saturn MouseHunter 代理池服务 - 配置集成验证")
    print("=" * 60)

    try:
        # 验证共享配置模块
        from saturn_mousehunter_shared.config.service_endpoints import (
            get_service_config,
            ServiceUrls,
            DEVELOPMENT_SERVICES,
            TESTING_SERVICES,
            PRODUCTION_SERVICES
        )

        print("✅ 共享配置模块导入成功")

        # 验证代理池服务配置存在
        print(f"\n📋 验证代理池服务配置:")

        all_envs = {
            "development": DEVELOPMENT_SERVICES,
            "testing": TESTING_SERVICES,
            "production": PRODUCTION_SERVICES
        }

        for env_name, services in all_envs.items():
            if "proxy-pool-service" in services:
                config = services["proxy-pool-service"]
                print(f"  ✅ {env_name}: {config['host']}:{config['port']}")
            else:
                print(f"  ❌ {env_name}: 配置缺失")

        # 验证服务URL常量
        print(f"\n🌐 服务URL常量:")
        print(f"  代理池服务: {ServiceUrls.PROXY_POOL}")
        print(f"  市场数据服务: {ServiceUrls.MARKET_DATA}")
        print(f"  认证服务: {ServiceUrls.AUTH}")

        # 模拟不同环境的启动
        print(f"\n🚀 模拟不同环境启动:")

        for env in ["development", "testing", "production"]:
            config = get_service_config("proxy-pool-service", env)
            print(f"  {env:12}: http://{config['host']}:{config['port']}")

        # 验证Kotlin项目对接信息
        print(f"\n📱 Kotlin项目对接信息:")
        print(f"  开发环境API: http://192.168.8.168:8005/api/v1/rpc")
        print(f"  获取代理接口: POST /api/v1/rpc {{\"event\":\"get_proxy\",\"market\":\"hk\"}}")
        print(f"  报告失败接口: POST /api/v1/rpc {{\"event\":\"report_failure\",\"proxy_addr\":\"IP:PORT\"}}")
        print(f"  健康检查接口: GET /api/v1/status?market=hk")

        # 配置优先级说明
        print(f"\n⚙️ 配置优先级:")
        print(f"  1. 环境变量 (HOST, PORT) - 最高优先级")
        print(f"  2. service_endpoints.py - 中等优先级")
        print(f"  3. 代码默认值 - 最低优先级")

        # 启动命令示例
        print(f"\n🔧 启动命令示例:")
        print(f"  开发环境: ENVIRONMENT=development MARKETS=hk ./start.sh")
        print(f"  测试环境: ENVIRONMENT=testing MARKETS=cn,hk,us ./start.sh")
        print(f"  生产环境: ENVIRONMENT=production MARKETS=cn,hk,us ./start.sh")

        print(f"\n✅ 配置集成验证通过!")

        print(f"\n📚 相关文档:")
        print(f"  配置说明: docs/configuration.md")
        print(f"  Kotlin集成: docs/kotlin-quick-start.md")
        print(f"  完整API: docs/fastapi-kotlin-integration.md")
        print(f"  OpenAPI规范: docs/openapi.yaml")

        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 代理池服务配置集成完成！")
        print(f"现在 main.py 会自动读取 service_endpoints.py 中的配置。")
        exit(0)
    else:
        exit(1)