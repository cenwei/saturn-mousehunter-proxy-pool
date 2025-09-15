# Saturn MouseHunter Proxy Pool Service

代理池轮换微服务，采用领域驱动设计(DDD)架构，提供统一的代理管理和A/B轮换机制。

## 🏗️ 架构设计

采用分层架构设计，遵循领域驱动设计原则：

```
src/
├── domain/                # 领域层 - 核心业务逻辑
│   ├── entities.py       # 实体和接口定义
│   └── services.py       # 领域服务
├── application/          # 应用层 - 用例编排
│   └── services.py       # 应用服务
├── infrastructure/      # 基础设施层 - 技术实现
│   ├── config.py        # 配置管理
│   ├── market_clock.py  # 市场时钟服务
│   ├── proxy_fetchers.py # 代理获取器
│   ├── memory_proxy_repository.py # 内存仓储实现
│   └── proxy_pool.py    # 代理池管理器
├── api/                 # 接口层 - Web API
│   └── routes/
│       └── proxy_pool_routes.py # 路由定义
└── main.py             # 应用入口
```

## 🚀 核心功能

- **A/B轮换机制**：双池设计，定期刷新备用池并原子切换
- **多市场支持**：US/HK/CN/SG/JP/KR/UK/EU市场时区
- **领域驱动设计**：清晰的分层架构和职责分离
- **依赖注入**：松耦合的组件设计
- **缓存集成**：使用shared项目的缓存装饰器
- **AOP支持**：集成测量、重试等切面功能
- **监控集成**：完整的指标收集和状态监控

## 📦 共享依赖

项目集成了`saturn-mousehunter-shared`的核心功能：

- **日志系统**：统一的日志记录和格式化
- **缓存装饰器**：`@cached`, `@cache_invalidate`
- **AOP装饰器**：`@measure`, `@retry`
- **基础工具**：ULID生成、配置管理等

## 🛠️ 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- Redis (可选，用于缓存)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd saturn-mousehunter-proxy-pool
```

2. **安装依赖**
```bash
pip install -r requirements.txt
# 或使用 uv (推荐)
uv pip install -r pyproject.toml
```

3. **配置数据库**
```bash
# 编辑数据库连接配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=saturn_mousehunter
```

4. **初始化数据库**
```bash
python scripts/init_database.py
```

5. **启动服务**

服务现在使用 saturn-mousehunter-shared 中的统一端点配置：

```bash
# 使用启动脚本（推荐）
./start.sh

# 开发环境 (默认)
ENVIRONMENT=development MARKETS=hk ./start.sh

# 启动多个市场
ENVIRONMENT=development MARKETS=cn,hk,us ./start.sh

# 手动启动
ENVIRONMENT=development MARKETS=cn,hk,us python src/main.py
```

6. **访问管理界面**

根据环境不同：
- **开发环境**: http://192.168.8.168:8005
- **测试环境**: http://test-proxy-pool:8005
- **生产环境**: http://proxy-pool.saturn-mousehunter.internal:8005

### 🔧 配置说明

服务端点配置来自 `saturn-mousehunter-shared/config/service_endpoints.py`：

| 环境 | 主机 | 端口 | 完整地址 |
|------|------|------|----------|
| 开发环境 | 192.168.8.168 | 8005 | http://192.168.8.168:8005 |
| 测试环境 | test-proxy-pool | 8005 | http://test-proxy-pool:8005 |
| 生产环境 | proxy-pool.saturn-mousehunter.internal | 8005 | http://proxy-pool.saturn-mousehunter.internal:8005 |

**环境变量**：
- `ENVIRONMENT`: 运行环境 (development/testing/production)
- `MARKETS`: 启动的市场 (cn,hk,us)
- `HOST`: 覆盖配置中的主机地址
- `PORT`: 覆盖配置中的端口

### 环境变量配置

```bash
# 基础配置
export ENVIRONMENT=development      # 运行环境
export MARKETS=cn,hk,us            # 启动的市场
export LOG_LEVEL=INFO              # 日志级别

# 可选配置（会覆盖shared配置）
export HOST=192.168.8.168          # 服务主机
export PORT=8005                   # 服务端口
```

## 🔧 API接口

### 管理接口

- `GET /health` - 健康检查
- `GET /api/v1/config` - 获取配置信息
- `GET /api/v1/status` - 获取服务状态
- `GET /api/v1/metrics` - 获取指标数据
- `POST /api/v1/start` - 启动服务
- `POST /api/v1/stop` - 停止服务

### RPC接口

`POST /api/v1/rpc` - 兼容原ZMQ事件格式

```json
{
    "event": "get_proxy",
    "proxy_type": "short"
}
```

支持的事件：
- `get_proxy` - 获取代理地址
- `report_failure` - 报告代理失败
- `get_status` - 获取服务状态
- `ping` - 心跳检测

## 🧪 测试运行

```bash
# 服务测试
python test_service.py --mode service

# API客户端测试
python test_service.py --mode client

# 外部代理函数测试
python test_service.py --mode external
```

## 🔌 扩展集成

### 1. 外部代理获取函数

```python
# 在应用启动时设置
def my_proxy_fetcher():
    # 从外部服务获取代理列表
    return ["http://proxy1:8080", "http://proxy2:8080"]

# 在main.py的startup_event中
proxy_pool_manager.set_external_fetcher(my_proxy_fetcher)
```

### 2. 缓存配置

服务自动使用shared项目的缓存装饰器：

```python
@cached(ttl=30, key_pattern="proxy_pool_status_{market}_{mode}")
async def get_status(self) -> dict:
    # 状态查询会被缓存30秒
    return await self.domain_service.get_status()
```

### 3. 监控集成

使用AOP装饰器自动收集指标：

```python
@measure("proxy_get_duration", ("market", "mode"))
@retry(times=3, delay=0.1)
async def get_proxy(self, proxy_type: str = "short") -> str | None:
    # 自动测量执行时间和重试逻辑
    pass
```

## 🐳 部署

### Docker

```bash
docker build -t saturn-proxy-pool .
docker run -p 8080:8080 -e MARKET=hk saturn-proxy-pool
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saturn-proxy-pool
spec:
  template:
    spec:
      containers:
      - name: saturn-proxy-pool
        image: saturn-proxy-pool:latest
        env:
        - name: MARKET
          value: "hk"
        - name: MODE
          value: "live"
        ports:
        - containerPort: 8080
```

## 📊 监控指标

服务提供以下监控指标：

- `proxy_get_duration` - 代理获取耗时
- `proxy_repository_get_duration` - 仓储层获取耗时
- `proxy_failure_report_duration` - 失败报告耗时
- 池状态统计（活跃/备用池大小、成功率等）

## 🔄 Git仓库管理

项目包含完整的Git管理脚本：

```bash
# 执行完整设置流程
./git_setup.sh full

# 或分步执行
./git_setup.sh init    # 初始提交
./git_setup.sh create  # 创建GitHub仓库
./git_setup.sh push    # 推送到远程
```

## 🏢 项目集成

已集成到主项目的workspace中：

```toml
# pyproject.toml
[tool.uv.workspace]
members = [
    # ... 其他项目
    "saturn-mousehunter-proxy-pool",
]
```

可通过根目录管理脚本进行统一管理：

```bash
cd /home/cenwei/workspace/saturn_mousehunter
./manage_proxy_pool_project.sh setup
```

## License

MIT License