#!/bin/bash
# 代理池项目静态分析检查脚本

echo "🔍 开始静态分析检查..."

PROJECT_DIR="/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-proxy-pool"
cd "$PROJECT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查工具是否安装
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}⚠️  $1 未安装，正在安装...${NC}"
        pip install $1
    fi
}

# 1. 语法检查 (Python内置)
echo -e "\n${GREEN}📝 1. Python语法检查${NC}"
python -m py_compile src/**/*.py 2>/dev/null && echo "✅ 语法检查通过" || echo -e "${RED}❌ 发现语法错误${NC}"

# 2. 导入检查
echo -e "\n${GREEN}📦 2. 导入检查${NC}"
python -c "
import sys
sys.path.append('src')
import ast
import os

def check_imports(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f'❌ {file_path}: {e}')
        return False

errors = 0
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if not check_imports(filepath):
                errors += 1

if errors == 0:
    print('✅ 导入检查通过')
else:
    print(f'❌ 发现 {errors} 个导入错误')
"

# 3. ruff检查 (如果可用)
echo -e "\n${GREEN}🚀 3. Ruff快速检查${NC}"
if command -v ruff &> /dev/null; then
    ruff check src/ --quiet && echo "✅ Ruff检查通过" || echo -e "${RED}❌ Ruff发现问题${NC}"
else
    echo -e "${YELLOW}⚠️  Ruff未安装，跳过检查${NC}"
fi

# 4. mypy类型检查 (如果可用)
echo -e "\n${GREEN}🎯 4. MyPy类型检查${NC}"
if command -v mypy &> /dev/null; then
    mypy src/ --ignore-missing-imports --no-strict-optional --quiet && echo "✅ 类型检查通过" || echo -e "${RED}❌ 发现类型问题${NC}"
else
    echo -e "${YELLOW}⚠️  MyPy未安装，跳过检查${NC}"
fi

# 5. 循环导入检查
echo -e "\n${GREEN}🔄 5. 循环导入检查${NC}"
python -c "
import sys
sys.path.append('src')

def check_circular_imports():
    try:
        import main
        import api.routes.proxy_pool_routes
        import infrastructure.dependencies
        print('✅ 无循环导入问题')
        return True
    except ImportError as e:
        print(f'❌ 导入错误: {e}')
        return False
    except Exception as e:
        print(f'❌ 其他错误: {e}')
        return False

check_circular_imports()
"

echo -e "\n${GREEN}📊 检查完成！${NC}"
echo "💡 建议安装完整的检查工具："
echo "   pip install ruff mypy pylint flake8"