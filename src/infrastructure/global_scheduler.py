"""
Infrastructure层 - 全局调度器
"""

import asyncio
from typing import Dict, Optional

from saturn_mousehunter_shared import get_logger
from domain.config_entities import ProxyPoolMode, IProxyPoolConfigRepository
from .market_clock import MarketClockService
from .postgresql_repositories import PostgreSQLProxyPoolConfigRepository


class GlobalScheduler:
    """全局调度器 - 管理所有市场的自动启停"""

    def __init__(self, get_manager_func):
        """
        初始化全局调度器

        Args:
            get_manager_func: 获取代理池管理器的函数
        """
        self.get_manager_func = get_manager_func
        self.market_clock = MarketClockService()
        self.config_repo: IProxyPoolConfigRepository = (
            PostgreSQLProxyPoolConfigRepository()
        )
        self.logger = get_logger("global_scheduler")

        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._market_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """启动全局调度器"""
        if self._running:
            self.logger.warning("Global scheduler already running")
            return

        self.logger.info("Starting global scheduler")
        self._running = True

        # 启动主调度循环
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

        self.logger.info("Global scheduler started")

    async def stop(self):
        """停止全局调度器"""
        if not self._running:
            return

        self.logger.info("Stopping global scheduler")
        self._running = False

        # 取消主调度任务
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        # 取消所有市场任务
        for market, task in self._market_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._market_tasks.clear()
        self.logger.info("Global scheduler stopped")

    async def _scheduler_loop(self):
        """主调度循环"""
        try:
            while self._running:
                try:
                    # 获取所有激活的配置
                    configs = await self.config_repo.get_all_active_configs()

                    for config in configs:
                        if (
                            config.mode == ProxyPoolMode.LIVE
                            and config.auto_start_enabled
                        ):
                            await self._check_market_schedule(config.market, config)

                    # 每分钟检查一次
                    await asyncio.sleep(60)

                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {e}")
                    await asyncio.sleep(60)  # 出错后等待1分钟再重试

        except asyncio.CancelledError:
            self.logger.info("Scheduler loop cancelled")

    async def _check_market_schedule(self, market: str, config):
        """检查市场调度"""
        try:
            # 先检查管理器是否存在，避免不必要的市场时间计算
            try:
                manager = self.get_manager_func(market, "live")
            except ValueError:
                # 只在首次检查时记录调试信息，避免重复日志
                self.logger.debug(f"No manager configured for market {market.upper()}, skipping schedule check")
                return

            # 检查是否应该启动
            should_start = self.market_clock.should_start_trading_session(
                market, config.pre_market_start_minutes
            )

            # 检查是否应该停止
            should_stop = self.market_clock.should_stop_trading_session(
                market, config.post_market_stop_minutes
            )

            current_running = manager.is_running

            # 决定操作
            if should_start and not current_running:
                await self._start_market_with_logging(market, manager, config)
            elif should_stop and current_running:
                # 检查是否是手动启动的，如果是则不自动停止
                if not getattr(manager, '_manually_started', False):
                    await self._stop_market_with_logging(market, manager, config)
                else:
                    self.logger.debug(
                        f"Market {market.upper()} is manually started, skipping auto-stop"
                    )
            elif current_running:
                # 如果正在运行，记录下次停止时间
                await self._log_next_stop_time(market, config)

        except Exception as e:
            self.logger.error(f"Error checking schedule for market {market}: {e}")

    async def _start_market_with_logging(self, market: str, manager, config):
        """启动市场并记录日志"""
        try:
            self.logger.info(
                f"🚀 Starting market {market.upper()} - trading session begins"
            )
            await manager.start()

            # 记录成功启动
            self.logger.info(f"✅ Market {market.upper()} started successfully")

            # 记录预期的停止时间
            await self._log_next_stop_time(market, config)

        except Exception as e:
            self.logger.error(f"❌ Failed to start market {market.upper()}: {e}")

    async def _stop_market_with_logging(self, market: str, manager, config):
        """停止市场并记录日志"""
        try:
            self.logger.info(
                f"🛑 Stopping market {market.upper()} - trading session ends"
            )
            await manager.stop()

            # 记录成功停止
            self.logger.info(f"✅ Market {market.upper()} stopped successfully")

            # 记录下次启动时间
            await self._log_next_start_time(market, config)

        except Exception as e:
            self.logger.error(f"❌ Failed to stop market {market.upper()}: {e}")

    async def _log_next_start_time(self, market: str, config):
        """记录下次启动时间"""
        try:
            next_start = self.market_clock.get_next_trading_start_time(
                market, config.pre_market_start_minutes
            )

            if next_start:
                time_until = self.market_clock.time_until_next_trading_session(
                    market, config.pre_market_start_minutes
                )

                if time_until:
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)

                    self.logger.info(
                        f"📅 Market {market.upper()} next start: {next_start.strftime('%Y-%m-%d %H:%M')} "
                        f"(in {hours}h {minutes}m)"
                    )

        except Exception as e:
            self.logger.error(f"Error logging next start time for {market}: {e}")

    async def _log_next_stop_time(self, market: str, config):
        """记录下次停止时间"""
        try:
            now = self.market_clock.market_now(market)
            stop_time = self.market_clock.get_post_market_stop_time(
                market, config.post_market_stop_minutes, now
            )

            if stop_time:
                time_until = stop_time - now
                if hasattr(now, "tzinfo") and hasattr(stop_time, "tzinfo"):
                    time_until = stop_time - now
                else:
                    # 简化计算
                    now_naive = (
                        now.replace(tzinfo=None) if hasattr(now, "tzinfo") else now
                    )
                    stop_naive = (
                        stop_time.replace(tzinfo=None)
                        if hasattr(stop_time, "tzinfo")
                        else stop_time
                    )
                    time_until = stop_naive - now_naive

                if time_until.total_seconds() > 0:
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)

                    self.logger.info(
                        f"⏰ Market {market.upper()} will stop at: {stop_time.strftime('%Y-%m-%d %H:%M')} "
                        f"(in {hours}h {minutes}m)"
                    )

        except Exception as e:
            self.logger.error(f"Error logging next stop time for {market}: {e}")

    async def get_schedule_status(self) -> dict:
        """获取调度状态"""
        try:
            configs = await self.config_repo.get_all_active_configs()
            status = {"scheduler_running": self._running, "markets": {}}

            for config in configs:
                if config.mode == ProxyPoolMode.LIVE:
                    market = config.market

                    # 获取管理器状态
                    try:
                        manager = self.get_manager_func(market, "live")
                        is_running = manager.is_running
                    except ValueError:
                        is_running = False

                    # 计算下次启动/停止时间
                    next_start = self.market_clock.get_next_trading_start_time(
                        market, config.pre_market_start_minutes
                    )

                    now = self.market_clock.market_now(market)
                    next_stop = (
                        self.market_clock.get_post_market_stop_time(
                            market, config.post_market_stop_minutes, now
                        )
                        if is_running
                        else None
                    )

                    status["markets"][market] = {
                        "running": is_running,
                        "auto_start_enabled": config.auto_start_enabled,
                        "pre_market_minutes": config.pre_market_start_minutes,
                        "post_market_minutes": config.post_market_stop_minutes,
                        "next_start": next_start.isoformat() if next_start else None,
                        "next_stop": next_stop.isoformat() if next_stop else None,
                        "is_trading_day": self.market_clock.is_trading_day(market, now),
                        "market_status": self.market_clock.get_market_status_desc(
                            market, now
                        ),
                    }

            return status

        except Exception as e:
            self.logger.error(f"Error getting schedule status: {e}")
            return {"scheduler_running": self._running, "error": str(e)}

    async def force_start_market(self, market: str) -> dict:
        """强制启动市场"""
        try:
            manager = self.get_manager_func(market, "live")

            if manager.is_running:
                return {
                    "status": "already_running",
                    "message": f"Market {market} is already running",
                }

            await manager.start(force=True)
            # 标记为手动启动，防止自动停止
            manager._manually_started = True
            self.logger.info(f"🔧 Manually started market {market.upper()}")

            return {"status": "started", "message": f"Market {market} started manually"}

        except Exception as e:
            self.logger.error(f"Failed to force start market {market}: {e}")
            return {"status": "error", "message": str(e)}

    async def force_stop_market(self, market: str) -> dict:
        """强制停止市场"""
        try:
            manager = self.get_manager_func(market, "live")

            if not manager.is_running:
                return {
                    "status": "already_stopped",
                    "message": f"Market {market} is already stopped",
                }

            await manager.stop()
            self.logger.info(f"🔧 Manually stopped market {market.upper()}")

            return {"status": "stopped", "message": f"Market {market} stopped manually"}

        except Exception as e:
            self.logger.error(f"Failed to force stop market {market}: {e}")
            return {"status": "error", "message": str(e)}
