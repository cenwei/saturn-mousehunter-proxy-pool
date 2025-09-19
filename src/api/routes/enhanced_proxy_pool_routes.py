"""
增强的代理池API路由 - 支持全日/半日交易模式
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from saturn_mousehunter_shared import get_logger

# 新增增强调度器相关接口
router_enhanced = APIRouter(tags=["enhanced_proxy_pool"], prefix="/enhanced")
log = get_logger("enhanced_proxy_pool_routes")


class TradingDayRequest(BaseModel):
    """交易日查询请求"""
    market: str
    date: Optional[str] = None  # YYYY-MM-DD format


class TradingModeResponse(BaseModel):
    """交易模式响应"""
    market: str
    date: str
    day_type: str
    session_type: str
    is_trading_day: bool
    status_description: str
    trading_hours: Optional[Dict[str, Any]] = None


def get_enhanced_global_scheduler():
    """获取增强全局调度器依赖"""
    from infrastructure.dependencies import get_enhanced_global_scheduler as get_scheduler
    return get_scheduler()


def get_enhanced_market_clock():
    """获取增强市场时钟依赖"""
    from infrastructure.dependencies import get_enhanced_market_clock as get_clock
    return get_clock()


# ========== 增强调度管理接口 ==========


@router_enhanced.get("/scheduler/status")
async def get_enhanced_scheduler_status(scheduler=Depends(get_enhanced_global_scheduler)):
    """获取增强调度器状态，包含交易日类型信息"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Enhanced global scheduler not available")

    try:
        status = await scheduler.get_enhanced_schedule_status()
        return status
    except Exception as e:
        log.error(f"Failed to get enhanced scheduler status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get enhanced scheduler status: {str(e)}"
        )


@router_enhanced.post("/scheduler/force-start/{market}")
async def force_start_market_enhanced(
    market: str,
    scheduler=Depends(get_enhanced_global_scheduler)
):
    """强制启动市场（增强版本，包含交易日类型信息）"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Enhanced global scheduler not available")

    try:
        result = await scheduler.force_start_market(market.lower())
        return result
    except Exception as e:
        log.error(f"Failed to force start market {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to force start market: {str(e)}"
        )


@router_enhanced.post("/scheduler/force-stop/{market}")
async def force_stop_market_enhanced(
    market: str,
    scheduler=Depends(get_enhanced_global_scheduler)
):
    """强制停止市场（增强版本，包含交易日类型信息）"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Enhanced global scheduler not available")

    try:
        result = await scheduler.force_stop_market(market.lower())
        return result
    except Exception as e:
        log.error(f"Failed to force stop market {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to force stop market: {str(e)}"
        )


# ========== 交易日类型查询接口 ==========


@router_enhanced.get("/trading-day/{market}")
async def get_trading_day_info(
    market: str,
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)，默认为今天"),
    market_clock=Depends(get_enhanced_market_clock)
):
    """获取指定市场和日期的交易日信息"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    try:
        # 解析日期
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # 获取交易日信息
        trading_summary = market_clock.get_trading_summary(market.lower(), target_date)

        return TradingModeResponse(**trading_summary)

    except Exception as e:
        log.error(f"Failed to get trading day info for {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading day info: {str(e)}"
        )


@router_enhanced.get("/trading-day/{market}/status")
async def get_current_market_status(
    market: str,
    market_clock=Depends(get_enhanced_market_clock)
):
    """获取市场当前状态（实时）"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    try:
        now = market_clock.market_now(market.lower())
        trading_summary = market_clock.get_trading_summary(market.lower(), now)

        # 添加实时判断
        is_open = market_clock.is_market_open(market.lower(), now)
        should_start = market_clock.should_start_trading_session_enhanced(market.lower())
        should_stop = market_clock.should_stop_trading_session_enhanced(market.lower())

        return {
            **trading_summary,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "is_market_open": is_open,
            "should_start_session": should_start,
            "should_stop_session": should_stop
        }

    except Exception as e:
        log.error(f"Failed to get current market status for {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get current market status: {str(e)}"
        )


