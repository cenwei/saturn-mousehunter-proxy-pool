# Saturn MouseHunter 代理池 Kotlin 序列化对象维护规则

## 📋 重要维护规则 (持久化规则)

### 🔄 规则1: JSON接口变更同步更新
**规则**: 当API接口JSON字段发生变更时，必须同步修订Kotlin序列化对象
**影响文件**:
- `/docs/ProxyPoolApiModels.kt` - 主要序列化数据类
- `/docs/KotlinClientUsageExample.kt` - 使用示例代码

**维护流程**:
1. 监控API接口JSON字段变更
2. 立即更新对应的@SerialName映射
3. 验证序列化/反序列化兼容性
4. 更新使用示例中的相关代码
5. 测试确认客户端正常工作

### 📌 规则2: 接口端点版本化管理
**规则**: 文档中的API端点不允许来回修订，只允许使用一个接口地址，保持版本持续更新，不要更改端点名称

**固定端点策略**:
- **基础URL**: `http://192.168.8.168:8001/api/v1` (不可变更)
- **端点路径**: 一旦确定不允许修改，只允许功能增强
- **版本管理**: 通过v1, v2版本前缀管理重大变更

**示例**:
```
✅ 正确做法:
/api/v1/status -> 持续维护和增强
/api/v2/status -> 新版本 (重大变更时)

❌ 错误做法:
/api/v1/status -> /api/v1/proxy-status (不允许重命名)
```

## 🔧 维护检查清单

### JSON字段变更检查
- [ ] 检查所有@SerialName是否匹配新的JSON字段名
- [ ] 验证数据类型是否兼容 (String, Int, Boolean等)
- [ ] 确认可空性设置正确 (nullable vs non-null)
- [ ] 测试序列化和反序列化功能
- [ ] 更新相关的使用示例代码

### 端点稳定性检查
- [ ] 确认不修改现有端点路径
- [ ] 新功能通过现有端点扩展参数实现
- [ ] 版本变更时使用新的版本前缀
- [ ] 保持向后兼容性

## 📁 关键文件清单

### 核心序列化文件
1. **ProxyPoolApiModels.kt**
   - 位置: `/docs/ProxyPoolApiModels.kt`
   - 用途: 主要序列化数据类定义
   - 维护频率: 随API变更立即更新

2. **KotlinClientUsageExample.kt**
   - 位置: `/docs/KotlinClientUsageExample.kt`
   - 用途: 客户端使用示例和工具类
   - 维护频率: API变更后验证更新

3. **KOTLIN_CLIENT_INFO.md**
   - 位置: `/docs/KOTLIN_CLIENT_INFO.md`
   - 用途: 客户端信息和基础配置
   - 维护频率: 框架升级时更新

4. **KOTLIN_QUICKLY_INTEGRATION_GUIDE.md**
   - 位置: `/docs/KOTLIN_QUICKLY_INTEGRATION_GUIDE.md`
   - 用途: 完整集成指南
   - 维护频率: 重大功能变更时更新

### API文档文件
5. **proxy_pool_openapi.json**
   - 位置: `/docs/proxy_pool_openapi.json`
   - 用途: OpenAPI 3.0规范定义
   - 维护频率: API变更时同步更新

6. **proxy-pool-api-types.ts**
   - 位置: `/docs/proxy-pool-api-types.ts`
   - 用途: TypeScript类型定义 (备用)
   - 维护频率: 需要时更新

## 🚨 关键维护点

### 高频变更点
1. **枚举值扩展**: 新增市场代码、操作状态等
2. **响应字段增加**: 统计信息、配置参数等新字段
3. **请求参数变化**: 批量操作、配置更新参数
4. **错误码定义**: 新的错误类型和错误码

### 兼容性要求
- **向后兼容**: 新字段必须设为可选 (nullable 或 default值)
- **字段重命名**: 通过@SerialName保持兼容，内部可改名
- **类型变更**: 避免破坏性类型变更，使用适配器模式

## 📋 版本管理策略

### 语义化版本控制
```kotlin
/**
 * Saturn MouseHunter 代理池系统 - Kotlin 序列化数据类
 *
 * @version 2.1.0  <- 主版本.次版本.修复版本
 * @apiVersion v1  <- API版本
 * @generated 2025-09-18
 * @client Kotlin Quickly Framework
 */
```

### 版本变更规则
- **主版本 (2.x.x)**: API重大变更，可能不兼容
- **次版本 (x.1.x)**: 新增功能，向后兼容
- **修复版本 (x.x.1)**: Bug修复，完全兼容

## 🔍 监控和验证

### 自动化检查
```bash
# 序列化测试脚本
./scripts/test_kotlin_serialization.sh

# API兼容性测试
./scripts/test_api_compatibility.sh
```

### 手动验证步骤
1. 对比新旧API响应JSON结构
2. 运行Kotlin序列化测试用例
3. 验证客户端使用示例正常工作
4. 检查错误处理逻辑
5. 确认性能无明显退化

---

**重要提醒**: 这些规则是为了确保 Kotlin Quickly 客户端的稳定性和开发效率，避免因API变更导致的反复试错。请严格遵守这些维护规则！