# Saturn MouseHunter 代理池服务文档中心

> 代理池轮换微服务完整文档集合

## 📚 文档导航

### 🚀 快速开始

| 文档 | 描述 | 适用对象 |
|------|------|----------|
| [Kotlin 快速集成指南](kotlin-quick-start.md) | 5分钟快速上手，最简单的集成方式 | Kotlin 开发者 |
| [完整 API 规范](fastapi-kotlin-integration.md) | 详细的接口文档和集成示例 | 所有开发者 |
| [OpenAPI 规范](openapi.yaml) | 标准化 API 规范，可生成客户端代码 | 自动化集成 |

### 📖 系统文档

| 文档 | 描述 | 适用对象 |
|------|------|----------|
| [系统设计文档](README.md) | 完整的架构设计、部署和运维指南 | 架构师、运维 |
| [Cache 集成指南](cache_integration_guide.md) | 缓存集成和性能优化 | 后端开发者 |

### 🔧 开发工具

| 工具 | 描述 | 用途 |
|------|------|------|
| [Swagger UI](http://localhost:8080/docs) | 交互式 API 文档 | 接口测试 |
| [Web 管理界面](http://localhost:8080) | 可视化管理控制台 | 运维管理 |

## 🎯 快速选择指南

### 我是 Kotlin 开发者
👉 直接阅读 [Kotlin 快速集成指南](kotlin-quick-start.md)

### 我需要完整的 API 参考
👉 查看 [完整 API 规范](fastapi-kotlin-integration.md)

### 我要自动生成客户端代码
👉 使用 [OpenAPI 规范](openapi.yaml)

### 我负责系统部署运维
👉 参考 [系统设计文档](README.md)

## 🔗 核心接口速查

### 最重要的3个接口

#### 1. 获取代理
```bash
curl -X POST "http://localhost:8080/api/v1/rpc" \
  -H "Content-Type: application/json" \
  -d '{"event":"get_proxy","market":"hk","mode":"live"}'
```

#### 2. 报告失败
```bash
curl -X POST "http://localhost:8080/api/v1/rpc" \
  -H "Content-Type: application/json" \
  -d '{"event":"report_failure","market":"hk","proxy_addr":"192.168.1.100:8080"}'
```

#### 3. 健康检查
```bash
curl -X GET "http://localhost:8080/api/v1/status?market=hk"
```

## 📋 支持的市场

| 市场 | 代码 | 交易时间 | 时区 |
|------|------|----------|------|
| 中国A股 | `cn` | 09:30-15:10 | GMT+8 |
| 香港股市 | `hk` | 09:30-16:15 | GMT+8 |
| 美股 | `us` | 09:30-16:00 | GMT-5 |

## 🌐 环境地址

| 环境 | 地址 | 用途 |
|------|------|------|
| 开发 | `http://localhost:8080` | 本地开发测试 |
| 测试 | `http://proxy-pool-test.saturn.com:8080` | 集成测试 |
| 生产 | `http://proxy-pool.saturn.com:8080` | 生产环境 |

## 💡 最佳实践

### Kotlin 项目集成
1. 使用 [快速集成指南](kotlin-quick-start.md) 中的 `ProxyPoolClient`
2. 必须在代理失败时调用 `reportFailure`
3. 实现重试机制和异常处理
4. 定期检查服务健康状态

### 生产环境使用
1. 配置合适的超时时间（建议 10 秒）
2. 实现降级方案（代理服务不可用时的备选方案）
3. 监控代理使用情况和成功率
4. 定期检查告警信息

### 性能优化
1. 缓存代理地址 5 分钟以减少请求频率
2. 使用连接池复用 HTTP 连接
3. 并行请求多个代理提高容错性
4. 根据成功率动态调整请求频率

## 🆘 故障排除

### 常见问题
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 获取不到代理 | 代理池为空或服务未启动 | 检查服务状态，等待代理池刷新 |
| 代理连接失败 | 代理地址无效或网络问题 | 报告失败，获取新代理 |
| 服务不响应 | 网络故障或服务停机 | 检查网络，使用健康检查接口 |

### 联系支持
- 📧 邮箱: support@saturn.com
- 💬 内部群: Saturn MouseHunter 技术支持群
- 📞 紧急热线: 400-SATURN-1 (仅生产环境问题)

---

**选择适合你的文档开始使用吧！** 🚀