@router_enhanced.get("/trading-modes/summary")
async def get_all_markets_trading_summary(
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)，默认为今天"),
    market_clock=Depends(get_enhanced_market_clock)
):
    """获取所有市场的交易日信息总结"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    try:
        # 解析日期
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # 获取所有支持的市场
        markets = ["cn", "hk", "us"]  # 可以从配置中读取
        summaries = {}

        for market in markets:
            try:
                trading_summary = market_clock.get_trading_summary(market, target_date)
                summaries[market] = trading_summary
            except Exception as e:
                log.warning(f"Failed to get trading summary for {market}: {e}")
                summaries[market] = {
                    "error": str(e),
                    "market": market.upper(),
                    "date": (target_date or datetime.now()).strftime("%Y-%m-%d")
                }

        return {
            "date": (target_date or datetime.now()).strftime("%Y-%m-%d"),
            "markets": summaries
        }

    except Exception as e:
        log.error(f"Failed to get trading summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading summary: {str(e)}"
        )


# ========== MACL数据集成接口 ==========


@router_enhanced.get("/macl/day-type/{market}")
async def get_macl_day_type(
    market: str,
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)，默认为今天"),
    market_clock=Depends(get_enhanced_market_clock)
):
    """基于MACL逻辑获取交易日类型"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    try:
        # 解析日期
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # 获取MACL判断结果
        day_type = market_clock.get_trading_day_type_from_macl(market.lower(), target_date)
        session_type = market_clock.get_trading_session_type(market.lower(), target_date)

        # 获取交易时间
        trading_hours = None
        if day_type.value in ["NORMAL", "HALF_DAY"]:
            start_time, end_time, lunch_break = market_clock.get_enhanced_trading_hours(
                market.lower(), target_date
            )
            trading_hours = {
                "start": start_time,
                "end": end_time,
                "lunch_break": lunch_break
            }

        return {
            "market": market.upper(),
            "date": (target_date or datetime.now()).strftime("%Y-%m-%d"),
            "day_type": day_type.value,
            "session_type": session_type.value,
            "is_trading_day": day_type.value in ["NORMAL", "HALF_DAY"],
            "trading_hours": trading_hours,
            "data_source": "macl"
        }

    except Exception as e:
        log.error(f"Failed to get MACL day type for {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get MACL day type: {str(e)}"
        )


@router_enhanced.get("/macl/should-operate/{market}")
async def get_macl_operation_decision(
    market: str,
    operation: str = Query(..., description="操作类型: start/stop"),
    market_clock=Depends(get_enhanced_market_clock)
):
    """基于MACL逻辑判断是否应该执行操作（启动/停止）"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    if operation not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="Operation must be 'start' or 'stop'")

    try:
        now = market_clock.market_now(market.lower())

        if operation == "start":
            should_operate = market_clock.should_start_trading_session_enhanced(market.lower())
            operation_desc = "启动代理池"
        else:
            should_operate = market_clock.should_stop_trading_session_enhanced(market.lower())
            operation_desc = "停止代理池"

        # 获取当前交易日信息
        trading_summary = market_clock.get_trading_summary(market.lower(), now)

        return {
            "market": market.upper(),
            "operation": operation,
            "should_operate": should_operate,
            "operation_description": operation_desc,
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "trading_info": trading_summary,
            "data_source": "macl"
        }

    except Exception as e:
        log.error(f"Failed to get MACL operation decision for {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get MACL operation decision: {str(e)}"
        )


# ========== 兼容性接口 ==========


@router_enhanced.get("/compatibility/trading-hours/{market}")
async def get_compatible_trading_hours(
    market: str,
    date: Optional[str] = Query(None, description="日期 (YYYY-MM-DD)，默认为今天"),
    market_clock=Depends(get_enhanced_market_clock)
):
    """获取交易时间（兼容原接口格式）"""
    if not market_clock:
        raise HTTPException(status_code=503, detail="Enhanced market clock not available")

    try:
        # 解析日期
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

        # 获取增强的交易时间
        start_time, end_time, lunch_break = market_clock.get_enhanced_trading_hours(
            market.lower(), target_date
        )

        return {
            "market": market.upper(),
            "date": (target_date or datetime.now()).strftime("%Y-%m-%d"),
            "start_time": start_time,
            "end_time": end_time,
            "lunch_break": lunch_break,
            "format": "enhanced_with_day_type_support"
        }

    except Exception as e:
        log.error(f"Failed to get compatible trading hours for {market}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get trading hours: {str(e)}"
        )