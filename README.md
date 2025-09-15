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

### 安装依赖

```bash
# 在项目根目录
cd /home/cenwei/workspace/saturn_mousehunter
uv install

# 或在微服务目录
cd saturn-mousehunter-proxy-pool
uv install
```

### 启动服务

```bash
# 方式1：使用入口脚本
python src/main.py

# 方式2：使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080 --app-dir src

# 方式3：使用项目脚本
saturn-mousehunter-proxy-pool
```

### 环境变量配置

```bash
# 基础配置
export MARKET=hk                    # 市场代码
export MODE=live                    # 运行模式
export AUTO_RUN=true               # 自动启动
export PORT=8080                   # 服务端口

# 代理池配置
export POOL_TYPE=memory_ab         # 池类型
export TARGET_SIZE=20              # 目标池大小
export ROTATE_INTERVAL_SEC=180     # 轮换间隔
export LOW_WATERMARK=5             # 低水位线

# 日志配置
export LOG_LEVEL=INFO              # 日志级别
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