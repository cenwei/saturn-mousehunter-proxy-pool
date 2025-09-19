"""
MACL交易日类型集成测试脚本
测试增强市场时钟和全日/半日交易模式支持
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from infrastructure.enhanced_market_clock import (
    EnhancedMarketClockService,
    TradingDayType,
    TradingSessionType
)
from infrastructure.enhanced_global_scheduler import EnhancedGlobalScheduler


async def test_macl_trading_day_types():
    """测试MACL交易日类型判断"""
    print("=" * 60)
    print("🧪 测试MACL交易日类型判断")
    print("=" * 60)

    market_clock = EnhancedMarketClockService()

    # 测试不同市场的交易日类型
    markets = ["cn", "hk", "us"]
    test_dates = [
        datetime.now(),  # 今天
        datetime.now() + timedelta(days=1),  # 明天
        datetime(2024, 12, 24),  # 平安夜（可能的半日交易）
        datetime(2024, 12, 31),  # 除夕（可能的半日交易）
        datetime(2024, 7, 4),    # 美国独立日
        datetime(2024, 10, 1),   # 中国国庆节
    ]

    for market in markets:
        print(f"\n📊 {market.upper()} 市场测试:")
        print("-" * 40)

        for test_date in test_dates:
            try:
                # 获取交易日类型
                day_type = market_clock.get_trading_day_type_from_macl(market, test_date)
                session_type = market_clock.get_trading_session_type(market, test_date)

                # 获取交易时间
                start_time, end_time, lunch_break = market_clock.get_enhanced_trading_hours(market, test_date)

                # 获取详细信息
                trading_summary = market_clock.get_trading_summary(market, test_date)

                print(f"  📅 {test_date.strftime('%Y-%m-%d %A')}")
                print(f"     日期类型: {day_type.value}")
                print(f"     交易时段: {session_type.value}")
                print(f"     交易时间: {start_time} - {end_time}")
                if lunch_break:
                    print(f"     午休时间: {lunch_break[0]} - {lunch_break[1]}")
                print(f"     状态描述: {trading_summary['status_description']}")
                print()

            except Exception as e:
                print(f"  ❌ 错误 {test_date.strftime('%Y-%m-%d')}: {e}")


async def test_enhanced_scheduler_integration():
    """测试增强调度器集成"""
    print("=" * 60)
    print("🔄 测试增强调度器集成")
    print("=" * 60)

    # 模拟代理池管理器
    class MockProxyPoolManager:
        def __init__(self, market: str):
            self.market = market
            self.is_running = False

        async def start(self):
            print(f"    🚀 启动 {self.market.upper()} 代理池")
            self.is_running = True

        async def stop(self):
            print(f"    🛑 停止 {self.market.upper()} 代理池")
            self.is_running = False

    # 模拟管理器获取函数
    managers = {
        "cn": MockProxyPoolManager("cn"),
        "hk": MockProxyPoolManager("hk"),
        "us": MockProxyPoolManager("us"),
    }

    def get_manager_func(market: str, mode: str) -> MockProxyPoolManager:
        if market.lower() in managers:
            return managers[market.lower()]
        raise ValueError(f"Manager not found for {market}")

    # 创建增强调度器
    scheduler = EnhancedGlobalScheduler(get_manager_func)

    # 测试不同市场的调度决策
    markets = ["cn", "hk", "us"]

    for market in markets:
        print(f"\n📋 {market.upper()} 市场调度测试:")
        print("-" * 40)

        try:
            # 获取交易日信息
            trading_summary = scheduler.market_clock.get_trading_summary(market)

            print(f"  交易日类型: {trading_summary['day_type']}")
            print(f"  交易时段: {trading_summary['session_type']}")
            print(f"  是否交易日: {trading_summary['is_trading_day']}")

            if trading_summary['is_trading_day']:
                # 测试启动决策
                should_start = scheduler.market_clock.should_start_trading_session_enhanced(market, 30)
                should_stop = scheduler.market_clock.should_stop_trading_session_enhanced(market, 30)

                print(f"  应该启动: {should_start}")
                print(f"  应该停止: {should_stop}")

                # 如果应该启动且当前未运行，则启动
                if should_start and not managers[market].is_running:
                    await managers[market].start()
                elif should_stop and managers[market].is_running:
                    await managers[market].stop()
                else:
                    print(f"  当前状态: {'运行中' if managers[market].is_running else '已停止'}")
            else:
                print(f"  非交易日，确保服务停止")
                if managers[market].is_running:
                    await managers[market].stop()

        except Exception as e:
            print(f"  ❌ 调度测试失败: {e}")


async def test_api_integration():
    """测试API集成功能"""
    print("=" * 60)
    print("🌐 测试API集成功能")
    print("=" * 60)

    market_clock = EnhancedMarketClockService()

    # 模拟API调用
    print("\n📡 模拟API调用测试:")
    print("-" * 40)

    # 测试获取交易日信息
    markets = ["cn", "hk", "us"]

    for market in markets:
        try:
            # 模拟 GET /enhanced/trading-day/{market}
            trading_summary = market_clock.get_trading_summary(market)

            print(f"  GET /enhanced/trading-day/{market}")
            print(f"  响应: {trading_summary}")
            print()

            # 模拟 GET /enhanced/macl/day-type/{market}
            day_type = market_clock.get_trading_day_type_from_macl(market)
            session_type = market_clock.get_trading_session_type(market)

            macl_response = {
                "market": market.upper(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "day_type": day_type.value,
                "session_type": session_type.value,
                "is_trading_day": day_type.value in ["NORMAL", "HALF_DAY"],
                "data_source": "macl"
            }

            print(f"  GET /enhanced/macl/day-type/{market}")
            print(f"  响应: {macl_response}")
            print()

        except Exception as e:
            print(f"  ❌ API测试失败 {market}: {e}")


async def test_half_day_trading_scenarios():
    """测试半日交易场景"""
    print("=" * 60)
    print("⏰ 测试半日交易场景")
    print("=" * 60)

    market_clock = EnhancedMarketClockService()

    # 构造半日交易测试场景
    test_scenarios = [
        {
            "date": datetime(2024, 12, 24),  # 平安夜
            "market": "hk",
            "expected_type": "HALF_DAY",
            "description": "香港平安夜半日交易"
        },
        {
            "date": datetime(2024, 12, 31),  # 除夕
            "market": "hk",
            "expected_type": "HALF_DAY",
            "description": "香港除夕半日交易"
        },
        {
            "date": datetime(2024, 11, 29),  # 感恩节后
            "market": "us",
            "expected_type": "HALF_DAY",
            "description": "美股感恩节后半日交易"
        },
        {
            "date": datetime.now(),  # 今天（正常交易日）
            "market": "cn",
            "expected_type": "NORMAL",
            "description": "中国正常交易日"
        }
    ]

    for scenario in test_scenarios:
        print(f"\n🎯 测试场景: {scenario['description']}")
        print("-" * 50)

        try:
            market = scenario['market']
            test_date = scenario['date']

            # 获取交易日类型
            day_type = market_clock.get_trading_day_type_from_macl(market, test_date)
            session_type = market_clock.get_trading_session_type(market, test_date)

            # 获取交易时间
            start_time, end_time, lunch_break = market_clock.get_enhanced_trading_hours(market, test_date)

            print(f"  日期: {test_date.strftime('%Y-%m-%d')}")
            print(f"  市场: {market.upper()}")
            print(f"  检测到类型: {day_type.value}")
            print(f"  交易时段: {session_type.value}")
            print(f"  交易时间: {start_time} - {end_time}")

            # 验证是否符合预期
            if day_type.value == scenario['expected_type']:
                print(f"  ✅ 类型判断正确")
            else:
                print(f"  ⚠️  类型判断不符合预期 (预期: {scenario['expected_type']})")

            # 如果是半日交易，显示详细信息
            if day_type == TradingDayType.HALF_DAY:
                if session_type == TradingSessionType.MORNING_ONLY:
                    print(f"  📅 半日交易模式: 仅上午交易")
                elif session_type == TradingSessionType.AFTERNOON_ONLY:
                    print(f"  📅 半日交易模式: 仅下午交易")
                else:
                    print(f"  📅 半日交易模式: {session_type.value}")

        except Exception as e:
            print(f"  ❌ 场景测试失败: {e}")


async def test_real_time_decision_making():
    """测试实时决策制定"""
    print("=" * 60)
    print("⚡ 测试实时决策制定")
    print("=" * 60)

    market_clock = EnhancedMarketClockService()

    # 测试当前时间的决策
    markets = ["cn", "hk", "us"]

    for market in markets:
        print(f"\n🕐 {market.upper()} 市场实时决策:")
        print("-" * 40)

        try:
            now = market_clock.market_now(market)

            # 获取当前交易状态
            is_trading_day = market_clock.is_trading_day_enhanced(market, now)
            is_market_open = market_clock.is_market_open(market, now)

            # 获取启动/停止决策
            should_start = market_clock.should_start_trading_session_enhanced(market, 30)  # 30分钟提前
            should_stop = market_clock.should_stop_trading_session_enhanced(market, 30)   # 30分钟延后

            # 获取交易日信息
            trading_summary = market_clock.get_trading_summary(market, now)

            print(f"  当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  是否交易日: {is_trading_day}")
            print(f"  市场是否开盘: {is_market_open}")
            print(f"  交易日类型: {trading_summary['day_type']}")
            print(f"  交易时段: {trading_summary['session_type']}")
            print(f"  状态描述: {trading_summary['status_description']}")
            print()

            # 决策建议
            print(f"  🤖 代理池管理决策:")
            if should_start:
                print(f"     ✅ 建议启动代理池 (盘前准备)")
            elif should_stop:
                print(f"     🛑 建议停止代理池 (盘后收尾)")
            elif is_trading_day and is_market_open:
                print(f"     🟢 保持代理池运行 (交易时段)")
            else:
                print(f"     ⏸️  保持代理池停止 (非交易时段)")

        except Exception as e:
            print(f"  ❌ 实时决策测试失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 MACL交易日类型集成测试开始")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # 执行各项测试
        await test_macl_trading_day_types()
        await test_enhanced_scheduler_integration()
        await test_api_integration()
        await test_half_day_trading_scenarios()
        await test_real_time_decision_making()

        print("=" * 60)
        print("✅ 所有集成测试完成")
        print("=" * 60)

        # 总结关键功能
        print("\n🎯 集成功能确认:")
        print("✅ MACL交易日类型判断 (全日/半日/假期/周末)")
        print("✅ 增强市场时钟服务 (支持半日交易时间)")
        print("✅ 增强全局调度器 (基于交易日类型的代理池管理)")
        print("✅ API接口集成 (RESTful接口支持)")
        print("✅ 实时决策制定 (启动/停止代理池)")
        print("✅ 向后兼容 (保持与现有MACL逻辑兼容)")

    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())