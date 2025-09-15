#!/bin/bash
# Git管理脚本 - 代理池微服务

set -e

PROJECT_NAME="saturn-mousehunter-proxy-pool"
GITHUB_ORG="cenwei"
REPO_URL="https://github.com/${GITHUB_ORG}/${PROJECT_NAME}.git"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查git配置
check_git_config() {
    echo_info "检查git配置..."

    if ! git config user.name >/dev/null 2>&1; then
        echo_warn "Git用户名未配置，设置为默认值"
        git config user.name "cenwei"
    fi

    if ! git config user.email >/dev/null 2>&1; then
        echo_warn "Git邮箱未配置，设置为默认值"
        git config user.email "cenwei@msn.com"
    fi

    echo_info "Git配置: $(git config user.name) <$(git config user.email)>"
}

# 初始提交
initial_commit() {
    echo_info "执行初始提交..."

    git add .
    git commit -m "feat: 初始化代理池轮换微服务

- 实现A/B轮换代理池机制
- 支持多市场时区管理
- 提供FastAPI管理接口和RPC接口
- 集成市场时钟自动生命周期管理
- 支持外部代理获取函数扩展
- 完整的Docker和部署配置

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    echo_info "初始提交完成"
}

# 创建GitHub仓库
create_github_repo() {
    echo_info "创建GitHub仓库..."

    # 检查gh命令是否可用
    if ! command -v gh &> /dev/null; then
        echo_error "GitHub CLI (gh) 未安装，请手动创建仓库: ${REPO_URL}"
        return 1
    fi

    # 创建仓库
    gh repo create "${GITHUB_ORG}/${PROJECT_NAME}" \
        --description "Saturn MouseHunter代理池轮换微服务 - 支持A/B轮换机制和多市场时区管理" \
        --public \
        --clone=false \
        --add-readme=false

    echo_info "GitHub仓库创建成功"
}

# 推送到远程仓库
push_to_remote() {
    echo_info "推送到远程仓库..."

    git remote add origin "${REPO_URL}"
    git branch -M main
    git push -u origin main

    echo_info "推送完成: ${REPO_URL}"
}

# 主函数
main() {
    echo_info "=== 代理池微服务Git仓库初始化 ==="

    # 检查是否在正确的目录
    if [[ ! -f "pyproject.toml" ]] || [[ ! -d "src/saturn_mousehunter_proxy_pool" ]]; then
        echo_error "请在项目根目录运行此脚本"
        exit 1
    fi

    case "${1:-}" in
        "init")
            check_git_config
            initial_commit
            ;;
        "create")
            create_github_repo
            ;;
        "push")
            push_to_remote
            ;;
        "full")
            check_git_config
            initial_commit
            create_github_repo
            sleep 2  # 等待GitHub仓库创建完成
            push_to_remote
            ;;
        *)
            echo "用法: $0 {init|create|push|full}"
            echo ""
            echo "命令说明:"
            echo "  init   - 检查配置并执行初始提交"
            echo "  create - 创建GitHub仓库"
            echo "  push   - 推送到远程仓库"
            echo "  full   - 执行完整流程 (init + create + push)"
            echo ""
            echo "示例:"
            echo "  $0 full    # 执行完整的git仓库创建流程"
            exit 1
            ;;
    esac

    echo_info "=== 操作完成 ==="
}

main "$@"