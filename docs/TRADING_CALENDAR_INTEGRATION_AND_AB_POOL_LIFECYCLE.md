# 代理池管理交易日历集成和A/B池生命周期管理方案

## 📋 需求分析

基于用户需求和现有代码分析，需要实现以下核心功能：

1. **交易日历集成**: 从市场数据服务的交易日历读取审核后的交易日期
2. **MACL数据回退**: 当日无审核数据时使用现有的市场时钟逻辑
3. **A/B池生命周期管理**: 实现盘中代理池的启动、运行、停止三个阶段

## 🏗️ 系统架构设计

### 当前代理池架构分析

```
代理池系统架构:
├── API层 (proxy_pool_routes.py)
├── 基础设施层
│   ├── MarketClockService - 市场时钟服务 ⭐ 需要增强
│   ├── GlobalScheduler - 全局调度器 ⭐ 需要集成日历
│   └── ProxyPoolManager - 代理池管理器 ⭐ 需要A/B池支持
└── 领域层
    └── IMarketClock - 市场时钟接口 ⭐ 需要扩展
```

### 增强后的架构

```
增强的代理池系统:
├── API层
│   └── 新增交易日历集成接口
├── 基础设施层
│   ├── EnhancedMarketClockService - 增强市场时钟 ✨ 新增
│   ├── TradingCalendarIntegration - 交易日历集成 ✨ 新增
│   ├── EnhancedGlobalScheduler - 增强全局调度器 ✨ 升级
│   └── ABPoolLifecycleManager - A/B池生命周期管理 ✨ 新增
└── 领域层
    └── ITradingCalendarProvider - 交易日历提供者 ✨ 新增
```

---

## 🔗 交易日历集成设计

### 1. 交易日历提供者接口

```python
# src/domain/entities/trading_calendar.py
from abc import ABC, abstractmethod
from datetime import date, time
from typing import Optional, Tuple, List
from dataclasses import dataclass

@dataclass
class TradingSession:
    """交易时段"""
    session_type: str  # "morning", "afternoon", "regular"
    start_time: time
    end_time: time
    description: str

@dataclass
class TradingCalendarDay:
    """交易日历日期"""
    market: str
    calendar_date: date
    is_trading_day: bool
    day_type: str  # "NORMAL", "HOLIDAY", "HALF_DAY"
    market_open: Optional[time]
    market_close: Optional[time]
    trading_sessions: List[TradingSession]
    approval_status: str  # "approved", "pending_review", etc.
    data_source: str  # "calendar_api", "macl_fallback"

class ITradingCalendarProvider(ABC):
    """交易日历数据提供者接口"""

    @abstractmethod
    async def get_trading_day(self, market: str, target_date: date) -> Optional[TradingCalendarDay]:
        """获取指定日期的交易日历信息"""
        pass

    @abstractmethod
    async def is_trading_day(self, market: str, target_date: date) -> bool:
        """判断指定日期是否为交易日"""
        pass

    @abstractmethod
    async def get_next_trading_day(self, market: str, from_date: date) -> Optional[TradingCalendarDay]:
        """获取下一个交易日"""
        pass
```

### 2. 交易日历集成实现

