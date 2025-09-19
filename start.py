#!/usr/bin/env python3
"""
Saturn MouseHunter Proxy Pool Service 启动脚本
一劳永逸解决路径导入问题
"""

import os
import sys
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"

# 添加src目录到Python路径
sys.path.insert(0, str(SRC_DIR))

# 设置工作目录
os.chdir(PROJECT_ROOT)

if __name__ == "__main__":
    try:
        from src.main import main
        main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动错误: {e}")
        sys.exit(1)