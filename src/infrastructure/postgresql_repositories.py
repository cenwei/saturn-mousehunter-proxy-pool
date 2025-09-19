"""
Infrastructure层 - 代理池配置PostgreSQL仓储实现
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime
import asyncpg
from pydantic_settings import BaseSettings

from saturn_mousehunter_shared import get_logger
from domain.config_entities import (
    ProxyPoolConfig,
    ProxyPoolStatus,
    ProxyPoolMode,
    IProxyPoolConfigRepository,
    IProxyPoolStatusRepository,
)


class DatabaseSettings(BaseSettings):
    """数据库连接配置"""

    postgres_dsn: str = (
        "postgresql://postgres:ChangeMe_StrongPwd!@192.168.8.188:30032/mh_central"
    )
    postgres_pool_min: int = 1
    postgres_pool_max: int = 16
    postgres_timeout: float = 30.0

    class Config:
        env_prefix = "DATABASE_"
        extra = "ignore"


# 全局连接池
_connection_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """获取数据库连接池"""
    global _connection_pool

    if _connection_pool is None:
        settings = DatabaseSettings()
        _connection_pool = await asyncpg.create_pool(
            settings.postgres_dsn,
            min_size=settings.postgres_pool_min,
            max_size=settings.postgres_pool_max,
            command_timeout=settings.postgres_timeout,
        )

    return _connection_pool


async def close_db_pool():
    """关闭数据库连接池"""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None


class PostgreSQLProxyPoolConfigRepository(IProxyPoolConfigRepository):
    """PostgreSQL代理池配置仓储"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    async def get_config(self, market: str, mode: ProxyPoolMode) -> ProxyPoolConfig:
        """获取配置"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # 首先尝试查询现有配置
            query = """
                SELECT market, mode, hailiang_api_url, hailiang_enabled, batch_size,
                       proxy_lifetime_minutes, rotation_interval_minutes, low_watermark,
                       target_size, auto_start_enabled, pre_market_start_minutes,
                       post_market_stop_minutes, backfill_enabled, backfill_duration_hours,
                       created_at, updated_at
                FROM proxy_pool_config
                WHERE market = $1 AND mode = $2
            """

            row = await conn.fetchrow(query, market, mode.value)

            if row:
                return ProxyPoolConfig(
                    market=row["market"],
                    mode=ProxyPoolMode(row["mode"]),
                    hailiang_api_url=row["hailiang_api_url"],
                    hailiang_enabled=row["hailiang_enabled"],
                    batch_size=row["batch_size"],
                    proxy_lifetime_minutes=row["proxy_lifetime_minutes"],
                    rotation_interval_minutes=row["rotation_interval_minutes"],
                    low_watermark=row["low_watermark"],
                    target_size=row["target_size"],
                    auto_start_enabled=row["auto_start_enabled"],
                    pre_market_start_minutes=row["pre_market_start_minutes"],
                    post_market_stop_minutes=row["post_market_stop_minutes"],
                    backfill_enabled=row["backfill_enabled"],
                    backfill_duration_hours=row["backfill_duration_hours"],
                    is_active=True,  # 默认激活状态
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            else:
                # 创建默认配置
                default_config = ProxyPoolConfig(market=market, mode=mode)
                await self.save_config(default_config)
                return default_config

    async def save_config(self, config: ProxyPoolConfig) -> bool:
        """保存配置"""
        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO proxy_pool_config (
                        market, mode, hailiang_api_url, hailiang_enabled, batch_size,
                        proxy_lifetime_minutes, rotation_interval_minutes, low_watermark,
                        target_size, auto_start_enabled, pre_market_start_minutes,
                        post_market_stop_minutes, backfill_enabled, backfill_duration_hours,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    )
                    ON CONFLICT (market, mode)
                    DO UPDATE SET
                        hailiang_api_url = EXCLUDED.hailiang_api_url,
                        hailiang_enabled = EXCLUDED.hailiang_enabled,
                        batch_size = EXCLUDED.batch_size,
                        proxy_lifetime_minutes = EXCLUDED.proxy_lifetime_minutes,
                        rotation_interval_minutes = EXCLUDED.rotation_interval_minutes,
                        low_watermark = EXCLUDED.low_watermark,
                        target_size = EXCLUDED.target_size,
                        auto_start_enabled = EXCLUDED.auto_start_enabled,
                        pre_market_start_minutes = EXCLUDED.pre_market_start_minutes,
                        post_market_stop_minutes = EXCLUDED.post_market_stop_minutes,
                        backfill_enabled = EXCLUDED.backfill_enabled,
                        backfill_duration_hours = EXCLUDED.backfill_duration_hours,
                        updated_at = EXCLUDED.updated_at
                """

                await conn.execute(
                    query,
                    config.market,
                    config.mode.value,
                    config.hailiang_api_url,
                    config.hailiang_enabled,
                    config.batch_size,
                    config.proxy_lifetime_minutes,
                    config.rotation_interval_minutes,
                    config.low_watermark,
                    config.target_size,
                    config.auto_start_enabled,
                    config.pre_market_start_minutes,
                    config.post_market_stop_minutes,
                    config.backfill_enabled,
                    config.backfill_duration_hours,
                    config.created_at,
                    config.updated_at,
                )

                self.logger.info(
                    f"Saved config for {config.market}/{config.mode.value}"
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    async def update_config(self, market: str, mode: ProxyPoolMode, **kwargs) -> bool:
        """更新配置"""
        if not kwargs:
            return False

        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                # 构建动态更新语句
                set_clauses = []
                values = []
                param_count = 1

                for field, value in kwargs.items():
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1

                # 添加 updated_at
                set_clauses.append(f"updated_at = ${param_count}")
                values.append(datetime.now())
                param_count += 1

                # 添加 WHERE 条件的参数
                values.extend([market, mode.value])

                query = f"""
                    UPDATE proxy_pool_config
                    SET {", ".join(set_clauses)}
                    WHERE market = ${param_count} AND mode = ${param_count + 1}
                """

                result = await conn.execute(query, *values)

                if result == "UPDATE 1":
                    self.logger.info(f"Updated config for {market}/{mode.value}")
                    return True
                else:
                    self.logger.warning(
                        f"No config found to update for {market}/{mode.value}"
                    )
                    return False

        except Exception as e:
            self.logger.error(f"Failed to update config: {e}")
            return False

    async def get_all_active_configs(self) -> list[ProxyPoolConfig]:
        """获取所有激活的配置（不依赖is_active列）"""
        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                # 由于实际数据库表可能没有is_active列，我们查询所有配置
                # 可以通过其他逻辑判断是否激活（比如enabled字段）
                query = """
                    SELECT market, mode, hailiang_api_url, hailiang_enabled, batch_size,
                           proxy_lifetime_minutes, rotation_interval_minutes, low_watermark,
                           target_size, auto_start_enabled, pre_market_start_minutes,
                           post_market_stop_minutes, backfill_enabled, backfill_duration_hours,
                           created_at, updated_at
                    FROM proxy_pool_config
                    WHERE hailiang_enabled = TRUE
                    ORDER BY market, mode
                """

                rows = await conn.fetch(query)
                configs = []

                for row in rows:
                    config = ProxyPoolConfig(
                        market=row["market"],
                        mode=ProxyPoolMode(row["mode"]),
                        hailiang_api_url=row["hailiang_api_url"],
                        hailiang_enabled=row["hailiang_enabled"],
                        batch_size=row["batch_size"],
                        proxy_lifetime_minutes=row["proxy_lifetime_minutes"],
                        rotation_interval_minutes=row["rotation_interval_minutes"],
                        low_watermark=row["low_watermark"],
                        target_size=row["target_size"],
                        auto_start_enabled=row["auto_start_enabled"],
                        pre_market_start_minutes=row["pre_market_start_minutes"],
                        post_market_stop_minutes=row["post_market_stop_minutes"],
                        backfill_enabled=row["backfill_enabled"],
                        backfill_duration_hours=row["backfill_duration_hours"],
                        is_active=True,  # 默认设为激活，因为我们已经通过hailiang_enabled过滤了
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    configs.append(config)

                return configs

        except Exception as e:
            self.logger.error(f"Failed to get all active configs: {e}")
            return []


class PostgreSQLProxyPoolStatusRepository(IProxyPoolStatusRepository):
    """PostgreSQL代理池状态仓储"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    async def get_status(self, market: str, mode: ProxyPoolMode) -> ProxyPoolStatus:
        """获取状态"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            query = """
                SELECT market, mode, is_running, active_pool, pool_a_size, pool_b_size,
                       total_requests, success_count, failure_count, success_rate,
                       last_rotation_time, last_fetch_time, api_failure_count,
                       created_at, updated_at
                FROM proxy_pool_status
                WHERE market = $1 AND mode = $2
            """

            row = await conn.fetchrow(query, market, mode.value)

            if row:
                return ProxyPoolStatus(
                    market=row["market"],
                    mode=ProxyPoolMode(row["mode"]),
                    is_running=row["is_running"],
                    active_pool=row["active_pool"],
                    pool_a_size=row["pool_a_size"],
                    pool_b_size=row["pool_b_size"],
                    total_requests=row["total_requests"],
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    success_rate=row["success_rate"],
                    started_at=None,  # 数据库表中没有这个字段
                    stopped_at=None,  # 数据库表中没有这个字段
                    last_rotation_at=row["last_rotation_time"],  # 映射字段名
                    updated_at=row["updated_at"],
                )
            else:
                # 创建默认状态
                default_status = ProxyPoolStatus(market=market, mode=mode)
                await self.save_status(default_status)
                return default_status

    async def save_status(self, status: ProxyPoolStatus) -> bool:
        """保存状态"""
        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO proxy_pool_status (
                        market, mode, is_running, active_pool, pool_a_size, pool_b_size,
                        total_requests, success_count, failure_count, success_rate,
                        last_rotation_time, last_fetch_time, api_failure_count,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    )
                    ON CONFLICT (market, mode)
                    DO UPDATE SET
                        is_running = EXCLUDED.is_running,
                        active_pool = EXCLUDED.active_pool,
                        pool_a_size = EXCLUDED.pool_a_size,
                        pool_b_size = EXCLUDED.pool_b_size,
                        total_requests = EXCLUDED.total_requests,
                        success_count = EXCLUDED.success_count,
                        failure_count = EXCLUDED.failure_count,
                        success_rate = EXCLUDED.success_rate,
                        last_rotation_time = EXCLUDED.last_rotation_time,
                        last_fetch_time = EXCLUDED.last_fetch_time,
                        api_failure_count = EXCLUDED.api_failure_count,
                        updated_at = EXCLUDED.updated_at
                """

                await conn.execute(
                    query,
                    status.market,
                    status.mode.value,
                    status.is_running,
                    status.active_pool,
                    status.pool_a_size,
                    status.pool_b_size,
                    status.total_requests,
                    status.success_count,
                    status.failure_count,
                    status.success_rate,
                    status.last_rotation_at,  # 映射到 last_rotation_time
                    None,  # last_fetch_time (数据库有这个字段但domain model没有)
                    0,  # api_failure_count (数据库有这个字段但domain model没有)
                    datetime.now(),  # created_at
                    status.updated_at or datetime.now(),
                )

                return True
        except Exception as e:
            self.logger.error(f"Failed to save status: {e}")
            return False

    async def update_pool_stats(
        self,
        market: str,
        mode: ProxyPoolMode,
        active_pool: str,
        pool_a_size: int,
        pool_b_size: int,
    ) -> bool:
        """更新池统计信息"""
        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                query = """
                    UPDATE proxy_pool_status
                    SET active_pool = $1, pool_a_size = $2, pool_b_size = $3, updated_at = $4
                    WHERE market = $5 AND mode = $6
                """

                result = await conn.execute(
                    query,
                    active_pool,
                    pool_a_size,
                    pool_b_size,
                    datetime.now(),
                    market,
                    mode.value,
                )

                if result == "UPDATE 1":
                    return True
                else:
                    # If no record exists, create one
                    status = ProxyPoolStatus(
                        market=market,
                        mode=mode,
                        active_pool=active_pool,
                        pool_a_size=pool_a_size,
                        pool_b_size=pool_b_size,
                    )
                    return await self.save_status(status)

        except Exception as e:
            self.logger.error(f"Failed to update pool stats: {e}")
            return False

    async def increment_request_stats(
        self, market: str, mode: ProxyPoolMode, success: bool
    ) -> bool:
        """增加请求统计"""
        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                # Get current stats
                current_status = await self.get_status(market, mode)

                # Update stats
                new_total = current_status.total_requests + 1
                if success:
                    new_success = current_status.success_count + 1
                    new_failure = current_status.failure_count
                else:
                    new_success = current_status.success_count
                    new_failure = current_status.failure_count + 1

                # Calculate new success rate
                new_success_rate = (new_success / new_total * 100) if new_total > 0 else 0.0

                query = """
                    UPDATE proxy_pool_status
                    SET total_requests = $1, success_count = $2, failure_count = $3,
                        success_rate = $4, updated_at = $5
                    WHERE market = $6 AND mode = $7
                """

                result = await conn.execute(
                    query,
                    new_total,
                    new_success,
                    new_failure,
                    new_success_rate,
                    datetime.now(),
                    market,
                    mode.value,
                )

                return result == "UPDATE 1"

        except Exception as e:
            self.logger.error(f"Failed to increment request stats: {e}")
            return False

    async def update_status(self, market: str, mode: ProxyPoolMode, **kwargs) -> bool:
        """更新状态"""
        if not kwargs:
            return False

        pool = await get_db_pool()

        try:
            async with pool.acquire() as conn:
                # 构建动态更新语句
                set_clauses = []
                values = []
                param_count = 1

                for field, value in kwargs.items():
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1

                # 添加 updated_at
                set_clauses.append(f"updated_at = ${param_count}")
                values.append(datetime.now())
                param_count += 1

                # 添加 WHERE 条件的参数
                values.extend([market, mode.value])

                query = f"""
                    UPDATE proxy_pool_status
                    SET {", ".join(set_clauses)}
                    WHERE market = ${param_count} AND mode = ${param_count + 1}
                """

                result = await conn.execute(query, *values)

                return result == "UPDATE 1"

        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
            return False