```python
# src/infrastructure/trading_calendar_integration.py
import httpx
from typing import Optional
from datetime import date, time
from saturn_mousehunter_shared import get_logger

from domain.entities.trading_calendar import ITradingCalendarProvider, TradingCalendarDay, TradingSession
from .market_clock import MarketClockService

class TradingCalendarIntegration(ITradingCalendarProvider):
    """交易日历集成服务"""

    def __init__(self,
                 calendar_api_base_url: str = "http://192.168.8.168:8000/api/v1",
                 fallback_market_clock: Optional[MarketClockService] = None):
        self.api_base_url = calendar_api_base_url
        self.fallback_clock = fallback_market_clock or MarketClockService()
        self.logger = get_logger("trading_calendar_integration")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_trading_day(self, market: str, target_date: date) -> Optional[TradingCalendarDay]:
        """获取指定日期的交易日历信息，优先使用审核数据，失败时回退到MACL"""
        try:
            # 1. 尝试从交易日历API获取审核后的数据
            calendar_data = await self._fetch_from_calendar_api(market, target_date)
            if calendar_data:
                self.logger.info(f"使用审核后的交易日历数据: {market} {target_date}")
                return calendar_data

        except Exception as e:
            self.logger.warning(f"获取交易日历API数据失败: {e}")

        # 2. 回退到MACL逻辑
        return await self._fallback_to_macl(market, target_date)

    async def _fetch_from_calendar_api(self, market: str, target_date: date) -> Optional[TradingCalendarDay]:
        """从交易日历API获取数据"""
        url = f"{self.api_base_url}/md/trading/calendar"
        params = {
            "market": market.upper(),
            "date_start": target_date.isoformat(),
            "date_end": target_date.isoformat(),
            "approval_status": "approved"  # 只获取已审核通过的数据
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        if not items:
            return None

        item = items[0]  # 取第一条记录

        # 构建交易时段
        trading_sessions = []
        sessions_data = item.get("trading_sessions", [])
        for session in sessions_data:
            trading_sessions.append(TradingSession(
                session_type=session.get("type", "regular"),
                start_time=time.fromisoformat(session.get("start_time", "09:30")),
                end_time=time.fromisoformat(session.get("end_time", "16:00")),
                description=session.get("description", "")
            ))

        return TradingCalendarDay(
            market=item["market"],
            calendar_date=date.fromisoformat(item["calendar_date"]),
            is_trading_day=item["is_trading_day"],
            day_type=item.get("day_type", "NORMAL"),
            market_open=time.fromisoformat(item["market_open"]) if item.get("market_open") else None,
            market_close=time.fromisoformat(item["market_close"]) if item.get("market_close") else None,
            trading_sessions=trading_sessions,
            approval_status=item.get("approval_status", "approved"),
            data_source="calendar_api"
        )

    async def _fallback_to_macl(self, market: str, target_date: date) -> TradingCalendarDay:
        """回退到MACL逻辑"""
        self.logger.info(f"使用MACL回退逻辑: {market} {target_date}")

        # 使用现有的市场时钟逻辑
        is_trading = self.fallback_clock.is_trading_day(market, target_date)
        start_time, end_time, lunch_break = self.fallback_clock.get_market_trading_hours(market)

        # 构建交易时段
        trading_sessions = []
        if is_trading:
            if lunch_break:  # 有午休时间的市场 (CN/HK)
                trading_sessions.extend([
                    TradingSession("morning", time.fromisoformat(start_time),
                                 time.fromisoformat(lunch_break[0]), "上午交易"),
                    TradingSession("afternoon", time.fromisoformat(lunch_break[1]),
                                 time.fromisoformat(end_time), "下午交易")
                ])
            else:  # 连续交易市场 (US)
                trading_sessions.append(
                    TradingSession("regular", time.fromisoformat(start_time),
                                 time.fromisoformat(end_time), "常规交易")
                )

        return TradingCalendarDay(
            market=market,
            calendar_date=target_date,
            is_trading_day=is_trading,
            day_type="NORMAL" if is_trading else ("WEEKEND" if target_date.weekday() >= 5 else "HOLIDAY"),
            market_open=time.fromisoformat(start_time) if is_trading else None,
            market_close=time.fromisoformat(end_time) if is_trading else None,
            trading_sessions=trading_sessions,
            approval_status="fallback",
            data_source="macl_fallback"
        )

    async def is_trading_day(self, market: str, target_date: date) -> bool:
        """判断是否为交易日"""
        calendar_day = await self.get_trading_day(market, target_date)
        return calendar_day.is_trading_day if calendar_day else False

    async def get_next_trading_day(self, market: str, from_date: date) -> Optional[TradingCalendarDay]:
        """获取下一个交易日"""
        for days_ahead in range(1, 8):  # 查找未来7天
            check_date = from_date + timedelta(days=days_ahead)
            calendar_day = await self.get_trading_day(market, check_date)
            if calendar_day and calendar_day.is_trading_day:
                return calendar_day
        return None
```

