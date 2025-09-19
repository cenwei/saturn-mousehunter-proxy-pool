#!/usr/bin/env python3
"""
修复代理池API配置脚本
修复数据库中的占位符API URL
"""

import asyncio
import asyncpg
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """数据库连接配置"""
    postgres_dsn: str = "postgresql://postgres:ChangeMe_StrongPwd!@192.168.8.188:30032/mh_central"

    class Config:
        env_prefix = "DATABASE_"
        extra = "ignore"


async def fix_api_config():
    """修复API配置中的占位符"""
    settings = DatabaseSettings()

    print(f"Connecting to: {settings.postgres_dsn}")

    try:
        conn = await asyncpg.connect(settings.postgres_dsn)

        # 正确的API URL（测试用，num=20）
        correct_api_url = "http://api.hailiangip.com:8422/api/getIp?type=1&num=20&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0"

        # 查询当前配置
        current_configs = await conn.fetch("""
            SELECT market, mode, hailiang_api_url
            FROM proxy_pool_config
            WHERE hailiang_api_url LIKE '%your_pid%'
        """)

        if current_configs:
            print(f"发现 {len(current_configs)} 个需要修复的配置:")
            for config in current_configs:
                print(f"  - {config['market']}/{config['mode']}")

            # 更新所有包含占位符的配置
            updated_count = await conn.execute("""
                UPDATE proxy_pool_config
                SET hailiang_api_url = $1, updated_at = NOW()
                WHERE hailiang_api_url LIKE '%your_pid%'
            """, correct_api_url)

            print(f"✅ 成功更新 {updated_count} 个配置")

            # 验证更新结果
            remaining_placeholders = await conn.fetchval("""
                SELECT COUNT(*) FROM proxy_pool_config
                WHERE hailiang_api_url LIKE '%your_pid%'
            """)

            if remaining_placeholders == 0:
                print("✅ 所有占位符已清理完毕")
            else:
                print(f"⚠️ 仍有 {remaining_placeholders} 个配置包含占位符")

        else:
            print("✅ 没有发现需要修复的配置")

        # 显示当前所有配置
        all_configs = await conn.fetch("""
            SELECT market, mode,
                   CASE
                       WHEN LENGTH(hailiang_api_url) > 50
                       THEN LEFT(hailiang_api_url, 50) || '...'
                       ELSE hailiang_api_url
                   END as api_url_short
            FROM proxy_pool_config
            ORDER BY market, mode
        """)

        print(f"\n📊 当前所有配置 ({len(all_configs)} 个):")
        for config in all_configs:
            print(f"  - {config['market']}/{config['mode']}: {config['api_url_short']}")

        await conn.close()
        print("\n🎉 API配置修复完成!")

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(fix_api_config())