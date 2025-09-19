"""
Infrastructure层 - 监控告警系统
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from saturn_mousehunter_shared import get_logger


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""

    id: str
    level: AlertLevel
    title: str
    message: str
    market: Optional[str] = None
    component: Optional[str] = None
    timestamp: datetime = None
    acknowledged: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertManager:
    """告警管理器"""

    def __init__(self, max_alerts: int = 1000):
        self.max_alerts = max_alerts
        self.alerts: List[Alert] = []
        self.alert_counts: Dict[str, int] = {}
        self.logger = get_logger("alert_manager")

        # 错误统计
        self.error_stats = {
            "total_errors": 0,
            "api_errors": 0,
            "proxy_failures": 0,
            "scheduler_errors": 0,
            "database_errors": 0,
        }

    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        market: Optional[str] = None,
        component: Optional[str] = None,
    ) -> Alert:
        """创建告警"""
        alert_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts)}"

        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            market=market,
            component=component,
        )

        # 添加到列表
        self.alerts.append(alert)

        # 限制数量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts :]

        # 统计
        level_key = level.value
        self.alert_counts[level_key] = self.alert_counts.get(level_key, 0) + 1

        # 记录日志
        log_method = getattr(self.logger, level.value, self.logger.info)
        log_method(f"[{component or 'SYSTEM'}] {title}: {message}")

        return alert

    def alert_info(
        self, title: str, message: str, market: str = None, component: str = None
    ):
        """信息告警"""
        return self.create_alert(AlertLevel.INFO, title, message, market, component)

    def alert_warning(
        self, title: str, message: str, market: str = None, component: str = None
    ):
        """警告告警"""
        return self.create_alert(AlertLevel.WARNING, title, message, market, component)

    def alert_error(
        self, title: str, message: str, market: str = None, component: str = None
    ):
        """错误告警"""
        self.error_stats["total_errors"] += 1
        return self.create_alert(AlertLevel.ERROR, title, message, market, component)

    def alert_critical(
        self, title: str, message: str, market: str = None, component: str = None
    ):
        """严重告警"""
        self.error_stats["total_errors"] += 1
        return self.create_alert(AlertLevel.CRITICAL, title, message, market, component)

    def alert_api_error(self, message: str, market: str = None):
        """API错误告警"""
        self.error_stats["api_errors"] += 1
        return self.alert_error("API Error", message, market, "API")

    def alert_proxy_failure(self, message: str, market: str = None):
        """代理失败告警"""
        self.error_stats["proxy_failures"] += 1
        return self.alert_warning("Proxy Failure", message, market, "PROXY")

    def alert_scheduler_error(self, message: str, market: str = None):
        """调度器错误告警"""
        self.error_stats["scheduler_errors"] += 1
        return self.alert_error("Scheduler Error", message, market, "SCHEDULER")

    def alert_database_error(self, message: str, component: str = "DATABASE"):
        """数据库错误告警"""
        self.error_stats["database_errors"] += 1
        return self.alert_critical("Database Error", message, None, component)

    def get_recent_alerts(
        self, hours: int = 24, level: AlertLevel = None
    ) -> List[Alert]:
        """获取最近的告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        alerts = [alert for alert in self.alerts if alert.timestamp >= cutoff_time]

        if level:
            alerts = [alert for alert in alerts if alert.level == level]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alerts_by_market(self, market: str, hours: int = 24) -> List[Alert]:
        """获取指定市场的告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            alert
            for alert in self.alerts
            if alert.market == market and alert.timestamp >= cutoff_time
        ]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False

    def get_alert_summary(self) -> Dict:
        """获取告警摘要"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_1h = now - timedelta(hours=1)

        recent_24h = [a for a in self.alerts if a.timestamp >= last_24h]
        recent_1h = [a for a in self.alerts if a.timestamp >= last_1h]

        def count_by_level(alerts, level):
            return len([a for a in alerts if a.level == level])

        return {
            "total_alerts": len(self.alerts),
            "alert_counts": self.alert_counts.copy(),
            "error_stats": self.error_stats.copy(),
            "last_24h": {
                "total": len(recent_24h),
                "critical": count_by_level(recent_24h, AlertLevel.CRITICAL),
                "error": count_by_level(recent_24h, AlertLevel.ERROR),
                "warning": count_by_level(recent_24h, AlertLevel.WARNING),
                "info": count_by_level(recent_24h, AlertLevel.INFO),
            },
            "last_1h": {
                "total": len(recent_1h),
                "critical": count_by_level(recent_1h, AlertLevel.CRITICAL),
                "error": count_by_level(recent_1h, AlertLevel.ERROR),
                "warning": count_by_level(recent_1h, AlertLevel.WARNING),
                "info": count_by_level(recent_1h, AlertLevel.INFO),
            },
        }

    def clear_old_alerts(self, days: int = 7):
        """清理旧告警"""
        cutoff_time = datetime.now() - timedelta(days=days)
        old_count = len(self.alerts)

        self.alerts = [alert for alert in self.alerts if alert.timestamp >= cutoff_time]

        cleared_count = old_count - len(self.alerts)
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} old alerts")

        return cleared_count