---

## 🔄 A/B池生命周期管理

### 1. A/B池生命周期状态

```python
# src/domain/entities/ab_pool_lifecycle.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

class PoolState(Enum):
    """代理池状态"""
    STOPPED = "stopped"           # 已停止
    STARTING = "starting"         # 启动中
    ACTIVE = "active"            # 活跃中
    STANDBY = "standby"          # 待机中
    STOPPING = "stopping"        # 停止中
    ERROR = "error"              # 错误状态

class LifecyclePhase(Enum):
    """生命周期阶段"""
    PRE_MARKET = "pre_market"     # 盘前准备
    MARKET_OPEN = "market_open"   # 市场开盘
    INTRADAY = "intraday"        # 盘中交易
    POST_MARKET = "post_market"   # 盘后收尾
    CLOSED = "closed"            # 已关闭

@dataclass
class ABPoolStatus:
    """A/B池状态"""
    pool_a_state: PoolState
    pool_b_state: PoolState
    active_pool: str  # "A" or "B"
    lifecycle_phase: LifecyclePhase
    last_rotation: Optional[datetime]
    next_rotation: Optional[datetime]
    statistics: Dict[str, Any]
```

### 2. A/B池生命周期管理器

```python
# src/infrastructure/ab_pool_lifecycle_manager.py
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from saturn_mousehunter_shared import get_logger
from domain.entities.ab_pool_lifecycle import PoolState, LifecyclePhase, ABPoolStatus
from domain.entities.trading_calendar import ITradingCalendarProvider
from .proxy_pool import ProxyPool

class ABPoolLifecycleManager:
    """A/B池生命周期管理器"""

    def __init__(self,
                 market: str,
                 calendar_provider: ITradingCalendarProvider,
                 rotation_interval_minutes: int = 30):
        self.market = market
        self.calendar_provider = calendar_provider
        self.rotation_interval = timedelta(minutes=rotation_interval_minutes)
        self.logger = get_logger(f"ab_pool_lifecycle_{market}")

        # A/B双池
        self.pool_a = ProxyPool(f"{market}_A")
        self.pool_b = ProxyPool(f"{market}_B")

        # 状态管理
        self.active_pool_name = "A"
        self.lifecycle_phase = LifecyclePhase.CLOSED
        self.last_rotation: Optional[datetime] = None
        self.rotation_task: Optional[asyncio.Task] = None
        self._running = False

        # 统计数据
        self.statistics = {
            "total_rotations": 0,
            "pool_a_requests": 0,
            "pool_b_requests": 0,
            "pool_a_failures": 0,
            "pool_b_failures": 0,
        }

    async def start_trading_session(self) -> None:
        """启动交易时段 - 生命周期开始"""
        if self._running:
            self.logger.warning("AB池生命周期已在运行中")
            return

        self.logger.info(f"🚀 启动 {self.market} A/B池生命周期管理")
        self._running = True
        self.lifecycle_phase = LifecyclePhase.PRE_MARKET

        try:
            # 阶段1: 盘前准备
            await self._pre_market_preparation()

            # 阶段2: 市场开盘
            await self._market_open_preparation()

            # 阶段3: 盘中交易 (启动自动轮换)
            await self._start_intraday_operations()

        except Exception as e:
            self.logger.error(f"启动交易时段失败: {e}")
            self.lifecycle_phase = LifecyclePhase.CLOSED
            self._running = False
            raise

    async def _pre_market_preparation(self) -> None:
        """阶段1: 盘前准备"""
        self.logger.info("📋 阶段1: 盘前准备开始")
        self.lifecycle_phase = LifecyclePhase.PRE_MARKET

        # 初始化A池并预热
        await self.pool_a.initialize()
        await self.pool_a.warm_up(target_size=50)

        # 初始化B池但保持待机
        await self.pool_b.initialize()

        self.active_pool_name = "A"
        self.logger.info("✅ 盘前准备完成 - A池活跃，B池待机")

    async def _market_open_preparation(self) -> None:
        """阶段2: 市场开盘准备"""
        self.logger.info("🔔 阶段2: 市场开盘准备")
        self.lifecycle_phase = LifecyclePhase.MARKET_OPEN

        # 确保A池达到最佳状态
        await self.pool_a.scale_to_target(target_size=100)

        # B池预热到50%
        await self.pool_b.warm_up(target_size=50)

        self.logger.info("✅ 开盘准备完成 - 双池就绪")

    async def _start_intraday_operations(self) -> None:
        """阶段3: 启动盘中交易操作"""
        self.logger.info("📈 阶段3: 盘中交易开始")
        self.lifecycle_phase = LifecyclePhase.INTRADAY

        # 启动自动轮换任务
        self.rotation_task = asyncio.create_task(self._rotation_loop())

        self.logger.info("🔄 A/B池自动轮换已启动")

    async def _rotation_loop(self) -> None:
        """A/B池自动轮换循环"""
        try:
            while self._running and self.lifecycle_phase == LifecyclePhase.INTRADAY:
                try:
                    # 等待轮换间隔
                    await asyncio.sleep(self.rotation_interval.total_seconds())

                    if self._running:  # 再次检查运行状态
                        await self._perform_rotation()

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"轮换过程出错: {e}")
                    await asyncio.sleep(60)  # 错误后等待1分钟

        except asyncio.CancelledError:
            self.logger.info("轮换循环已取消")
        finally:
            self.logger.info("轮换循环已结束")

    async def _perform_rotation(self) -> None:
        """执行A/B池轮换"""
        current_pool = self._get_active_pool()
        standby_pool = self._get_standby_pool()
        next_pool_name = "B" if self.active_pool_name == "A" else "A"

        self.logger.info(f"🔄 开始 A/B池轮换: {self.active_pool_name} → {next_pool_name}")

        try:
            # 1. 预热待机池
            await standby_pool.warm_up(target_size=80)

            # 2. 执行切换
            self.active_pool_name = next_pool_name
            self.last_rotation = datetime.now()

            # 3. 缩减原活跃池至待机状态
            await current_pool.scale_down(target_size=30)

            # 4. 更新统计
            self.statistics["total_rotations"] += 1

            self.logger.info(f"✅ A/B池轮换完成: 当前活跃池 {self.active_pool_name}")

        except Exception as e:
            self.logger.error(f"A/B池轮换失败: {e}")
            # 轮换失败时保持原状态

    async def stop_trading_session(self) -> None:
        """停止交易时段 - 生命周期结束"""
        if not self._running:
            return

        self.logger.info(f"🛑 停止 {self.market} A/B池生命周期管理")
        self.lifecycle_phase = LifecyclePhase.POST_MARKET

        # 停止轮换任务
        if self.rotation_task and not self.rotation_task.done():
            self.rotation_task.cancel()
            try:
                await self.rotation_task
            except asyncio.CancelledError:
                pass

        # 阶段4: 盘后收尾
        await self._post_market_cleanup()

        self.lifecycle_phase = LifecyclePhase.CLOSED
        self._running = False

        self.logger.info("✅ A/B池生命周期管理已停止")

    async def _post_market_cleanup(self) -> None:
        """阶段4: 盘后收尾"""
        self.logger.info("🧹 阶段4: 盘后收尾")

        # 逐步关闭双池
        await asyncio.gather(
            self.pool_a.graceful_shutdown(),
            self.pool_b.graceful_shutdown(),
            return_exceptions=True
        )

        # 记录最终统计
        self.logger.info("📊 交易时段统计", extra=self.statistics)

    def _get_active_pool(self) -> ProxyPool:
        """获取当前活跃池"""
        return self.pool_a if self.active_pool_name == "A" else self.pool_b

    def _get_standby_pool(self) -> ProxyPool:
        """获取当前待机池"""
        return self.pool_b if self.active_pool_name == "A" else self.pool_a

    async def get_proxy(self, proxy_type: str = "short") -> Optional[str]:
        """从活跃池获取代理"""
        if not self._running:
            return None

        active_pool = self._get_active_pool()
        proxy = await active_pool.get_proxy(proxy_type)

        # 更新统计
        if self.active_pool_name == "A":
            self.statistics["pool_a_requests"] += 1
        else:
            self.statistics["pool_b_requests"] += 1

        return proxy

    async def report_failure(self, proxy_addr: str) -> None:
        """报告代理失败"""
        # 尝试在双池中查找并标记失败
        await asyncio.gather(
            self.pool_a.report_failure(proxy_addr),
            self.pool_b.report_failure(proxy_addr),
            return_exceptions=True
        )

        # 更新失败统计
        if self.active_pool_name == "A":
            self.statistics["pool_a_failures"] += 1
        else:
            self.statistics["pool_b_failures"] += 1

    def get_status(self) -> ABPoolStatus:
        """获取A/B池状态"""
        return ABPoolStatus(
            pool_a_state=self._get_pool_state(self.pool_a),
            pool_b_state=self._get_pool_state(self.pool_b),
            active_pool=self.active_pool_name,
            lifecycle_phase=self.lifecycle_phase,
            last_rotation=self.last_rotation,
            next_rotation=self.last_rotation + self.rotation_interval if self.last_rotation else None,
            statistics=self.statistics.copy()
        )

    def _get_pool_state(self, pool: ProxyPool) -> PoolState:
        """获取代理池状态"""
        if not pool.is_initialized:
            return PoolState.STOPPED
        elif pool.is_scaling:
            return PoolState.STARTING if pool.current_size < pool.target_size else PoolState.STOPPING
        elif pool == self._get_active_pool():
            return PoolState.ACTIVE
        else:
            return PoolState.STANDBY
```

