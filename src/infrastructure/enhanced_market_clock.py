"""
增强市场时钟服务 - 集成交易日类型支持
支持全日交易和半日交易的代理池管理
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Optional, Tuple, Dict, Any
from enum import Enum

from saturn_mousehunter_shared import get_logger
from domain.entities import IMarketClock
from .market_clock import MarketClockService

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False


class TradingDayType(Enum):
    """交易日类型"""
    NORMAL = "NORMAL"          # 正常全日交易
    HALF_DAY = "HALF_DAY"      # 半日交易
    HOLIDAY = "HOLIDAY"        # 假期，不交易
    WEEKEND = "WEEKEND"        # 周末，不交易


class TradingSessionType(Enum):
    """交易时段类型"""
    FULL_DAY = "full_day"      # 全日交易
    MORNING_ONLY = "morning_only"   # 仅上午交易 (半日)
    AFTERNOON_ONLY = "afternoon_only" # 仅下午交易 (半日)


class EnhancedMarketClockService(MarketClockService):
    """增强的市场时钟服务 - 支持交易日类型判断"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger("enhanced_market_clock")

        # 半日交易时间配置
        self.half_day_trading_hours = {
            "cn": {
                "morning_only": ("09:30", "11:30"),  # 中国半日：仅上午
                "afternoon_only": ("13:00", "15:00")  # 中国半日：仅下午
            },
            "hk": {
                "morning_only": ("09:30", "12:00"),  # 香港半日：仅上午
                "afternoon_only": ("13:00", "16:00")  # 香港半日：仅下午（实际很少用）
            },
            "us": {
                "morning_only": ("09:30", "13:00"),  # 美股半日：仅上半段
                "afternoon_only": ("13:00", "16:00")  # 美股半日：仅下半段
            }
        }

    def get_trading_day_type_from_macl(self, market: str, date: Optional[datetime] = None) -> TradingDayType:
        """
        从MACL数据判断交易日类型
        这是当前可用的MACL逻辑，后续可扩展为读取交易日历数据库
        """
        date = date or self.market_now(market)
        weekday = date.weekday()

        # 周末判断
        if weekday >= 5:  # Saturday=5, Sunday=6
            return TradingDayType.WEEKEND

        # TODO: 这里后续集成交易日历数据库
        # 目前使用简化的MACL逻辑判断特殊日期

        # 简化的半日交易判断 (基于MACL已有逻辑)
        if self._is_half_day_by_macl(market, date):
            return TradingDayType.HALF_DAY

        # 简化的假期判断 (基于MACL已有逻辑)
        if self._is_holiday_by_macl(market, date):
            return TradingDayType.HOLIDAY

        # 默认为正常交易日
        return TradingDayType.NORMAL

    def _is_half_day_by_macl(self, market: str, date: datetime) -> bool:
        """
        基于MACL逻辑判断是否为半日交易
        这里可以扩展具体的半日交易日期判断逻辑
        """
        market = market.lower()

        # 简化示例：一些常见的半日交易日期判断
        month_day = date.strftime("%m-%d")

        if market == "hk":
            # 香港常见半日交易：平安夜、除夕等
            half_day_dates = ["12-24", "12-31"]  # 平安夜、除夕
            return month_day in half_day_dates

        elif market == "us":
            # 美股常见半日交易：感恩节后、平安夜等
            half_day_dates = ["11-29", "12-24"]  # 感恩节后、平安夜（示例）
            return month_day in half_day_dates

        elif market == "cn":
            # 中国市场半日交易较少，主要在一些特殊调整日
            # 这里可以根据实际情况扩展
            return False

        return False

    def _is_holiday_by_macl(self, market: str, date: datetime) -> bool:
        """
        基于MACL逻辑判断是否为假期
        这里可以扩展具体的假期判断逻辑
        """
        # 这里可以实现更复杂的假期判断逻辑
        # 目前返回False，表示使用基础的is_trading_day逻辑
        return False

    def get_trading_session_type(self, market: str, date: Optional[datetime] = None) -> TradingSessionType:
        """获取交易时段类型"""
        day_type = self.get_trading_day_type_from_macl(market, date)

        if day_type == TradingDayType.NORMAL:
            return TradingSessionType.FULL_DAY
        elif day_type == TradingDayType.HALF_DAY:
            # 半日交易默认为上午，具体可以根据市场和日期进一步判断
            return self._determine_half_day_session(market, date)
        else:
            # 假期和周末不交易，但返回默认值
            return TradingSessionType.FULL_DAY

    def _determine_half_day_session(self, market: str, date: Optional[datetime] = None) -> TradingSessionType:
        """确定半日交易是上午还是下午"""
        market = market.lower()
        date = date or self.market_now(market)

        # 默认半日交易为上午交易
        # 这里可以根据具体市场和日期进行更精确的判断
        if market == "hk":
            # 香港半日交易通常是上午
            return TradingSessionType.MORNING_ONLY
        elif market == "us":
            # 美股半日交易通常是上午到中午
            return TradingSessionType.MORNING_ONLY
        elif market == "cn":
            # 中国市场根据具体情况
            return TradingSessionType.MORNING_ONLY

        return TradingSessionType.MORNING_ONLY

    def get_enhanced_trading_hours(self, market: str, date: Optional[datetime] = None) -> Tuple[str, str, Optional[Tuple[str, str]]]:
        """
        获取增强的交易时间，支持交易日类型
        返回: (开盘时间, 收盘时间, 午休时间段或None)
        """
        session_type = self.get_trading_session_type(market, date)
        market = market.lower()

        if session_type == TradingSessionType.FULL_DAY:
            # 使用父类的全日交易时间
            return super().get_market_trading_hours(market)

        elif session_type == TradingSessionType.MORNING_ONLY:
            # 半日交易 - 仅上午
            if market in self.half_day_trading_hours:
                start, end = self.half_day_trading_hours[market]["morning_only"]
                return (start, end, None)  # 半日交易没有午休
            else:
                # 回退到全日交易时间
                return super().get_market_trading_hours(market)

        elif session_type == TradingSessionType.AFTERNOON_ONLY:
            # 半日交易 - 仅下午
            if market in self.half_day_trading_hours:
                start, end = self.half_day_trading_hours[market]["afternoon_only"]
                return (start, end, None)  # 半日交易没有午休
            else:
                # 回退到全日交易时间
                return super().get_market_trading_hours(market)

        # 默认回退
        return super().get_market_trading_hours(market)

    def is_trading_day_enhanced(self, market: str, date: Optional[datetime] = None) -> bool:
        """增强的交易日判断，考虑交易日类型"""
        day_type = self.get_trading_day_type_from_macl(market, date)
        return day_type in [TradingDayType.NORMAL, TradingDayType.HALF_DAY]

    def get_enhanced_market_status_desc(self, market: str, t: Optional[datetime] = None) -> str:
        """获取增强的市场状态描述，包含交易日类型信息"""
        t = t or self.market_now(market)
        day_type = self.get_trading_day_type_from_macl(market, t)
        session_type = self.get_trading_session_type(market, t)

        # 基础状态描述
        base_desc = super().get_market_status_desc(market, t)

        # 添加交易日类型信息
        if day_type == TradingDayType.HALF_DAY:
            session_desc = {
                TradingSessionType.MORNING_ONLY: "半日交易(仅上午)",
                TradingSessionType.AFTERNOON_ONLY: "半日交易(仅下午)",
                TradingSessionType.FULL_DAY: "半日交易"
            }.get(session_type, "半日交易")

            return f"{base_desc} - {session_desc}"
        elif day_type == TradingDayType.HOLIDAY:
            return f"{base_desc} - 假期"
        elif day_type == TradingDayType.WEEKEND:
            return f"{base_desc} - 周末"
        else:
            return f"{base_desc} - 正常交易日"

    def should_start_trading_session_enhanced(self, market: str, pre_minutes: int = 2) -> bool:
        """增强的交易时段启动判断，考虑交易日类型"""
        now = self.market_now(market)

        # 使用增强的交易日判断
        if not self.is_trading_day_enhanced(market, now):
            return False

        # 获取增强的交易时间
        start_time, _, _ = self.get_enhanced_trading_hours(market, now)

        # 计算启动时间
        try:
            market_open = datetime.strptime(
                f"{now.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M"
            )

            pre_start = market_open - timedelta(minutes=pre_minutes)

            # 比较时间
            now_time = now.strftime("%H:%M")
            pre_time = pre_start.strftime("%H:%M")

            return now_time >= pre_time

        except Exception as e:
            self.logger.error(f"Error checking enhanced start condition: {e}")
            # 回退到基础逻辑
            return super().should_start_trading_session(market, pre_minutes)

    def should_stop_trading_session_enhanced(self, market: str, post_minutes: int = 30) -> bool:
        """增强的交易时段停止判断，考虑交易日类型"""
        now = self.market_now(market)

        # 非交易日应该停止
        if not self.is_trading_day_enhanced(market, now):
            return True

        # 获取增强的交易时间
        _, end_time, _ = self.get_enhanced_trading_hours(market, now)

        # 计算停止时间
        try:
            market_close = datetime.strptime(
                f"{now.strftime('%Y-%m-%d')} {end_time}", "%Y-%m-%d %H:%M"
            )

            post_stop = market_close + timedelta(minutes=post_minutes)

            # 比较时间
            now_time = now.strftime("%H:%M")
            post_time = post_stop.strftime("%H:%M")

            return now_time >= post_time

        except Exception as e:
            self.logger.error(f"Error checking enhanced stop condition: {e}")
            # 回退到基础逻辑
            return super().should_stop_trading_session(market, post_minutes)

    def get_trading_summary(self, market: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        """获取交易日信息总结"""
        date = date or self.market_now(market)
        day_type = self.get_trading_day_type_from_macl(market, date)
        session_type = self.get_trading_session_type(market, date)

        summary = {
            "market": market.upper(),
            "date": date.strftime("%Y-%m-%d"),
            "day_type": day_type.value,
            "session_type": session_type.value,
            "is_trading_day": self.is_trading_day_enhanced(market, date),
            "status_description": self.get_enhanced_market_status_desc(market, date)
        }

        if summary["is_trading_day"]:
            start_time, end_time, lunch_break = self.get_enhanced_trading_hours(market, date)
            summary.update({
                "trading_hours": {
                    "start": start_time,
                    "end": end_time,
                    "lunch_break": lunch_break
                }
            })

        return summary

    # 保持与父类兼容的方法，但使用增强逻辑
    def is_trading_day(self, market: str, date: Optional[datetime] = None) -> bool:
        """重写父类方法，使用增强逻辑"""
        return self.is_trading_day_enhanced(market, date)

    def should_start_trading_session(self, market: str, pre_minutes: int = 2) -> bool:
        """重写父类方法，使用增强逻辑"""
        return self.should_start_trading_session_enhanced(market, pre_minutes)

    def should_stop_trading_session(self, market: str, post_minutes: int = 30) -> bool:
        """重写父类方法，使用增强逻辑"""
        return self.should_stop_trading_session_enhanced(market, post_minutes)