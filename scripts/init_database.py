#!/usr/bin/env python3
"""
代理池服务数据库初始化脚本
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, '/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src')

from saturn_mousehunter_shared import get_logger
from saturn_mousehunter_shared.infra.database import get_db_connection
from domain.config_entities import ProxyPoolConfig, ProxyPoolStatus, ProxyPoolMode
from infrastructure.database_repositories import (
    DatabaseProxyPoolConfigRepository,
    DatabaseProxyPoolStatusRepository
)

log = get_logger("db_init")


async def create_tables():
    """创建数据库表"""
    log.info("Creating database tables...")

    # 读取SQL文件
    sql_file = project_root / "sql" / "proxy_pool_config.sql"

    if not sql_file.exists():
        log.error(f"SQL file not found: {sql_file}")
        return False

    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        async with get_db_connection() as conn:
            for statement in statements:
                if statement:
                    try:
                        await conn.execute(statement)
                        log.info(f"Executed SQL statement: {statement[:50]}...")
                    except Exception as e:
                        log.error(f"Error executing SQL: {e}")
                        log.error(f"Statement: {statement}")

        log.info("✅ Database tables created successfully")
        return True

    except Exception as e:
        log.error(f"Error creating tables: {e}")
        return False


async def init_default_configs():
    """初始化默认配置"""
    log.info("Initializing default configurations...")

    try:
        config_repo = DatabaseProxyPoolConfigRepository()
        status_repo = DatabaseProxyPoolStatusRepository()

        # 检查是否已有配置
        existing_configs = await config_repo.get_all_active_configs()
        if existing_configs:
            log.info(f"Found {len(existing_configs)} existing configurations, skipping initialization")
            return True

        # 默认海量代理URL
        default_url = "http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0"

        # 创建三个市场的默认配置
        markets = ["cn", "hk", "us"]

        for market in markets:
            # Live模式配置
            live_config = ProxyPoolConfig(
                market=market,
                mode=ProxyPoolMode.LIVE,
                hailiang_api_url=default_url,
                hailiang_enabled=True,
                batch_size=400,
                proxy_lifetime_minutes=10,
                rotation_interval_minutes=7,
                low_watermark=50,
                target_size=200,
                auto_start_enabled=True,
                pre_market_start_minutes=2,  # 盘前2分钟启动
                post_market_stop_minutes=30,
                backfill_enabled=False,
                backfill_duration_hours=2,
                is_active=True
            )

            saved_config = await config_repo.save_config(live_config)
            log.info(f"✅ Created live config for {market}: ID {saved_config.id}")

            # Backfill模式配置
            backfill_config = ProxyPoolConfig(
                market=market,
                mode=ProxyPoolMode.BACKFILL,
                hailiang_api_url=default_url,
                hailiang_enabled=True,
                batch_size=400,
                proxy_lifetime_minutes=10,
                rotation_interval_minutes=7,
                low_watermark=50,
                target_size=200,
                auto_start_enabled=False,  # backfill模式不自动启动
                pre_market_start_minutes=0,
                post_market_stop_minutes=0,
                backfill_enabled=True,
                backfill_duration_hours=2,
                is_active=True
            )

            saved_backfill = await config_repo.save_config(backfill_config)
            log.info(f"✅ Created backfill config for {market}: ID {saved_backfill.id}")

            # 创建初始状态记录
            live_status = ProxyPoolStatus(
                market=market,
                mode=ProxyPoolMode.LIVE,
                is_running=False,
                active_pool='A',
                pool_a_size=0,
                pool_b_size=0,
                total_requests=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0
            )

            await status_repo.save_status(live_status)
            log.info(f"✅ Created initial status for {market} live mode")

            backfill_status = ProxyPoolStatus(
                market=market,
                mode=ProxyPoolMode.BACKFILL,
                is_running=False,
                active_pool='A',
                pool_a_size=0,
                pool_b_size=0,
                total_requests=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0
            )

            await status_repo.save_status(backfill_status)
            log.info(f"✅ Created initial status for {market} backfill mode")

        log.info("✅ Default configurations initialized successfully")
        return True

    except Exception as e:
        log.error(f"Error initializing default configs: {e}")
        return False


async def verify_database():
    """验证数据库设置"""
    log.info("Verifying database setup...")

    try:
        config_repo = DatabaseProxyPoolConfigRepository()
        status_repo = DatabaseProxyPoolStatusRepository()

        # 测试配置表
        configs = await config_repo.get_all_active_configs()
        log.info(f"Found {len(configs)} active configurations:")

        for config in configs:
            log.info(f"  - {config.market}/{config.mode.value}: "
                    f"auto_start={config.auto_start_enabled}, "
                    f"pre_start={config.pre_market_start_minutes}min")

        # 测试状态表
        for config in configs:
            status = await status_repo.get_status(config.market, config.mode)
            if status:
                log.info(f"  - Status {config.market}/{config.mode.value}: "
                        f"running={status.is_running}")

        log.info("✅ Database verification completed successfully")
        return True

    except Exception as e:
        log.error(f"Error verifying database: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 Saturn MouseHunter 代理池数据库初始化")
    print("=" * 60)

    try:
        # 1. 创建表
        if not await create_tables():
            print("❌ 表创建失败")
            return 1

        # 2. 初始化默认配置
        if not await init_default_configs():
            print("❌ 默认配置初始化失败")
            return 1

        # 3. 验证数据库
        if not await verify_database():
            print("❌ 数据库验证失败")
            return 1

        print("\n🎉 数据库初始化完成！")
        print("\n📋 配置摘要:")
        print("- 支持市场: CN, HK, US")
        print("- 每个市场都有 live 和 backfill 两种模式")
        print("- 盘前2分钟自动启动，盘后30分钟自动停止")
        print("- 默认400个代理，10分钟生命周期，7分钟轮换")
        print("\n🌐 访问管理界面: http://localhost:8080")

        return 0

    except Exception as e:
        log.error(f"Initialization failed: {e}")
        print(f"❌ 初始化失败: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)