---

## 🔌 增强的全局调度器

### 集成交易日历的调度器

```python
# src/infrastructure/enhanced_global_scheduler.py
import asyncio
from typing import Dict, Optional
from datetime import date, datetime, timedelta

from saturn_mousehunter_shared import get_logger
from domain.config_entities import ProxyPoolMode, IProxyPoolConfigRepository
from domain.entities.trading_calendar import ITradingCalendarProvider
from .trading_calendar_integration import TradingCalendarIntegration
from .ab_pool_lifecycle_manager import ABPoolLifecycleManager
from .postgresql_repositories import PostgreSQLProxyPoolConfigRepository

class EnhancedGlobalScheduler:
    """增强的全局调度器 - 集成交易日历和A/B池生命周期管理"""

    def __init__(self, get_manager_func, calendar_api_base_url: str):
        self.get_manager_func = get_manager_func
        self.config_repo: IProxyPoolConfigRepository = PostgreSQLProxyPoolConfigRepository()

        # 集成交易日历
        self.calendar_provider: ITradingCalendarProvider = TradingCalendarIntegration(
            calendar_api_base_url
        )

        # A/B池生命周期管理器
        self.ab_managers: Dict[str, ABPoolLifecycleManager] = {}

        self.logger = get_logger("enhanced_global_scheduler")
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动增强全局调度器"""
        if self._running:
            self.logger.warning("增强全局调度器已在运行中")
            return

        self.logger.info("🚀 启动增强全局调度器 (支持交易日历集成)")
        self._running = True

        # 启动主调度循环
        self._scheduler_task = asyncio.create_task(self._enhanced_scheduler_loop())

        self.logger.info("✅ 增强全局调度器已启动")

    async def _enhanced_scheduler_loop(self):
        """增强的调度循环"""
        try:
            while self._running:
                try:
                    # 获取所有激活的配置
                    configs = await self.config_repo.get_all_active_configs()

                    for config in configs:
                        if config.mode == ProxyPoolMode.LIVE and config.auto_start_enabled:
                            await self._check_enhanced_market_schedule(config.market, config)

                    # 每分钟检查一次
                    await asyncio.sleep(60)

                except Exception as e:
                    self.logger.error(f"增强调度循环出错: {e}")
                    await asyncio.sleep(60)

        except asyncio.CancelledError:
            self.logger.info("增强调度循环已取消")

    async def _check_enhanced_market_schedule(self, market: str, config):
        """检查增强的市场调度 (集成交易日历)"""
        try:
            today = date.today()

            # 1. 检查今日是否为交易日 (优先使用审核数据)
            is_trading_day = await self.calendar_provider.is_trading_day(market, today)

            if not is_trading_day:
                # 非交易日确保服务停止
                await self._ensure_market_stopped(market, "非交易日")
                return

            # 2. 获取交易日历详细信息
            calendar_day = await self.calendar_provider.get_trading_day(market, today)
            if not calendar_day:
                self.logger.warning(f"无法获取 {market} 的交易日历信息，跳过调度")
                return

            # 3. 检查当前时间是否应该启动/停止
            now = datetime.now()
            should_start = await self._should_start_with_calendar(calendar_day, config, now)
            should_stop = await self._should_stop_with_calendar(calendar_day, config, now)

            # 4. 获取或创建A/B池管理器
            ab_manager = await self._get_or_create_ab_manager(market)

            # 5. 执行调度决策
            if should_start and not ab_manager._running:
                await self._start_market_with_calendar_info(market, calendar_day, ab_manager)
            elif should_stop and ab_manager._running:
                await self._stop_market_with_calendar_info(market, calendar_day, ab_manager)
            elif ab_manager._running:
                # 记录运行状态和下次停止时间
                await self._log_running_status(market, calendar_day, config)

        except Exception as e:
            self.logger.error(f"检查增强市场调度失败 {market}: {e}")

    async def _should_start_with_calendar(self, calendar_day, config, now: datetime) -> bool:
        """基于交易日历判断是否应该启动"""
        if not calendar_day.is_trading_day:
            return False

        # 计算盘前启动时间
        if calendar_day.market_open:
            pre_market_time = datetime.combine(
                calendar_day.calendar_date,
                calendar_day.market_open
            ) - timedelta(minutes=config.pre_market_start_minutes)

            return now >= pre_market_time

        return False

    async def _should_stop_with_calendar(self, calendar_day, config, now: datetime) -> bool:
        """基于交易日历判断是否应该停止"""
        if not calendar_day.is_trading_day:
            return True

        # 计算盘后停止时间
        if calendar_day.market_close:
            post_market_time = datetime.combine(
                calendar_day.calendar_date,
                calendar_day.market_close
            ) + timedelta(minutes=config.post_market_stop_minutes)

            return now >= post_market_time

        return False

    async def _get_or_create_ab_manager(self, market: str) -> ABPoolLifecycleManager:
        """获取或创建A/B池管理器"""
        if market not in self.ab_managers:
            self.ab_managers[market] = ABPoolLifecycleManager(
                market=market,
                calendar_provider=self.calendar_provider,
                rotation_interval_minutes=30  # 可配置
            )
        return self.ab_managers[market]

    async def _start_market_with_calendar_info(self, market: str, calendar_day, ab_manager: ABPoolLifecycleManager):
        """使用交易日历信息启动市场"""
        data_source = calendar_day.data_source
        approval_status = calendar_day.approval_status

        self.logger.info(
            f"🚀 启动市场 {market.upper()}: "
            f"数据源={data_source}, 审核状态={approval_status}"
        )

        try:
            # 启动A/B池生命周期管理
            await ab_manager.start_trading_session()

            self.logger.info(f"✅ 市场 {market.upper()} A/B池生命周期已启动")

            # 记录启动信息
            sessions_info = ", ".join([
                f"{s.session_type}:{s.start_time}-{s.end_time}"
                for s in calendar_day.trading_sessions
            ])
            self.logger.info(f"📋 交易时段: {sessions_info}")

        except Exception as e:
            self.logger.error(f"❌ 启动市场 {market.upper()} A/B池失败: {e}")

    async def _stop_market_with_calendar_info(self, market: str, calendar_day, ab_manager: ABPoolLifecycleManager):
        """使用交易日历信息停止市场"""
        self.logger.info(f"🛑 停止市场 {market.upper()}: 交易时段结束")

        try:
            # 停止A/B池生命周期管理
            await ab_manager.stop_trading_session()

            self.logger.info(f"✅ 市场 {market.upper()} A/B池生命周期已停止")

            # 记录下次启动时间
            next_trading_day = await self.calendar_provider.get_next_trading_day(
                market, calendar_day.calendar_date
            )
            if next_trading_day:
                self.logger.info(
                    f"📅 下次交易日: {next_trading_day.calendar_date} "
                    f"({next_trading_day.data_source})"
                )

        except Exception as e:
            self.logger.error(f"❌ 停止市场 {market.upper()} A/B池失败: {e}")

    async def _ensure_market_stopped(self, market: str, reason: str):
        """确保市场停止"""
        if market in self.ab_managers:
            ab_manager = self.ab_managers[market]
            if ab_manager._running:
                self.logger.info(f"🛑 停止市场 {market.upper()}: {reason}")
                await ab_manager.stop_trading_session()

    async def _log_running_status(self, market: str, calendar_day, config):
        """记录运行状态"""
        if market in self.ab_managers:
            ab_status = self.ab_managers[market].get_status()
            self.logger.info(
                f"📊 {market.upper()} 运行中: "
                f"活跃池={ab_status.active_pool}, "
                f"阶段={ab_status.lifecycle_phase.value}, "
                f"轮换={ab_status.statistics['total_rotations']}次"
            )

    async def get_enhanced_status(self) -> dict:
        """获取增强状态信息"""
        status = {
            "scheduler_running": self._running,
            "calendar_integration": True,
            "ab_pool_management": True,
            "markets": {}
        }

        try:
            configs = await self.config_repo.get_all_active_configs()

            for config in configs:
                if config.mode == ProxyPoolMode.LIVE:
                    market = config.market
                    today = date.today()

                    # 获取交易日历信息
                    calendar_day = await self.calendar_provider.get_trading_day(market, today)

                    # 获取A/B池状态
                    ab_status = None
                    if market in self.ab_managers:
                        ab_status = self.ab_managers[market].get_status()

                    status["markets"][market] = {
                        "trading_calendar": {
                            "is_trading_day": calendar_day.is_trading_day if calendar_day else False,
                            "day_type": calendar_day.day_type if calendar_day else "UNKNOWN",
                            "data_source": calendar_day.data_source if calendar_day else "none",
                            "approval_status": calendar_day.approval_status if calendar_day else "none",
                        },
                        "ab_pool_status": {
                            "running": ab_status._running if ab_status else False,
                            "active_pool": ab_status.active_pool if ab_status else None,
                            "lifecycle_phase": ab_status.lifecycle_phase.value if ab_status else "closed",
                            "total_rotations": ab_status.statistics.get("total_rotations", 0) if ab_status else 0,
                        } if ab_status else None,
                        "auto_start_enabled": config.auto_start_enabled,
                    }

            return status

        except Exception as e:
            self.logger.error(f"获取增强状态失败: {e}")
            status["error"] = str(e)
            return status
```

