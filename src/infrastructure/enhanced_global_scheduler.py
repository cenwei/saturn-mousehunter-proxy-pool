"""
增强全局调度器 - 支持全日/半日交易模式的代理池管理
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from saturn_mousehunter_shared import get_logger
from domain.config_entities import ProxyPoolMode, IProxyPoolConfigRepository
from .enhanced_market_clock import EnhancedMarketClockService, TradingDayType, TradingSessionType
from .postgresql_repositories import PostgreSQLProxyPoolConfigRepository


class EnhancedGlobalScheduler:
    """增强的全局调度器 - 支持交易日类型感知的代理池管理"""

    def __init__(self, get_manager_func):
        """
        初始化增强全局调度器

        Args:
            get_manager_func: 获取代理池管理器的函数
        """
        self.get_manager_func = get_manager_func
        self.market_clock = EnhancedMarketClockService()  # 使用增强的市场时钟
        self.config_repo: IProxyPoolConfigRepository = (
            PostgreSQLProxyPoolConfigRepository()
        )
        self.logger = get_logger("enhanced_global_scheduler")

        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._market_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """启动增强全局调度器"""
        if self._running:
            self.logger.warning("Enhanced global scheduler already running")
            return

        self.logger.info("Starting enhanced global scheduler with trading day type support")
        self._running = True

        # 启动主调度循环
        self._scheduler_task = asyncio.create_task(self._enhanced_scheduler_loop())

        self.logger.info("Enhanced global scheduler started")

    async def stop(self):
        """停止增强全局调度器"""
        if not self._running:
            return

        self.logger.info("Stopping enhanced global scheduler")
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
        self.logger.info("Enhanced global scheduler stopped")

    async def _enhanced_scheduler_loop(self):
        """增强的调度循环"""
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
                            await self._check_enhanced_market_schedule(config.market, config)

                    # 每分钟检查一次
                    await asyncio.sleep(60)

                except Exception as e:
                    self.logger.error(f"Error in enhanced scheduler loop: {e}")
                    await asyncio.sleep(60)  # 出错后等待1分钟再重试

        except asyncio.CancelledError:
            self.logger.info("Enhanced scheduler loop cancelled")

    async def _check_enhanced_market_schedule(self, market: str, config):
        """检查增强的市场调度，支持交易日类型"""
        try:
            # 先检查管理器是否存在
            try:
                manager = self.get_manager_func(market, "live")
            except ValueError:
                self.logger.debug(f"No manager configured for market {market.upper()}, skipping enhanced schedule check")
                return

            # 获取交易日信息
            trading_summary = self.market_clock.get_trading_summary(market)
            day_type = TradingDayType(trading_summary["day_type"])
            session_type = TradingSessionType(trading_summary["session_type"])

            # 检查是否应该启动
            should_start = self.market_clock.should_start_trading_session_enhanced(
                market, config.pre_market_start_minutes
            )

            # 检查是否应该停止
            should_stop = self.market_clock.should_stop_trading_session_enhanced(
                market, config.post_market_stop_minutes
            )

            current_running = manager.is_running

            # 决定操作
            if should_start and not current_running:
                await self._start_market_with_enhanced_logging(market, manager, config, trading_summary)
            elif should_stop and current_running:
                await self._stop_market_with_enhanced_logging(market, manager, config, trading_summary)
            elif current_running:
                # 如果正在运行，记录下次停止时间
                await self._log_enhanced_next_stop_time(market, config, trading_summary)

        except Exception as e:
            self.logger.error(f"Error checking enhanced schedule for market {market}: {e}")

    async def _start_market_with_enhanced_logging(self, market: str, manager, config, trading_summary):
        """启动市场并记录增强的日志信息"""
        try:
            day_type = trading_summary["day_type"]
            session_type = trading_summary["session_type"]

            # 构建启动消息
            trading_mode = self._get_trading_mode_description(day_type, session_type)

            self.logger.info(
                f"🚀 Starting market {market.upper()} - {trading_mode} trading session begins"
            )

            # 记录交易时间信息
            if "trading_hours" in trading_summary:
                hours = trading_summary["trading_hours"]
                self.logger.info(
                    f"📋 {market.upper()} Trading hours: {hours['start']} - {hours['end']}"
                    + (f" (Lunch: {hours['lunch_break'][0]}-{hours['lunch_break'][1]})" if hours['lunch_break'] else "")
                )

            await manager.start()

            # 记录成功启动
            self.logger.info(f"✅ Market {market.upper()} started successfully ({trading_mode})")

            # 记录预期的停止时间
            await self._log_enhanced_next_stop_time(market, config, trading_summary)

        except Exception as e:
            self.logger.error(f"❌ Failed to start market {market.upper()}: {e}")

    async def _stop_market_with_enhanced_logging(self, market: str, manager, config, trading_summary):
        """停止市场并记录增强的日志信息"""
        try:
            day_type = trading_summary["day_type"]
            session_type = trading_summary["session_type"]

            trading_mode = self._get_trading_mode_description(day_type, session_type)

            self.logger.info(
                f"🛑 Stopping market {market.upper()} - {trading_mode} trading session ends"
            )

            await manager.stop()

            # 记录成功停止
            self.logger.info(f"✅ Market {market.upper()} stopped successfully ({trading_mode})")

            # 记录下次启动时间
            await self._log_enhanced_next_start_time(market, config)

        except Exception as e:
            self.logger.error(f"❌ Failed to stop market {market.upper()}: {e}")

    def _get_trading_mode_description(self, day_type: str, session_type: str) -> str:
        """获取交易模式描述"""
        if day_type == "HALF_DAY":
            if session_type == "morning_only":
                return "半日交易(仅上午)"
            elif session_type == "afternoon_only":
                return "半日交易(仅下午)"
            else:
                return "半日交易"
        elif day_type == "NORMAL":
            return "全日交易"
        else:
            return f"特殊交易({day_type})"

    async def _log_enhanced_next_start_time(self, market: str, config):
        """记录增强的下次启动时间信息"""
        try:
            # 查找下一个交易日
            now = self.market_clock.market_now(market)
            current_date = now.date()

            # 如果今天还有交易时段且还没开始，显示今天的
            if self.market_clock.is_trading_day_enhanced(market, now):
                if not self.market_clock.should_start_trading_session_enhanced(market, config.pre_market_start_minutes):
                    today_summary = self.market_clock.get_trading_summary(market, now)
                    trading_mode = self._get_trading_mode_description(
                        today_summary["day_type"],
                        today_summary["session_type"]
                    )

                    # 计算今天的启动时间
                    start_time, _, _ = self.market_clock.get_enhanced_trading_hours(market, now)
                    pre_start_time = (
                        datetime.strptime(f"{now.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M")
                        - timedelta(minutes=config.pre_market_start_minutes)
                    )

                    self.logger.info(
                        f"📅 Market {market.upper()} today start: {pre_start_time.strftime('%H:%M')} ({trading_mode})"
                    )
                    return

            # 查找下一个交易日
            for days_ahead in range(1, 8):
                future_date = current_date + timedelta(days=days_ahead)
                future_datetime = datetime.combine(future_date, now.time())

                if self.market_clock.is_trading_day_enhanced(market, future_datetime):
                    future_summary = self.market_clock.get_trading_summary(market, future_datetime)
                    trading_mode = self._get_trading_mode_description(
                        future_summary["day_type"],
                        future_summary["session_type"]
                    )

                    # 计算启动时间
                    start_time, _, _ = self.market_clock.get_enhanced_trading_hours(market, future_datetime)
                    pre_start_time = (
                        datetime.strptime(f"{future_date.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M")
                        - timedelta(minutes=config.pre_market_start_minutes)
                    )

                    time_until = pre_start_time - now.replace(tzinfo=None)
                    if time_until.total_seconds() > 0:
                        hours = int(time_until.total_seconds() // 3600)
                        minutes = int((time_until.total_seconds() % 3600) // 60)

                        self.logger.info(
                            f"📅 Market {market.upper()} next start: {pre_start_time.strftime('%Y-%m-%d %H:%M')} "
                            f"({trading_mode}, in {hours}h {minutes}m)"
                        )
                    break

        except Exception as e:
            self.logger.error(f"Error logging enhanced next start time for {market}: {e}")

    async def _log_enhanced_next_stop_time(self, market: str, config, trading_summary):
        """记录增强的下次停止时间信息"""
        try:
            now = self.market_clock.market_now(market)

            # 获取当日交易结束时间
            if "trading_hours" in trading_summary:
                end_time = trading_summary["trading_hours"]["end"]

                # 计算停止时间
                market_close = datetime.strptime(
                    f"{now.strftime('%Y-%m-%d')} {end_time}", "%Y-%m-%d %H:%M"
                )
                post_stop_time = market_close + timedelta(minutes=config.post_market_stop_minutes)

                time_until = post_stop_time - now.replace(tzinfo=None)
                if time_until.total_seconds() > 0:
                    hours = int(time_until.total_seconds() // 3600)
                    minutes = int((time_until.total_seconds() % 3600) // 60)

                    trading_mode = self._get_trading_mode_description(
                        trading_summary["day_type"],
                        trading_summary["session_type"]
                    )

                    self.logger.info(
                        f"⏰ Market {market.upper()} will stop at: {post_stop_time.strftime('%H:%M')} "
                        f"({trading_mode}, in {hours}h {minutes}m)"
                    )

        except Exception as e:
            self.logger.error(f"Error logging enhanced next stop time for {market}: {e}")

    async def get_enhanced_schedule_status(self) -> dict:
        """获取增强的调度状态"""
        try:
            configs = await self.config_repo.get_all_active_configs()
            status = {"scheduler_running": self._running, "enhanced_features": True, "markets": {}}

            for config in configs:
                if config.mode == ProxyPoolMode.LIVE:
                    market = config.market

                    # 获取管理器状态
                    try:
                        manager = self.get_manager_func(market, "live")
                        is_running = manager.is_running
                    except ValueError:
                        is_running = False

                    # 获取交易日信息
                    trading_summary = self.market_clock.get_trading_summary(market)

                    # 计算下次启动/停止时间
                    now = self.market_clock.market_now(market)

                    # 使用增强方法计算时间
                    should_start = self.market_clock.should_start_trading_session_enhanced(
                        market, config.pre_market_start_minutes
                    )
                    should_stop = self.market_clock.should_stop_trading_session_enhanced(
                        market, config.post_market_stop_minutes
                    )

                    status["markets"][market] = {
                        "running": is_running,
                        "auto_start_enabled": config.auto_start_enabled,
                        "pre_market_minutes": config.pre_market_start_minutes,
                        "post_market_minutes": config.post_market_stop_minutes,

                        # 增强字段
                        "trading_summary": trading_summary,
                        "should_start": should_start,
                        "should_stop": should_stop,
                        "trading_day_type": trading_summary["day_type"],
                        "session_type": trading_summary["session_type"],
                        "status_description": trading_summary["status_description"],

                        # 传统字段保持兼容
                        "is_trading_day": trading_summary["is_trading_day"],
                        "market_status": trading_summary["status_description"],
                    }

                    # 添加交易时间信息
                    if "trading_hours" in trading_summary:
                        status["markets"][market]["trading_hours"] = trading_summary["trading_hours"]

            return status

        except Exception as e:
            self.logger.error(f"Error getting enhanced schedule status: {e}")
            return {"scheduler_running": self._running, "enhanced_features": True, "error": str(e)}

    # 保持与原调度器兼容的方法
    async def get_schedule_status(self) -> dict:
        """获取调度状态（兼容性方法）"""
        return await self.get_enhanced_schedule_status()

    async def force_start_market(self, market: str) -> dict:
        """强制启动市场（增强版本）"""
        try:
            manager = self.get_manager_func(market, "live")

            if manager.is_running:
                return {
                    "status": "already_running",
                    "message": f"Market {market} is already running",
                }

            # 获取交易日信息
            trading_summary = self.market_clock.get_trading_summary(market)
            trading_mode = self._get_trading_mode_description(
                trading_summary["day_type"],
                trading_summary["session_type"]
            )

            await manager.start()
            self.logger.info(f"🔧 Manually started market {market.upper()} ({trading_mode})")

            return {
                "status": "started",
                "message": f"Market {market} started manually ({trading_mode})",
                "trading_info": trading_summary
            }

        except Exception as e:
            self.logger.error(f"Failed to force start market {market}: {e}")
            return {"status": "error", "message": str(e)}

    async def force_stop_market(self, market: str) -> dict:
        """强制停止市场（增强版本）"""
        try:
            manager = self.get_manager_func(market, "live")

            if not manager.is_running:
                return {
                    "status": "already_stopped",
                    "message": f"Market {market} is already stopped",
                }

            # 获取交易日信息
            trading_summary = self.market_clock.get_trading_summary(market)
            trading_mode = self._get_trading_mode_description(
                trading_summary["day_type"],
                trading_summary["session_type"]
            )

            await manager.stop()
            self.logger.info(f"🔧 Manually stopped market {market.upper()} ({trading_mode})")

            return {
                "status": "stopped",
                "message": f"Market {market} stopped manually ({trading_mode})",
                "trading_info": trading_summary
            }

        except Exception as e:
            self.logger.error(f"Failed to force stop market {market}: {e}")
            return {"status": "error", "message": str(e)}