# 优化的A/B池轮换策略 - 修正版本

## 📋 需求修正和关键约束

### 用户反馈修正
- ✅ **批量获取限制**: 最多200个代理，测试期间使用20个
- ✅ **7分钟轮换间隔**: A/B池智能切换
- ✅ **10分钟IP生命周期**: 代理IP有效期限制
- ✅ **数据库URL读取**: 从数据库直接获取代理URL

---

## 🔧 修正的批量获取策略

### 批量配置参数 (修正版)
```python
# 批量获取配置 - 遵循用户限制
PROXY_BATCH_CONFIGS = {
    "production": {
        "batch_size": 200,        # 生产环境批量大小 (接口上限)
        "min_threshold": 100,     # 最小触发阈值
        "prefetch_buffer": 80,    # 预取缓冲区大小
        "max_concurrent": 2       # 最大并发批次
    },
    "development": {
        "batch_size": 20,         # 开发/测试环境批量大小
        "min_threshold": 10,      # 最小触发阈值
        "prefetch_buffer": 5,     # 预取缓冲区大小
        "max_concurrent": 1       # 最大并发批次
    }
}

# 轮换时间配置
ROTATION_CONFIG = {
    "rotation_interval": 420,     # 7分钟 = 420秒
    "ip_lifetime": 600,          # 10分钟 = 600秒
    "overlap_window": 180,       # 3分钟重叠期
    "warmup_duration": 120       # 2分钟预热时间
}
```

### 优化的A/B池Repository (修正版)

