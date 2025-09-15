"""
Infrastructure层 - 市场时钟实现
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple

from saturn_mousehunter_shared import get_logger
from domain import IMarketClock

try:
    from zoneinfo import ZoneInfo
    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False


class MarketClockService(IMarketClock):
    """市场时钟服务实现"""

    # 市场时区映射
    MARKET_TZ = {
        "cn": "Asia/Shanghai",
        "hk": "Asia/Hong_Kong",
        "us": "America/New_York",
        "sg": "Asia/Singapore",
        "jp": "Asia/Tokyo",
        "kr": "Asia/Seoul",
        "uk": "Europe/London",
        "eu": "Europe/Berlin"
    }

    def __init__(self):
        self.logger = get_logger("market_clock")

    def market_now(self, market: str) -> datetime:
        """获取市场当前时间"""
        if not HAS_ZONEINFO:
            return datetime.now()

        tz_name = self.MARKET_TZ.get(market.lower(), "UTC")
        try:
            tz = ZoneInfo(tz_name)
            return datetime.now(tz)
        except Exception:
            return datetime.now()

    def is_market_open(self, market: str, t: Optional[datetime] = None) -> bool:
        """判断市场是否开盘"""
        t = t or self.market_now(market)
        hhmm = t.strftime("%H:%M")

        market = market.lower()
        if market == "us":
            return "09:30" <= hhmm <= "16:00"
        elif market == "hk":
            return ("09:30" <= hhmm <= "12:00") or ("13:00" <= hhmm <= "16:15")
        elif market == "cn":
            return ("09:30" <= hhmm <= "11:30") or ("13:00" <= hhmm <= "15:10")
        else:
            # 其他市场默认开盘
            return True

    def get_market_status_desc(self, market: str, t: Optional[datetime] = None) -> str:
        """获取市场状态描述"""
        t = t or self.market_now(market)
        hhmm = t.strftime("%H:%M")

        if self.is_market_open(market, t):
            return f"市场开盘中 ({hhmm})"

        market = market.lower()
        if market == "hk" and "12:00" < hhmm < "13:00":
            return f"午休时间 ({hhmm})"
        elif market == "cn" and "11:30" < hhmm < "13:00":
            return f"午休时间 ({hhmm})"
        else:
            return f"已收盘 ({hhmm})"

    def should_terminate_after_close(self, market: str, t: Optional[datetime] = None) -> bool:
        """判断是否应该在收盘后终止"""
        t = t or self.market_now(market)
        hhmm = t.strftime("%H:%M")

        market = market.lower()
        if market == "cn":
            return hhmm >= "15:05"
        elif market in ("hk", "us"):
            return hhmm >= "16:20"
        else:
            return False

    def is_trading_day(self, market: str, date: Optional[datetime] = None) -> bool:
        """判断是否为交易日（简化版本，实际应查询交易日历）"""
        date = date or self.market_now(market)
        weekday = date.weekday()

        # 排除周末
        if weekday >= 5:  # Saturday=5, Sunday=6
            return False

        # TODO: 这里应该查询具体的交易日历数据库，排除节假日
        # 目前简化为只排除周末
        return True

    def get_market_trading_hours(self, market: str) -> Tuple[str, str, Optional[Tuple[str, str]]]:
        """
        获取市场交易时间
        返回: (开盘时间, 收盘时间, 午休时间段或None)
        """
        market = market.lower()
        if market == "us":
            return ("09:30", "16:00", None)
        elif market == "hk":
            return ("09:30", "16:15", ("12:00", "13:00"))
        elif market == "cn":
            return ("09:30", "15:10", ("11:30", "13:00"))
        else:
            # 其他市场默认24小时
            return ("00:00", "23:59", None)

    def get_pre_market_start_time(self, market: str, pre_minutes: int = 30,
                                 date: Optional[datetime] = None) -> Optional[datetime]:
        """获取盘前启动时间"""
        date = date or self.market_now(market)

        if not self.is_trading_day(market, date):
            return None

        start_time, _, _ = self.get_market_trading_hours(market)
        market_tz = self._get_market_timezone(market)

        try:
            # 构建开盘时间
            open_time = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {start_time}", "%Y-%m-%d %H:%M")
            if HAS_ZONEINFO and market_tz:
                open_time = open_time.replace(tzinfo=market_tz)

            # 减去提前启动时间
            pre_start = open_time - timedelta(minutes=pre_minutes)
            return pre_start
        except Exception as e:
            self.logger.error(f"Error calculating pre-market start time: {e}")
            return None

    def get_post_market_stop_time(self, market: str, post_minutes: int = 30,
                                 date: Optional[datetime] = None) -> Optional[datetime]:
        """获取盘后停止时间"""
        date = date or self.market_now(market)

        if not self.is_trading_day(market, date):
            return None

        _, end_time, _ = self.get_market_trading_hours(market)
        market_tz = self._get_market_timezone(market)

        try:
            # 构建收盘时间
            close_time = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {end_time}", "%Y-%m-%d %H:%M")
            if HAS_ZONEINFO and market_tz:
                close_time = close_time.replace(tzinfo=market_tz)

            # 增加延后停止时间
            post_stop = close_time + timedelta(minutes=post_minutes)
            return post_stop
        except Exception as e:
            self.logger.error(f"Error calculating post-market stop time: {e}")
            return None

    def should_start_trading_session(self, market: str, pre_minutes: int = 30) -> bool:
        """判断是否应该开始交易时段"""
        now = self.market_now(market)

        if not self.is_trading_day(market, now):
            return False

        pre_start = self.get_pre_market_start_time(market, pre_minutes, now)
        if not pre_start:
            return False

        # 移除时区信息进行比较（如果都有时区）
        if hasattr(now, 'tzinfo') and hasattr(pre_start, 'tzinfo'):
            return now >= pre_start
        else:
            # 简化比较，只比较时间部分
            now_time = now.strftime("%H:%M")
            pre_time = pre_start.strftime("%H:%M")
            return now_time >= pre_time

    def should_stop_trading_session(self, market: str, post_minutes: int = 30) -> bool:
        """判断是否应该停止交易时段"""
        now = self.market_now(market)

        if not self.is_trading_day(market, now):
            return True

        post_stop = self.get_post_market_stop_time(market, post_minutes, now)
        if not post_stop:
            return True

        # 移除时区信息进行比较（如果都有时区）
        if hasattr(now, 'tzinfo') and hasattr(post_stop, 'tzinfo'):
            return now >= post_stop
        else:
            # 简化比较，只比较时间部分
            now_time = now.strftime("%H:%M")
            post_time = post_stop.strftime("%H:%M")
            return now_time >= post_time

    def _get_market_timezone(self, market: str) -> Optional[ZoneInfo]:
        """获取市场时区对象"""
        if not HAS_ZONEINFO:
            return None

        tz_name = self.MARKET_TZ.get(market.lower(), "UTC")
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return None