#!/usr/bin/env python3
"""
验证代理池服务配置读取
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

def main():
    print("🔧 验证代理池服务配置")
    print("=" * 50)

    try:
        # 1. 验证共享配置
        from saturn_mousehunter_shared.config.service_endpoints import get_service_config

        print("✅ 共享配置模块导入成功")

        # 2. 验证开发环境配置
        config = get_service_config("proxy-pool-service", "development")
        print(f"开发环境配置: {config}")

        expected_host = "192.168.8.168"
        expected_port = 8005

        if config["host"] == expected_host and config["port"] == expected_port:
            print("✅ 开发环境配置正确")
        else:
            print(f"❌ 配置不符合预期")
            return False

        # 3. 验证应用配置读取
        os.environ["ENVIRONMENT"] = "development"

        from infrastructure.config import get_app_config
        app_config = get_app_config()

        print(f"应用配置:")
        print(f"  Host: {app_config.host}")
        print(f"  Port: {app_config.port}")
        print(f"  App Name: {app_config.app_name}")

        if app_config.host == expected_host and app_config.port == expected_port:
            print("✅ 应用配置正确读取共享端点配置")
        else:
            print(f"❌ 应用配置读取失败")
            return False

        # 4. 验证启动命令
        print(f"\n🚀 服务启动信息:")
        print(f"启动地址: http://{app_config.host}:{app_config.port}")
        print(f"管理界面: http://{app_config.host}:{app_config.port}")
        print(f"API文档: http://{app_config.host}:{app_config.port}/docs")

        print(f"\n✅ 配置验证完成！")
        return True

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理环境变量
        os.environ.pop("ENVIRONMENT", None)


if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎉 代理池服务已正确配置为使用共享服务端点配置！")
        exit(0)
    else:
        exit(1)