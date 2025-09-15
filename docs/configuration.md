# 代理池服务配置说明

> 代理池服务现在使用 saturn-mousehunter-shared 中的统一服务端点配置

## 🔧 配置集成

代理池服务的 `main.py` 现在会自动读取 `/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src/saturn_mousehunter_shared/config/service_endpoints.py` 中定义的服务端点配置。

## 🌐 环境配置

### 开发环境 (development)
```
Host: 192.168.8.168
Port: 8005
Base URL: http://192.168.8.168:8005
```

### 测试环境 (testing)
```
Host: test-proxy-pool
Port: 8005
Base URL: http://test-proxy-pool:8080
```

### 生产环境 (production)
```
Host: proxy-pool.saturn-mousehunter.internal
Port: 8005
Base URL: http://proxy-pool.saturn-mousehunter.internal:8005
```

## 🚀 启动方式

### 方式1: 使用启动脚本（推荐）

```bash
# 开发环境
./start.sh

# 指定环境
ENVIRONMENT=testing ./start.sh

# 指定市场
ENVIRONMENT=development MARKETS=cn,hk,us ./start.sh
```

### 方式2: 直接运行

```bash
# 开发环境
ENVIRONMENT=development MARKETS=hk python src/main.py

# 测试环境
ENVIRONMENT=testing MARKETS=cn,hk,us python src/main.py

# 生产环境
ENVIRONMENT=production MARKETS=cn,hk,us python src/main.py
```

### 方式3: 环境变量文件

创建 `.env` 文件：
```env
ENVIRONMENT=development
MARKETS=cn,hk,us
LOG_LEVEL=INFO
```

然后运行：
```bash
python src/main.py
```

## 📋 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|-------|------|
| `ENVIRONMENT` | `development` | 运行环境：development/testing/production |
| `MARKETS` | `hk` | 启动的市场，逗号分隔：cn,hk,us |
| `HOST` | 从配置读取 | 覆盖配置中的主机地址 |
| `PORT` | 从配置读取 | 覆盖配置中的端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEBUG` | `false` | 调试模式 |

## 🔍 配置验证

运行配置验证脚本：
```bash
python verify_shared_config.py
```

预期输出：
```
✅ 共享配置模块导入成功
✅ 开发环境配置符合预期
✅ 配置验证完成！
```

## 🌟 配置优先级

1. **环境变量** (最高优先级)
   - `HOST`, `PORT` 等环境变量会覆盖配置文件

2. **共享配置文件** (中等优先级)
   - `service_endpoints.py` 中的配置

3. **默认值** (最低优先级)
   - 代码中的硬编码默认值

## 📊 访问地址

### 开发环境
- **管理界面**: http://192.168.8.168:8005
- **API文档**: http://192.168.8.168:8005/docs
- **健康检查**: http://192.168.8.168:8005/health

### 测试环境
- **管理界面**: http://test-proxy-pool:8005
- **API文档**: http://test-proxy-pool:8005/docs
- **健康检查**: http://test-proxy-pool:8005/health

### 生产环境
- **管理界面**: http://proxy-pool.saturn-mousehunter.internal:8005
- **API文档**: http://proxy-pool.saturn-mousehunter.internal:8005/docs
- **健康检查**: http://proxy-pool.saturn-mousehunter.internal:8005/health

## 🔧 故障排除

### 配置文件找不到
```bash
❌ Failed to load service endpoint config: ..., using defaults
```

**解决方案**: 确保 saturn-mousehunter-shared 项目路径正确，或设置 `PYTHONPATH`：
```bash
export PYTHONPATH="/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-shared/src:$PYTHONPATH"
```

### 端口被占用
```bash
❌ Error: [Errno 98] Address already in use
```

**解决方案**:
1. 检查端口占用：`netstat -tulpn | grep 8005`
2. 终止占用进程或使用其他端口：`PORT=8006 python src/main.py`

### 依赖缺失
```bash
❌ ModuleNotFoundError: No module named 'httpx'
```

**解决方案**: 安装依赖
```bash
pip install -r requirements.txt
# 或
pip install httpx fastapi uvicorn
```

## 🎯 最佳实践

1. **使用环境变量**：通过 `ENVIRONMENT` 变量切换环境
2. **统一配置**：所有服务端点都在 `service_endpoints.py` 中管理
3. **日志记录**：启动时会输出当前使用的配置信息
4. **健康检查**：定期访问 `/health` 端点检查服务状态

---

**现在代理池服务完全集成了共享配置系统！** 🎉