---

## 🔌 API接口增强

### 新增交易日历集成接口

```python
# 在 src/api/routes/proxy_pool_routes.py 中添加

@router.get("/calendar/today/{market}")
async def get_today_calendar(
    market: str,
    enhanced_scheduler = Depends(get_enhanced_global_scheduler)
):
    """获取今日交易日历信息"""
    try:
        today = date.today()
        calendar_day = await enhanced_scheduler.calendar_provider.get_trading_day(
            market, today
        )

        if not calendar_day:
            raise HTTPException(status_code=404, detail=f"No calendar data for {market}")

        return {
            "market": calendar_day.market,
            "calendar_date": calendar_day.calendar_date.isoformat(),
            "is_trading_day": calendar_day.is_trading_day,
            "day_type": calendar_day.day_type,
            "market_open": calendar_day.market_open.isoformat() if calendar_day.market_open else None,
            "market_close": calendar_day.market_close.isoformat() if calendar_day.market_close else None,
            "trading_sessions": [
                {
                    "session_type": s.session_type,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "description": s.description
                }
                for s in calendar_day.trading_sessions
            ],
            "approval_status": calendar_day.approval_status,
            "data_source": calendar_day.data_source
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ab-pool/status/{market}")
async def get_ab_pool_status(
    market: str,
    enhanced_scheduler = Depends(get_enhanced_global_scheduler)
):
    """获取A/B池状态"""
    try:
        if market not in enhanced_scheduler.ab_managers:
            raise HTTPException(status_code=404, detail=f"No AB pool manager for {market}")

        ab_manager = enhanced_scheduler.ab_managers[market]
        status = ab_manager.get_status()

        return {
            "market": market,
            "pool_a_state": status.pool_a_state.value,
            "pool_b_state": status.pool_b_state.value,
            "active_pool": status.active_pool,
            "lifecycle_phase": status.lifecycle_phase.value,
            "last_rotation": status.last_rotation.isoformat() if status.last_rotation else None,
            "next_rotation": status.next_rotation.isoformat() if status.next_rotation else None,
            "statistics": status.statistics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ab-pool/force-rotation/{market}")
async def force_ab_pool_rotation(
    market: str,
    enhanced_scheduler = Depends(get_enhanced_global_scheduler)
):
    """强制执行A/B池轮换"""
    try:
        if market not in enhanced_scheduler.ab_managers:
            raise HTTPException(status_code=404, detail=f"No AB pool manager for {market}")

        ab_manager = enhanced_scheduler.ab_managers[market]

        if not ab_manager._running:
            raise HTTPException(status_code=400, detail="AB pool lifecycle not running")

        await ab_manager._perform_rotation()

        return {
            "status": "success",
            "message": f"Forced rotation completed for {market}",
            "active_pool": ab_manager.active_pool_name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enhanced/status")
async def get_enhanced_system_status(
    enhanced_scheduler = Depends(get_enhanced_global_scheduler)
):
    """获取增强系统状态"""
    return await enhanced_scheduler.get_enhanced_status()
```

