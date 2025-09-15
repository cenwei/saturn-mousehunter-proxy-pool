#!/usr/bin/env python3
"""
测试代理池服务配置是否正确读取共享服务端点配置
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

def test_config():
    print("🔧 测试代理池服务配置")
    print("=" * 60)

    try:
        # 测试共享配置导入
        from saturn_mousehunter_shared.config.service_endpoints import (
            ServiceEndpointConfig,
            get_service_config,
            ServiceUrls
        )

        print("✅ 共享配置模块导入成功")

        # 测试不同环境的配置
        environments = ["development", "testing", "production"]

        for env in environments:
            print(f"\n📋 {env.upper()} 环境配置:")
            try:
                config = get_service_config("proxy-pool-service", env)
                print(f"  Host: {config['host']}")
                print(f"  Port: {config['port']}")
                print(f"  Base URL: {config['base_url']}")
            except Exception as e:
                print(f"  ❌ 获取配置失败: {e}")

        # 测试应用配置
        print(f"\n🏗️ 测试应用配置加载:")

        # 设置不同环境变量测试
        test_cases = [
            ("development", None),
            ("testing", "ENVIRONMENT=testing"),
            ("production", "ENVIRONMENT=production"),
        ]

        for env_name, env_var in test_cases:
            print(f"\n  测试 {env_name} 环境:")

            # 设置环境变量
            if env_var:
                key, value = env_var.split("=")
                os.environ[key] = value

            try:
                # 重新导入配置模块以应用新的环境变量
                import importlib
                import infrastructure.config
                importlib.reload(infrastructure.config)

                from infrastructure.config import get_app_config

                app_config = get_app_config()
                print(f"    Host: {app_config.host}")
                print(f"    Port: {app_config.port}")
                print(f"    App Name: {app_config.app_name}")
                print(f"    Debug: {app_config.debug}")

            except Exception as e:
                print(f"    ❌ 配置加载失败: {e}")

            # 清理环境变量
            if env_var:
                key = env_var.split("=")[0]
                if key in os.environ:
                    del os.environ[key]

        print(f"\n🌐 常用服务URL:")
        print(f"  Proxy Pool: {ServiceUrls.PROXY_POOL}")
        print(f"  Market Data: {ServiceUrls.MARKET_DATA}")
        print(f"  Auth: {ServiceUrls.AUTH}")

        print(f"\n✅ 配置测试完成！")

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保saturn-mousehunter-shared已正确安装")
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

    return True


def test_service_startup():
    """测试服务启动配置"""
    print(f"\n🚀 测试服务启动配置")
    print("=" * 60)

    try:
        # 测试默认开发环境
        os.environ.pop("ENVIRONMENT", None)  # 清除环境变量

        from infrastructure.config import get_app_config
        config = get_app_config()

        print(f"默认配置:")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Debug: {config.debug}")

        # 测试指定开发环境
        os.environ["ENVIRONMENT"] = "development"

        # 重新导入以获取新配置
        import importlib
        import infrastructure.config
        importlib.reload(infrastructure.config)

        config = get_app_config()

        print(f"\n开发环境配置:")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  应该是: 192.168.8.168:8005")

        if config.host == "192.168.8.168" and config.port == 8005:
            print("✅ 开发环境配置正确!")
        else:
            print("⚠️ 开发环境配置可能不正确")

        return True

    except Exception as e:
        print(f"❌ 服务启动配置测试失败: {e}")
        return False

    finally:
        # 清理环境变量
        os.environ.pop("ENVIRONMENT", None)


if __name__ == "__main__":
    success = True

    success &= test_config()
    success &= test_service_startup()

    if success:
        print(f"\n🎉 所有测试通过！代理池服务已配置为读取共享服务端点配置。")
        exit(0)
    else:
        print(f"\n❌ 部分测试失败，请检查配置。")
        exit(1)