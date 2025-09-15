"""
Infrastructure层 - 市场时钟实现
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

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