---

## 📋 部署配置

### 环境变量配置

```bash
# .env 文件添加
TRADING_CALENDAR_API_BASE_URL=http://192.168.8.168:8000/api/v1
AB_POOL_ROTATION_INTERVAL_MINUTES=30
CALENDAR_API_TIMEOUT_SECONDS=10
ENABLE_ENHANCED_SCHEDULING=true
```

### 依赖注入配置

```python
# src/infrastructure/dependencies.py 更新

def get_enhanced_global_scheduler():
    """获取增强全局调度器"""
    global _enhanced_scheduler
    if _enhanced_scheduler is None:
        calendar_api_url = os.getenv("TRADING_CALENDAR_API_BASE_URL", "http://192.168.8.168:8000/api/v1")
        _enhanced_scheduler = EnhancedGlobalScheduler(
            get_proxy_pool_manager,
            calendar_api_url
        )
    return _enhanced_scheduler
```

---

## 🎯 实施计划

### 阶段1: 交易日历集成 (1-2天)
1. ✅ 实现 `TradingCalendarIntegration`
2. ✅ 更新 `MarketClockService` 接口
3. ✅ 测试API集成和回退机制

### 阶段2: A/B池生命周期管理 (2-3天)
1. ⏳ 实现 `ABPoolLifecycleManager`
2. ⏳ 测试池轮换逻辑
3. ⏳ 性能调优和监控

### 阶段3: 调度器增强 (1-2天)
1. ⏳ 实现 `EnhancedGlobalScheduler`
2. ⏳ 集成A/B池管理
3. ⏳ 增强API接口

### 阶段4: 测试和部署 (1天)
1. ⏳ 端到端测试
2. ⏳ 监控和日志验证
3. ⏳ 生产部署

---

## 🔍 监控和日志

### 关键监控指标
- 交易日历API调用成功率
- MACL回退使用频率
- A/B池轮换成功率
- 代理池健康状况

### 核心日志事件
- 交易日历数据源切换
- A/B池生命周期阶段转换
- 池轮换执行记录
- 调度决策日志

**文档创建时间**: 2025-09-18
**实施状态**: 🎯 设计完成，等待开发实施