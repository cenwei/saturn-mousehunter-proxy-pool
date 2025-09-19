"""
Dependency Injection Module
依赖注入模块 - 避免循环导入，支持增强组件
"""

from typing import Dict, Optional
from infrastructure.proxy_pool import ProxyPoolManager
from infrastructure.global_scheduler import GlobalScheduler
from infrastructure.enhanced_global_scheduler import EnhancedGlobalScheduler
from infrastructure.enhanced_market_clock import EnhancedMarketClockService
from infrastructure.monitoring import AlertManager, HealthMonitor

# 全局变量存储
_proxy_pool_managers: Dict[str, ProxyPoolManager] = {}
_global_scheduler: Optional[GlobalScheduler] = None
_enhanced_global_scheduler: Optional[EnhancedGlobalScheduler] = None
_enhanced_market_clock: Optional[EnhancedMarketClockService] = None
_alert_manager: Optional[AlertManager] = None
_health_monitor: Optional[HealthMonitor] = None


def set_proxy_pool_managers(managers: Dict[str, ProxyPoolManager]):
    """设置代理池管理器"""
    global _proxy_pool_managers
    _proxy_pool_managers = managers


def set_global_scheduler(scheduler: GlobalScheduler):
    """设置全局调度器"""
    global _global_scheduler
    _global_scheduler = scheduler


def set_enhanced_global_scheduler(scheduler: EnhancedGlobalScheduler):
    """设置增强全局调度器"""
    global _enhanced_global_scheduler
    _enhanced_global_scheduler = scheduler


def set_enhanced_market_clock(market_clock: EnhancedMarketClockService):
    """设置增强市场时钟"""
    global _enhanced_market_clock
    _enhanced_market_clock = market_clock


def set_alert_manager(alert_manager: AlertManager):
    """设置告警管理器"""
    global _alert_manager
    _alert_manager = alert_manager


def set_health_monitor(health_monitor: HealthMonitor):
    """设置健康监控器"""
    global _health_monitor
    _health_monitor = health_monitor


def get_proxy_pool_manager(market: str, mode: str) -> ProxyPoolManager:
    """获取代理池管理器"""
    key = f"{market.upper()}_{mode.lower()}"
    if key not in _proxy_pool_managers:
        raise ValueError(f"Proxy pool manager not found for {market}/{mode}")
    return _proxy_pool_managers[key]


def get_all_proxy_pool_managers() -> Dict[str, ProxyPoolManager]:
    """获取所有代理池管理器"""
    return _proxy_pool_managers


def get_global_scheduler() -> Optional[GlobalScheduler]:
    """获取全局调度器"""
    return _global_scheduler


def get_enhanced_global_scheduler() -> Optional[EnhancedGlobalScheduler]:
    """获取增强全局调度器"""
    return _enhanced_global_scheduler


def get_enhanced_market_clock() -> Optional[EnhancedMarketClockService]:
    """获取增强市场时钟"""
    return _enhanced_market_clock


def get_alert_manager() -> Optional[AlertManager]:
    """获取告警管理器"""
    return _alert_manager


def get_health_monitor() -> Optional[HealthMonitor]:
    """获取健康监控器"""
    return _health_monitor


# 增强组件初始化函数
def initialize_enhanced_components():
    """初始化增强组件"""
    global _enhanced_market_clock, _enhanced_global_scheduler

    if _enhanced_market_clock is None:
        _enhanced_market_clock = EnhancedMarketClockService()

    if _enhanced_global_scheduler is None and _proxy_pool_managers:
        # 获取代理池管理器函数
        def get_manager_func(market: str, mode: str) -> ProxyPoolManager:
            return get_proxy_pool_manager(market, mode)

        _enhanced_global_scheduler = EnhancedGlobalScheduler(get_manager_func)


def is_enhanced_mode_enabled() -> bool:
    """检查是否启用增强模式"""
    return _enhanced_global_scheduler is not None and _enhanced_market_clock is not None
