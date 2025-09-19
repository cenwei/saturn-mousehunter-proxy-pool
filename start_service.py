#!/usr/bin/env python3
"""
代理池微服务启动器
在微服务目录内启动，无需污染workspace
"""

import os
import sys
import signal
import subprocess
from pathlib import Path
from typing import Optional
import time
import psutil

# 设置路径
service_root = Path(__file__).parent
workspace_root = service_root.parent

# 添加共享库路径
shared_path = workspace_root / "saturn-mousehunter-shared" / "src"
sys.path.insert(0, str(shared_path))

try:
    from saturn_mousehunter_shared import get_logger
    log = get_logger("proxy_pool_service")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("proxy_pool_service")


class ProxyPoolService:
    """代理池微服务管理器"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.running = False

        # 从环境变量获取配置
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.proxy_markets = os.getenv("MARKETS", "cn,hk,us")
        self.service_port = int(os.getenv("PORT", "8005"))

        # 服务文件路径
        self.main_file = service_root / "src" / "main.py"

    def _is_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    return False
            return True
        except:
            return True

    def start(self) -> bool:
        """启动代理池微服务"""
        if self.process and self.process.poll() is None:
            log.info("代理池服务已在运行")
            return True

        # 检查主文件
        if not self.main_file.exists():
            log.error(f"主文件不存在: {self.main_file}")
            return False

        # 检查端口
        if not self._is_port_available(self.service_port):
            log.warning(f"端口 {self.service_port} 已被占用，服务可能已在运行")
            return True

        # 设置环境变量
        env = os.environ.copy()
        env.update({
            "ENVIRONMENT": self.environment,
            "MARKETS": self.proxy_markets,
            "AUTO_START_POOLS": "true"
        })

        # 启动命令 - 直接在微服务目录内运行
        cmd = ["uv", "run", "python", "src/main.py"]

        try:
            log.info("🚀 启动代理池微服务")
            log.info(f"   环境: {self.environment}")
            log.info(f"   市场: {self.proxy_markets}")
            log.info(f"   端口: {self.service_port}")

            self.process = subprocess.Popen(
                cmd,
                cwd=service_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            log.info(f"✅ 代理池服务启动成功 (PID: {self.process.pid})")
            self.running = True
            return True

        except Exception as e:
            log.error(f"❌ 启动代理池服务失败: {e}")
            return False

    def stop(self):
        """停止代理池微服务"""
        if not self.process:
            return

        log.info("停止代理池微服务")

        try:
            self.process.terminate()
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            log.warning("强制终止代理池服务")
            self.process.kill()
        except Exception as e:
            log.error(f"停止代理池服务失败: {e}")

        self.running = False
        self.process = None

    def run(self):
        """运行代理池微服务"""
        def signal_handler(signum, frame):
            log.info(f"收到信号 {signum}，正在停止服务...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            if not self.start():
                log.error("启动代理池服务失败")
                return 1

            # 显示服务状态
            print(f"\n🎯 代理池微服务已启动:")
            print("=" * 40)
            print(f"✅ 端口: {self.service_port}")
            print(f"📊 市场: {self.proxy_markets}")
            print("=" * 40)
            print(f"🌐 API文档: http://localhost:{self.service_port}/docs")
            print(f"🔍 健康检查: http://localhost:{self.service_port}/health")
            print("\n按 Ctrl+C 停止服务")

            # 等待进程结束或用户中断
            while self.running and self.process:
                if self.process.poll() is not None:
                    log.error("代理池服务意外停止")
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            log.info("用户中断")
        except Exception as e:
            log.error(f"运行异常: {e}")
            return 1
        finally:
            self.stop()

        return 0


def main():
    """主函数"""
    print("🚀 代理池微服务启动器")
    print("=" * 30)

    service = ProxyPoolService()
    return service.run()


if __name__ == "__main__":
    sys.exit(main())