class HealthMonitor:
    """健康监控器"""

    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.logger = get_logger("health_monitor")

        # 健康检查阈值
        self.thresholds = {
            "success_rate_warning": 80.0,  # 成功率低于80%告警
            "success_rate_critical": 60.0,  # 成功率低于60%严重告警
            "pool_size_warning": 10,  # 池大小低于10告警
            "proxy_lifetime_warning": 300,  # 代理生命周期低于5分钟告警
            "api_failure_threshold": 5,  # API连续失败5次告警
        }

        self.api_failure_counts = {}

    async def check_market_health(self, market: str, status: dict) -> List[Alert]:
        """检查市场健康状态"""
        alerts = []

        try:
            stats = status.get("stats", {})
            running = status.get("running", False)

            if not running:
                # 如果应该运行但没有运行，告警
                alerts.append(
                    self.alert_manager.alert_warning(
                        "Market Not Running",
                        f"Market {market} proxy pool is not running",
                        market,
                        "HEALTH_CHECK",
                    )
                )
                return alerts

            # 检查成功率
            success_rate = stats.get("success_rate", 0)
            if success_rate < self.thresholds["success_rate_critical"]:
                alerts.append(
                    self.alert_manager.alert_critical(
                        "Low Success Rate",
                        f"Market {market} success rate is critically low: {success_rate}%",
                        market,
                        "HEALTH_CHECK",
                    )
                )
            elif success_rate < self.thresholds["success_rate_warning"]:
                alerts.append(
                    self.alert_manager.alert_warning(
                        "Low Success Rate",
                        f"Market {market} success rate is low: {success_rate}%",
                        market,
                        "HEALTH_CHECK",
                    )
                )

            # 检查池大小
            total_pool_size = stats.get("total_pool_size", 0)
            if total_pool_size < self.thresholds["pool_size_warning"]:
                alerts.append(
                    self.alert_manager.alert_warning(
                        "Low Pool Size",
                        f"Market {market} pool size is low: {total_pool_size}",
                        market,
                        "HEALTH_CHECK",
                    )
                )

            # 检查失败率
            failure_count = stats.get("failure_count", 0)
            total_requests = stats.get("total_requests", 0)

            if total_requests > 100:  # 有足够的请求样本
                failure_rate = (failure_count / total_requests) * 100
                if failure_rate > 40:  # 失败率超过40%
                    alerts.append(
                        self.alert_manager.alert_error(
                            "High Failure Rate",
                            f"Market {market} failure rate is high: {failure_rate:.1f}%",
                            market,
                            "HEALTH_CHECK",
                        )
                    )

        except Exception as e:
            alerts.append(
                self.alert_manager.alert_error(
                    "Health Check Failed",
                    f"Failed to check health for market {market}: {str(e)}",
                    market,
                    "HEALTH_CHECK",
                )
            )

        return alerts

    def record_api_failure(self, market: str, api_name: str, error: str):
        """记录API失败"""
        key = f"{market}_{api_name}"
        self.api_failure_counts[key] = self.api_failure_counts.get(key, 0) + 1

        count = self.api_failure_counts[key]

        if count >= self.thresholds["api_failure_threshold"]:
            self.alert_manager.alert_error(
                "API Consecutive Failures",
                f"API {api_name} failed {count} times consecutively for market {market}: {error}",
                market,
                "API",
            )

    def record_api_success(self, market: str, api_name: str):
        """记录API成功"""
        key = f"{market}_{api_name}"
        if key in self.api_failure_counts:
            del self.api_failure_counts[key]

    def get_health_summary(self) -> dict:
        """获取健康摘要"""
        return {
            "thresholds": self.thresholds.copy(),
            "api_failure_counts": self.api_failure_counts.copy(),
            "monitor_status": "running",
        }
