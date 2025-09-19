"""
优化的A/B池配置管理器
支持开发/生产环境自动切换和批量限制管理
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

@dataclass
class ProxyPoolConfig:
    """代理池配置数据结构"""
    environment: str
    batch_size: int
    min_threshold: int
    prefetch_buffer: int
    max_concurrent: int
    rotation_interval: int
    ip_lifetime: int
    overlap_window: int
    warmup_duration: int
    database_url: str
    table_name: str
    log_level: str
    enable_metrics: bool = False

class OptimizedConfigManager:
    """优化的配置管理器 - 严格遵循批量限制"""

    def __init__(self):
        self.environment = os.getenv("PROXY_ENVIRONMENT", "development")
        self._validate_environment()

    def _validate_environment(self):
        """验证环境配置"""
        if self.environment not in ["development", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")

    def get_config(self) -> ProxyPoolConfig:
        """获取当前环境配置"""
        if self.environment == "development":
            return self._get_development_config()
        else:
            return self._get_production_config()

    def _get_development_config(self) -> ProxyPoolConfig:
        """开发环境配置 - 20个代理限制"""
        return ProxyPoolConfig(
            environment="development",
            batch_size=int(os.getenv("PROXY_BATCH_SIZE", "20")),  # 用户指定测试限制
            min_threshold=int(os.getenv("PROXY_MIN_THRESHOLD", "10")),
            prefetch_buffer=int(os.getenv("PROXY_PREFETCH_BUFFER", "5")),
            max_concurrent=int(os.getenv("PROXY_MAX_CONCURRENT", "1")),
            rotation_interval=int(os.getenv("ROTATION_INTERVAL_SECONDS", "420")),  # 7分钟
            ip_lifetime=int(os.getenv("IP_LIFETIME_SECONDS", "600")),  # 10分钟
            overlap_window=int(os.getenv("OVERLAP_WINDOW_SECONDS", "180")),  # 3分钟
            warmup_duration=int(os.getenv("WARMUP_DURATION_SECONDS", "120")),  # 2分钟
            database_url=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/proxy_pool"),
            table_name=os.getenv("PROXY_TABLE_NAME", "mh_proxy_pool"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_metrics=os.getenv("ENABLE_METRICS", "false").lower() == "true"
        )

    def _get_production_config(self) -> ProxyPoolConfig:
        """生产环境配置 - 200个代理限制"""
        return ProxyPoolConfig(
            environment="production",
            batch_size=int(os.getenv("PROXY_BATCH_SIZE", "200")),  # 接口上限
            min_threshold=int(os.getenv("PROXY_MIN_THRESHOLD", "100")),
            prefetch_buffer=int(os.getenv("PROXY_PREFETCH_BUFFER", "80")),
            max_concurrent=int(os.getenv("PROXY_MAX_CONCURRENT", "2")),
            rotation_interval=int(os.getenv("ROTATION_INTERVAL_SECONDS", "420")),  # 7分钟
            ip_lifetime=int(os.getenv("IP_LIFETIME_SECONDS", "600")),  # 10分钟
            overlap_window=int(os.getenv("OVERLAP_WINDOW_SECONDS", "180")),  # 3分钟
            warmup_duration=int(os.getenv("WARMUP_DURATION_SECONDS", "120")),  # 2分钟
            database_url=os.getenv("DATABASE_URL", "postgresql://user:pass@prod_host:5432/proxy_pool"),
            table_name=os.getenv("PROXY_TABLE_NAME", "mh_proxy_pool"),
            log_level=os.getenv("LOG_LEVEL", "WARNING"),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true"
        )

    def validate_batch_size(self, requested_size: int) -> int:
        """验证并限制批量大小"""
        config = self.get_config()
        max_allowed = config.batch_size

        if requested_size > max_allowed:
            return max_allowed
        return requested_size

    def get_environment_summary(self) -> Dict[str, Any]:
        """获取环境配置摘要"""
        config = self.get_config()
        return {
            "environment": config.environment,
            "batch_limits": {
                "max_batch_size": config.batch_size,
                "min_threshold": config.min_threshold,
                "prefetch_buffer": config.prefetch_buffer
            },
            "timing": {
                "rotation_interval_minutes": config.rotation_interval / 60,
                "ip_lifetime_minutes": config.ip_lifetime / 60,
                "overlap_window_minutes": config.overlap_window / 60
            },
            "restrictions": {
                "user_specified_test_limit": config.batch_size if config.environment == "development" else None,
                "interface_limit": config.batch_size if config.environment == "production" else None
            }
        }

# 全局配置管理器实例
config_manager = OptimizedConfigManager()

# 便利函数
def get_current_config() -> ProxyPoolConfig:
    """获取当前配置"""
    return config_manager.get_config()

def validate_batch_request(size: int) -> int:
    """验证批量请求大小"""
    return config_manager.validate_batch_size(size)

def is_development() -> bool:
    """检查是否为开发环境"""
    return config_manager.environment == "development"

def is_production() -> bool:
    """检查是否为生产环境"""
    return config_manager.environment == "production"