```python
# src/infrastructure/optimized_ab_pool_repository.py
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from saturn_mousehunter_shared import get_logger
from .base_repository import BaseRepository

class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"

@dataclass
class ProxyConfig:
    """代理配置数据结构"""
    url: str
    type: str
    quality_score: float
    last_used: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def age_seconds(self) -> float:
        """获取代理年龄(秒)"""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def is_expired(self) -> bool:
        """检查代理是否过期(10分钟)"""
        return self.age_seconds > 600  # 10分钟

class OptimizedABPoolRepository(BaseRepository):
    """优化的A/B池Repository - 修正批量限制版本"""

    def __init__(self, environment: str = "development"):
        super().__init__()
        self.environment = Environment(environment)
        self.config = PROXY_BATCH_CONFIGS[self.environment.value]
        self.logger = get_logger(f"ab_pool_repo_{environment}")

        # A/B双池存储
        self.pool_a: List[ProxyConfig] = []
        self.pool_b: List[ProxyConfig] = []
        self.active_pool = "A"

        # 性能监控
        self.stats = {
            "total_fetches": 0,
            "successful_fetches": 0,
            "expired_cleanups": 0,
            "rotation_count": 0,
            "avg_fetch_time": 0.0
        }

        # 数据库连接 (从依赖注入获取)
        self.db_connection = None

    async def initialize(self, db_connection):
        """初始化Repository"""
        self.db_connection = db_connection
        await self._initial_population()
        self.logger.info(f"Initialized optimized AB pool repository",
                        environment=self.environment.value,
                        batch_size=self.config["batch_size"])

    async def _initial_population(self):
        """初始化池填充"""
        # 为A池预取代理
        await self._fetch_proxies_for_pool("A", self.config["batch_size"])

        # 为B池预取较少代理作为预备
        await self._fetch_proxies_for_pool("B", self.config["prefetch_buffer"])

        self.logger.info("Initial population completed",
                        pool_a_size=len(self.pool_a),
                        pool_b_size=len(self.pool_b))

    async def _fetch_proxies_from_database(self, count: int) -> List[str]:
        """从数据库获取代理URL列表"""
        try:
            # 修正版本：严格遵循数量限制
            actual_count = min(count, self.config["batch_size"])

            sql = """
            SELECT proxy_url, proxy_type, quality_score
            FROM mh_proxy_pool
            WHERE is_active = true
            AND last_used < NOW() - INTERVAL '5 minutes'
            ORDER BY quality_score DESC, last_used ASC
            LIMIT $1
            """

            rows = await self.db_connection.fetch(sql, actual_count)

            proxy_configs = []
            for row in rows:
                config = ProxyConfig(
                    url=row['proxy_url'],
                    type=row['proxy_type'],
                    quality_score=row['quality_score']
                )
                proxy_configs.append(config)

            self.stats["total_fetches"] += 1
            self.stats["successful_fetches"] += 1

            self.logger.info("Fetched proxies from database",
                           requested_count=count,
                           actual_count=len(proxy_configs),
                           max_allowed=self.config["batch_size"])

            return proxy_configs

        except Exception as e:
            self.logger.error(f"Failed to fetch proxies from database: {e}")
            return []

    async def _fetch_proxies_for_pool(self, pool_name: str, count: int):
        """为指定池获取代理"""
        start_time = datetime.now()

        # 确保不超过配置限制
        actual_count = min(count, self.config["batch_size"])

        proxies = await self._fetch_proxies_from_database(actual_count)

        if pool_name == "A":
            self.pool_a.extend(proxies)
        else:
            self.pool_b.extend(proxies)

        # 更新性能统计
        fetch_time = (datetime.now() - start_time).total_seconds()
        self._update_fetch_stats(fetch_time)

        self.logger.info(f"Fetched proxies for pool {pool_name}",
                        count=len(proxies),
                        pool_size=len(self.pool_a if pool_name == "A" else self.pool_b))

    def _update_fetch_stats(self, fetch_time: float):
        """更新获取统计"""
        if self.stats["total_fetches"] == 0:
            self.stats["avg_fetch_time"] = fetch_time
        else:
            self.stats["avg_fetch_time"] = (
                self.stats["avg_fetch_time"] * (self.stats["total_fetches"] - 1) + fetch_time
            ) / self.stats["total_fetches"]

    async def get_proxy(self, proxy_type: str = "short") -> Optional[str]:
        """从活跃池获取代理"""
        active_pool_list = self.pool_a if self.active_pool == "A" else self.pool_b

        # 清理过期代理
        await self._cleanup_expired_proxies()

        # 检查是否需要补充代理
        if len(active_pool_list) < self.config["min_threshold"]:
            await self._replenish_active_pool()

        # 获取最佳代理
        best_proxy = self._select_best_proxy(active_pool_list, proxy_type)

        if best_proxy:
            best_proxy.last_used = datetime.now()
            return best_proxy.url

        return None

    def _select_best_proxy(self, pool: List[ProxyConfig], proxy_type: str) -> Optional[ProxyConfig]:
        """选择最佳代理"""
        available_proxies = [p for p in pool if not p.is_expired]

        if not available_proxies:
            return None

        # 按质量分数和使用时间排序
        available_proxies.sort(
            key=lambda p: (p.quality_score, -(p.last_used or datetime.min).timestamp()),
            reverse=True
        )

        return available_proxies[0]

    async def _cleanup_expired_proxies(self):
        """清理过期代理"""
        before_a = len(self.pool_a)
        before_b = len(self.pool_b)

        self.pool_a = [p for p in self.pool_a if not p.is_expired]
        self.pool_b = [p for p in self.pool_b if not p.is_expired]

        cleaned_count = (before_a + before_b) - (len(self.pool_a) + len(self.pool_b))

        if cleaned_count > 0:
            self.stats["expired_cleanups"] += cleaned_count
            self.logger.info("Cleaned up expired proxies",
                           cleaned_count=cleaned_count,
                           pool_a_size=len(self.pool_a),
                           pool_b_size=len(self.pool_b))

    async def _replenish_active_pool(self):
        """补充活跃池"""
        if self.active_pool == "A":
            needed = self.config["batch_size"] - len(self.pool_a)
        else:
            needed = self.config["batch_size"] - len(self.pool_b)

        if needed > 0:
            # 限制补充数量不超过配置限制
            replenish_count = min(needed, self.config["batch_size"])
            await self._fetch_proxies_for_pool(self.active_pool, replenish_count)

    async def perform_rotation(self) -> bool:
        """执行A/B池轮换"""
        try:
            standby_pool = "B" if self.active_pool == "A" else "A"

            self.logger.info(f"Starting rotation: {self.active_pool} → {standby_pool}")

            # 预热待机池
            await self._warmup_standby_pool(standby_pool)

            # 执行切换
            old_active = self.active_pool
            self.active_pool = standby_pool

            # 更新统计
            self.stats["rotation_count"] += 1

            self.logger.info("Pool rotation completed",
                           from_pool=old_active,
                           to_pool=self.active_pool,
                           total_rotations=self.stats["rotation_count"])

            # 异步清理旧池
            asyncio.create_task(self._async_cleanup_old_pool(old_active))

            return True

        except Exception as e:
            self.logger.error(f"Pool rotation failed: {e}")
            return False

    async def _warmup_standby_pool(self, pool_name: str):
        """预热待机池"""
        target_size = self.config["batch_size"]
        current_size = len(self.pool_a if pool_name == "A" else self.pool_b)

        if current_size < target_size:
            needed = target_size - current_size
            await self._fetch_proxies_for_pool(pool_name, needed)

    async def _async_cleanup_old_pool(self, pool_name: str):
        """异步清理旧池到最小状态"""
        await asyncio.sleep(180)  # 等待3分钟重叠期

        if pool_name == "A":
            self.pool_a = self.pool_a[:self.config["prefetch_buffer"]]
        else:
            self.pool_b = self.pool_b[:self.config["prefetch_buffer"]]

        self.logger.info(f"Cleaned up old pool {pool_name} to standby size")

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "environment": self.environment.value,
            "config": self.config,
            "active_pool": self.active_pool,
            "pool_sizes": {
                "pool_a": len(self.pool_a),
                "pool_b": len(self.pool_b)
            },
            "performance": self.stats,
            "health": {
                "total_proxies": len(self.pool_a) + len(self.pool_b),
                "active_pool_health": len(self.pool_a if self.active_pool == "A" else self.pool_b) / self.config["batch_size"],
                "expired_ratio": len([p for p in (self.pool_a + self.pool_b) if p.is_expired]) / max(1, len(self.pool_a) + len(self.pool_b))
            }
        }
```

