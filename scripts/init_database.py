#!/usr/bin/env python3
"""
数据库初始化脚本 - 代理池微服务

创建PostgreSQL表结构，支持：
- 代理池配置存储
- 代理池状态追踪
- 多市场多模式支持
"""

import asyncio
import asyncpg
from datetime import datetime
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """数据库连接配置"""
    postgres_dsn: str = "postgresql://postgres:ChangeMe_StrongPwd!@192.168.8.188:30032/mh_central"

    class Config:
        env_prefix = "DATABASE_"
        extra = "ignore"


async def create_tables():
    """创建数据库表"""
    settings = DatabaseSettings()

    print(f"Connecting to: {settings.postgres_dsn}")

    try:
        conn = await asyncpg.connect(settings.postgres_dsn)

        # 创建代理池配置表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS proxy_pool_config (
                id BIGSERIAL PRIMARY KEY,
                market VARCHAR(10) NOT NULL,
                mode VARCHAR(20) NOT NULL,
                hailiang_api_url TEXT NOT NULL,
                hailiang_enabled BOOLEAN DEFAULT TRUE,
                batch_size INTEGER DEFAULT 400,
                proxy_lifetime_minutes INTEGER DEFAULT 10,
                rotation_interval_minutes INTEGER DEFAULT 7,
                low_watermark INTEGER DEFAULT 50,
                target_size INTEGER DEFAULT 200,
                auto_start_enabled BOOLEAN DEFAULT TRUE,
                pre_market_start_minutes INTEGER DEFAULT 2,
                post_market_stop_minutes INTEGER DEFAULT 30,
                backfill_enabled BOOLEAN DEFAULT FALSE,
                backfill_duration_hours INTEGER DEFAULT 2,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                UNIQUE(market, mode)
            );
        """)
        print("✅ 代理池配置表创建成功")

        # 创建代理池状态表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS proxy_pool_status (
                id BIGSERIAL PRIMARY KEY,
                market VARCHAR(10) NOT NULL,
                mode VARCHAR(20) NOT NULL,
                is_running BOOLEAN DEFAULT FALSE,
                active_pool VARCHAR(1) DEFAULT 'A',
                pool_a_size INTEGER DEFAULT 0,
                pool_b_size INTEGER DEFAULT 0,
                total_requests BIGINT DEFAULT 0,
                success_count BIGINT DEFAULT 0,
                failure_count BIGINT DEFAULT 0,
                success_rate DECIMAL(5,2) DEFAULT 0.00,
                last_rotation_time TIMESTAMP WITH TIME ZONE,
                last_fetch_time TIMESTAMP WITH TIME ZONE,
                api_failure_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                UNIQUE(market, mode)
            );
        """)
        print("✅ 代理池状态表创建成功")

        # 创建索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_proxy_pool_config_market_mode
            ON proxy_pool_config(market, mode);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_proxy_pool_status_market_mode
            ON proxy_pool_status(market, mode);
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_proxy_pool_status_running
            ON proxy_pool_status(is_running);
        """)
        print("✅ 索引创建成功")

        # 插入默认配置数据
        markets_modes = [
            ("hk", "live"),
            ("hk", "backfill"),
            ("cn", "live"),
            ("cn", "backfill"),
            ("us", "live"),
            ("us", "backfill"),
        ]

        for market, mode in markets_modes:
            # 检查是否已存在
            existing = await conn.fetchrow("""
                SELECT id FROM proxy_pool_config WHERE market = $1 AND mode = $2
            """, market, mode)

            if not existing:
                # 插入默认配置
                await conn.execute("""
                    INSERT INTO proxy_pool_config (
                        market, mode, hailiang_api_url, hailiang_enabled, batch_size,
                        proxy_lifetime_minutes, rotation_interval_minutes, low_watermark,
                        target_size, auto_start_enabled, pre_market_start_minutes,
                        post_market_stop_minutes, backfill_enabled, backfill_duration_hours
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                    )
                """,
                    market, mode,
                    "http://api.hailiangip.com:8422/api/getIp?type=1&num=20&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0",
                    True, 400, 10, 7, 50, 200, True, 2, 30,
                    mode == "backfill", 2 if mode == "backfill" else 0
                )

                # 插入默认状态
                await conn.execute("""
                    INSERT INTO proxy_pool_status (
                        market, mode, is_running, active_pool, pool_a_size, pool_b_size,
                        total_requests, success_count, failure_count, success_rate
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                    )
                """, market, mode, False, 'A', 0, 0, 0, 0, 0, 0.0)

                print(f"✅ 初始化 {market}/{mode} 配置和状态")

        print("✅ 默认数据插入成功")

        # 显示表信息
        tables_info = await conn.fetch("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_name LIKE 'proxy_pool%'
            ORDER BY table_name;
        """)

        print("\n📊 数据库表信息:")
        for table in tables_info:
            print(f"  - {table['table_name']}: {table['column_count']} 列")

        # 显示数据统计
        config_count = await conn.fetchval("SELECT COUNT(*) FROM proxy_pool_config")
        status_count = await conn.fetchval("SELECT COUNT(*) FROM proxy_pool_status")

        print(f"\n📈 数据统计:")
        print(f"  - 配置记录: {config_count}")
        print(f"  - 状态记录: {status_count}")

        await conn.close()
        print("\n🎉 数据库初始化完成!")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_tables())