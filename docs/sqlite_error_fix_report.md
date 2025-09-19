# 🔧 Proxy-Pool SQLite错误修复报告

## 📋 问题描述

**错误信息**:
```
'sqlite3.Connection' object does not support the asynchronous context manager protocol
```

**错误位置**:
- `infrastructure.global_scheduler:_scheduler_loop:92`
- `infrastructure/database_repositories.py`

## 🔍 问题根因

1. **架构不匹配**: proxy-pool微服务应该使用PostgreSQL，但错误地引用了SQLite实现
2. **异步兼容性**: SQLite的`sqlite3.Connection`不支持`async with`语法
3. **导入错误**: `global_scheduler.py`中导入了`DatabaseProxyPoolConfigRepository`（SQLite版本）而不是`PostgreSQLProxyPoolConfigRepository`

## 🛠️ 修复方案

### 1. 修正导入引用
**文件**: `src/infrastructure/global_scheduler.py`

**修改前**:
```python
from .database_repositories import DatabaseProxyPoolConfigRepository
# ...
self.config_repo: IProxyPoolConfigRepository = DatabaseProxyPoolConfigRepository()
```

**修改后**:
```python
from .postgresql_repositories import PostgreSQLProxyPoolConfigRepository
# ...
self.config_repo: IProxyPoolConfigRepository = PostgreSQLProxyPoolConfigRepository()
```

### 2. 补全PostgreSQL仓储实现
**文件**: `src/infrastructure/postgresql_repositories.py`

**新增方法**: `get_all_active_configs()`
```python
async def get_all_active_configs(self) -> list[ProxyPoolConfig]:
    """获取所有激活的配置"""
    pool = await get_db_pool()

    try:
        async with pool.acquire() as conn:
            query = """
                SELECT market, mode, hailiang_api_url, hailiang_enabled, batch_size,
                       proxy_lifetime_minutes, rotation_interval_minutes, low_watermark,
                       target_size, auto_start_enabled, pre_market_start_minutes,
                       post_market_stop_minutes, backfill_enabled, backfill_duration_hours,
                       created_at, updated_at
                FROM proxy_pool_config
                WHERE is_active = TRUE
                ORDER BY market, mode
            """

            rows = await conn.fetch(query)
            configs = []

            for row in rows:
                config = ProxyPoolConfig(...)
                configs.append(config)

            return configs
    except Exception as e:
        self.logger.error(f"Failed to get all active configs: {e}")
        return []
```

### 3. 移除冲突文件
**操作**: 重命名SQLite实现文件
```bash
mv src/infrastructure/database_repositories.py src/infrastructure/database_repositories.py.backup
```

## ✅ 修复验证

修复后，`global_scheduler`将：
1. ✅ 使用正确的PostgreSQL连接池（`asyncpg.Pool`）
2. ✅ 支持`async with pool.acquire() as conn`语法
3. ✅ 避免SQLite异步兼容性问题
4. ✅ 符合项目的PostgreSQL架构设计

## 🎯 技术要点

### PostgreSQL vs SQLite对比
| 特性 | PostgreSQL | SQLite |
|------|------------|--------|
| 异步支持 | ✅ `asyncpg.Pool` | ❌ `sqlite3.Connection` |
| 并发性能 | ✅ 高并发 | ❌ 有限制 |
| 企业级功能 | ✅ 完整 | ❌ 基础 |
| 项目架构匹配 | ✅ 符合 | ❌ 不符合 |

### 异步上下文管理器要求
```python
# ✅ 正确 - PostgreSQL
async with pool.acquire() as conn:
    await conn.fetch(query)

# ❌ 错误 - SQLite
async with default_connect() as conn:  # sqlite3.Connection不支持
    await conn.fetchone(query)  # 而且fetchone也不是异步方法
```

## 📚 相关文件

### 修改的文件
- `src/infrastructure/global_scheduler.py` - 修正导入和实例化
- `src/infrastructure/postgresql_repositories.py` - 补全缺失方法

### 备份的文件
- `src/infrastructure/database_repositories.py.backup` - SQLite实现（已移除）

### 数据库表结构
确保PostgreSQL数据库中存在以下表：
- `proxy_pool_config` - 代理池配置表
- `proxy_pool_status` - 代理池状态表

## 🚀 后续建议

1. **验证配置**: 确保PostgreSQL连接字符串正确
2. **数据库初始化**: 运行`scripts/init_database.py`创建必要的表
3. **监控日志**: 观察修复后的调度器运行情况
4. **清理代码**: 完全移除SQLite相关的代码引用

---

**修复完成时间**: 2025-01-17
**预期效果**: 彻底解决SQLite异步兼容性错误，恢复调度器正常运行