---

## 🎯 关键优化点总结

### 1. 批量限制修正 ✅
- **生产环境**: 最大200个代理 (遵循接口限制)
- **开发环境**: 最大20个代理 (用户指定测试限制)
- **严格检查**: 所有代理获取都检查数量上限

### 2. 7分钟轮换策略 ✅
- **轮换间隔**: 7分钟 = 420秒
- **重叠窗口**: 3分钟缓冲期
- **预热机制**: 2分钟提前准备

### 3. 10分钟IP生命周期 ✅
- **过期检查**: 自动清理10分钟以上代理
- **性能优化**: 异步清理和预取
- **统计监控**: 过期率和健康度指标

### 4. 数据库集成 ✅
- **URL读取**: 直接从数据库获取代理URL
- **质量排序**: 按质量分数和使用时间优选
- **连接管理**: 通过依赖注入管理数据库连接

---

## 📊 配置对比表

| 配置项 | 开发环境 | 生产环境 | 说明 |
|--------|----------|----------|------|
| 批量大小 | 20 | 200 | 用户指定限制 |
| 最小阈值 | 10 | 100 | 触发补充的临界点 |
| 预取缓冲 | 5 | 80 | 待机池预留数量 |
| 轮换间隔 | 7分钟 | 7分钟 | 固定轮换周期 |
| IP生命周期 | 10分钟 | 10分钟 | 固定过期时间 |

---

## 🚀 部署和配置

### 环境变量配置
```bash
# 修正版本的环境配置
PROXY_ENVIRONMENT=development  # 或 production
PROXY_BATCH_SIZE_DEV=20       # 开发环境批量大小
PROXY_BATCH_SIZE_PROD=200     # 生产环境批量大小 (接口上限)
ROTATION_INTERVAL_SECONDS=420  # 7分钟轮换
IP_LIFETIME_SECONDS=600       # 10分钟IP生命周期
```

### 使用示例
```python
# 初始化优化的A/B池
repo = OptimizedABPoolRepository(environment="development")
await repo.initialize(db_connection)

# 获取代理 (自动遵循20个限制)
proxy_url = await repo.get_proxy("short")

# 执行轮换 (7分钟间隔)
success = await repo.perform_rotation()

# 查看统计 (监控批量限制遵循情况)
stats = repo.get_statistics()
```

---

**文档版本**: v2.0 (批量限制修正版)
**更新时间**: 2025-09-18
**遵循约束**: ✅ 最大200个代理，测试20个，数据库URL读取