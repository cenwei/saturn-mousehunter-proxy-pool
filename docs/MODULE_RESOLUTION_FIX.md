# IDE 模块解析路径混乱问题解决方案

## 问题描述

在 `saturn-mousehunter-proxy-pool` 项目中，当点击 IDE 中的 `from domain import IMarketClock` 时，IDE 跳转到了 `saturn-mousehunter-market-data` 项目，而不是当前项目的 domain 模块。

## 根本原因分析

### 1. 环境路径混乱
- Shell 工作目录总是被重置到 `saturn-mousehunter-market-data`
- IDE 的 Python 解释器配置可能指向了错误的项目根目录
- PYTHONPATH 配置不当，导致模块解析优先级错误

### 2. 模块名称冲突
两个项目都有 `domain` 模块：
- **Proxy Pool**: `/saturn-mousehunter-proxy-pool/src/domain/` (包含 `IMarketClock`)
- **Market Data**: `/saturn-mousehunter-market-data/src/domain/` (基本为空)

### 3. IDE 配置问题
IDE 的模块解析配置优先选择了 market-data 项目的路径。

## 解决方案

### 方案 1: 使用绝对导入（推荐）

将相对导入改为绝对导入，明确指定模块路径：

```python
# 修改前（容易混淆）
from domain import IMarketClock

# 修改后（明确路径）
from saturn_mousehunter_proxy_pool.domain import IMarketClock
```

### 方案 2: 项目特定的模块名称

为每个项目的 domain 模块使用不同的名称：

```python
# Proxy Pool 项目
from proxy_pool_domain import IMarketClock

# Market Data 项目
from market_data_domain import SomeEntity
```

### 方案 3: 修正 IDE 配置

#### PyCharm/IntelliJ IDEA
1. 打开项目设置 (File → Project Structure)
2. 设置正确的 Project Root
3. 配置 Python Interpreter 指向正确的虚拟环境
4. 设置 Source Folders 为各项目的 `src` 目录

#### VS Code
```json
// .vscode/settings.json
{
    "python.defaultInterpreter": "/home/cenwei/workspace/saturn_mousehunter/.venv/bin/python",
    "python.analysis.extraPaths": [
        "./src",
        "../saturn-mousehunter-shared/src"
    ],
    "python.analysis.autoSearchPaths": false
}
```

### 方案 4: 运行时路径修正

确保每个项目的 `main.py` 正确设置模块路径：

```python
# 在 main.py 开头
import os
import sys

# 添加当前项目的 src 目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir)  # 如果 main.py 在 src 目录
sys.path.insert(0, src_dir)

# 确保共享模块可用
shared_src = os.path.join(current_dir, '../../saturn-mousehunter-shared/src')
if os.path.exists(shared_src):
    sys.path.insert(0, shared_src)
```

## 实施修复

### 立即修复 - 使用绝对导入路径

修改 `/saturn-mousehunter-proxy-pool/src/infrastructure/market_clock.py`:

```python
# 修改前
from domain import IMarketClock

# 修改后 - 方案A: 使用相对导入
from ..domain import IMarketClock

# 或 修改后 - 方案B: 保持简洁但确保路径正确
from domain.entities import IMarketClock  # 更具体的导入
```

### 长期解决方案 - 项目结构规范化

1. **统一命名规范**：为每个服务的 domain 模块使用唯一名称
2. **IDE 工作区配置**：为 monorepo 配置正确的工作区设置
3. **PYTHONPATH 管理**：使用项目特定的环境配置

## 验证修复

### 测试导入解析
```bash
cd /home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-proxy-pool

# 测试正确的模块导入
PYTHONPATH=src uv run python -c "
from domain.entities import IMarketClock
print(f'✅ IMarketClock 导入成功: {IMarketClock}')
print(f'模块位置: {IMarketClock.__module__}')
"
```

### 检查 IDE 跳转
1. 修改导入语句后重启 IDE
2. 清除 IDE 缓存 (File → Invalidate Caches and Restart)
3. 重新索引项目文件

## 预防措施

### 1. 项目模板标准化
为每个新服务创建标准的项目模板，包含：
- 正确的 `main.py` 路径配置
- 标准的 IDE 配置文件
- 明确的模块导入规范

### 2. 开发环境检查脚本
```bash
#!/bin/bash
# 检查当前项目的模块解析是否正确
echo "=== 检查模块解析 ==="
PYTHONPATH=src python -c "
import sys
print('当前项目 src 路径:', 'src' in sys.path[0])

try:
    import domain
    print('✅ domain 模块路径:', domain.__file__)
except ImportError as e:
    print('❌ domain 导入失败:', e)
"
```

### 3. CI/CD 验证
在持续集成中添加模块导入测试，确保每个服务的模块都能正确解析。

---

**关键点**: 这是一个典型的 **monorepo 中模块命名冲突** 问题，主要通过改进导入策略和 IDE 配置来解决。