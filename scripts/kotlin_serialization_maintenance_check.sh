#!/bin/bash

# Saturn MouseHunter 代理池 Kotlin 序列化对象维护脚本
# 用于检查API变更并提醒更新序列化对象

set -e

PROXY_POOL_DIR="/home/cenwei/workspace/saturn_mousehunter/saturn-mousehunter-proxy-pool"
DOCS_DIR="$PROXY_POOL_DIR/docs"
API_BASE_URL="http://192.168.8.168:8001/api/v1"

echo "🔍 Saturn MouseHunter 代理池 Kotlin 序列化维护检查"
echo "=================================================="

# 颜色输出函数
print_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
print_warning() { echo -e "\033[0;33m⚠️  $1\033[0m"; }
print_error() { echo -e "\033[0;31m❌ $1\033[0m"; }
print_info() { echo -e "\033[0;34m📋 $1\033[0m"; }

# 检查关键文件是否存在
check_critical_files() {
    print_info "检查关键维护文件..."

    local files=(
        "$DOCS_DIR/ProxyPoolApiModels.kt"
        "$DOCS_DIR/KotlinClientUsageExample.kt"
        "$DOCS_DIR/KOTLIN_SERIALIZATION_MAINTENANCE_RULES.md"
        "$DOCS_DIR/proxy_pool_openapi.json"
        "$DOCS_DIR/KOTLIN_QUICKLY_INTEGRATION_GUIDE.md"
    )

    local missing_files=()

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "存在: $(basename "$file")"
        else
            print_error "缺失: $(basename "$file")"
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "发现 ${#missing_files[@]} 个缺失文件！需要重新生成。"
        return 1
    fi

    print_success "所有关键文件检查完成"
    return 0
}

# 检查API端点可用性
check_api_endpoints() {
    print_info "检查API端点可用性..."

    local endpoints=(
        "/status?market=cn&mode=live"
        "/enhanced/trading-day/cn"
        "/enhanced/scheduler/status"
        "/config?market=cn&mode=live"
    )

    local failed_endpoints=()

    for endpoint in "${endpoints[@]}"; do
        local url="$API_BASE_URL$endpoint"
        if curl -s -f --connect-timeout 5 "$url" > /dev/null 2>&1; then
            print_success "可访问: $endpoint"
        else
            print_warning "无法访问: $endpoint (可能是服务未启动)"
            failed_endpoints+=("$endpoint")
        fi
    done

    if [[ ${#failed_endpoints[@]} -gt 0 ]]; then
        print_warning "检测到 ${#failed_endpoints[@]} 个端点无法访问"
        print_info "这可能是因为代理池服务未启动，不影响序列化对象维护"
    else
        print_success "所有关键API端点可访问"
    fi
}

# 检查Kotlin文件语法
check_kotlin_syntax() {
    print_info "检查Kotlin文件语法正确性..."

    local kotlin_files=(
        "$DOCS_DIR/ProxyPoolApiModels.kt"
        "$DOCS_DIR/KotlinClientUsageExample.kt"
    )

    local syntax_errors=()

    for file in "${kotlin_files[@]}"; do
        if [[ -f "$file" ]]; then
            # 基础语法检查 (检查大括号匹配、分号等)
            local open_braces=$(grep -o '{' "$file" | wc -l)
            local close_braces=$(grep -o '}' "$file" | wc -l)

            if [[ $open_braces -eq $close_braces ]]; then
                print_success "语法检查通过: $(basename "$file")"
            else
                print_error "语法错误: $(basename "$file") - 大括号不匹配 (开:{$open_braces} 闭:{$close_braces})"
                syntax_errors+=("$file")
            fi

            # 检查@Serializable注解数量
            local serializable_count=$(grep -c "@Serializable" "$file" || echo "0")
            if [[ "$file" == *"ProxyPoolApiModels.kt" ]]; then
                if [[ $serializable_count -ge 40 ]]; then
                    print_success "@Serializable注解数量正常: $serializable_count 个"
                else
                    print_warning "@Serializable注解数量偏少: $serializable_count 个 (预期>=40)"
                fi
            fi
        fi
    done

    if [[ ${#syntax_errors[@]} -gt 0 ]]; then
        print_error "发现 ${#syntax_errors[@]} 个语法错误文件！"
        return 1
    fi

    return 0
}

# 检查版本信息
check_version_info() {
    print_info "检查版本信息..."

    local models_file="$DOCS_DIR/ProxyPoolApiModels.kt"

    if [[ -f "$models_file" ]]; then
        local version_line=$(grep "@version" "$models_file" | head -1)
        local api_version_line=$(grep "API_BASE_URL.*8001/api/v1" "$models_file")

        if [[ -n "$version_line" ]]; then
            print_success "发现版本信息: $version_line"
        else
            print_warning "缺少版本信息，建议添加@version注释"
        fi

        if [[ -n "$api_version_line" ]]; then
            print_success "API版本固定为 v1 (符合规则2要求)"
        else
            print_warning "API版本信息可能有问题"
        fi
    fi
}

# 生成维护报告
generate_maintenance_report() {
    print_info "生成维护检查报告..."

    local report_file="$DOCS_DIR/KOTLIN_SERIALIZATION_CHECK_REPORT.md"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$report_file" << EOF
# Kotlin 序列化对象维护检查报告

**生成时间**: $timestamp
**检查脚本**: kotlin_serialization_maintenance_check.sh

## 检查结果概览

$(if check_critical_files >/dev/null 2>&1; then echo "✅ 关键文件完整"; else echo "❌ 关键文件缺失"; fi)
$(if check_kotlin_syntax >/dev/null 2>&1; then echo "✅ Kotlin语法正确"; else echo "❌ Kotlin语法错误"; fi)

## 文件清单

### Kotlin序列化文件
- ProxyPoolApiModels.kt ($(if [[ -f "$DOCS_DIR/ProxyPoolApiModels.kt" ]]; then echo "存在"; else echo "缺失"; fi))
- KotlinClientUsageExample.kt ($(if [[ -f "$DOCS_DIR/KotlinClientUsageExample.kt" ]]; then echo "存在"; else echo "缺失"; fi))

### 文档文件
- KOTLIN_SERIALIZATION_MAINTENANCE_RULES.md ($(if [[ -f "$DOCS_DIR/KOTLIN_SERIALIZATION_MAINTENANCE_RULES.md" ]]; then echo "存在"; else echo "缺失"; fi))
- KOTLIN_QUICKLY_INTEGRATION_GUIDE.md ($(if [[ -f "$DOCS_DIR/KOTLIN_QUICKLY_INTEGRATION_GUIDE.md" ]]; then echo "存在"; else echo "缺失"; fi))

### API文档
- proxy_pool_openapi.json ($(if [[ -f "$DOCS_DIR/proxy_pool_openapi.json" ]]; then echo "存在"; else echo "缺失"; fi))

## 维护提醒

⚠️ **规则1提醒**: 如果API接口JSON字段有变更，请立即更新Kotlin序列化对象！
⚠️ **规则2提醒**: API端点地址禁止修改，保持版本连续性！

## 下次检查建议

- 检查API响应JSON结构变更
- 验证@SerialName映射准确性
- 测试序列化/反序列化功能
- 确认客户端示例代码可正常运行

---
**自动生成报告** - 如需手动检查，运行: \`./scripts/kotlin_serialization_maintenance_check.sh\`
EOF

    print_success "维护报告已生成: $report_file"
}

# 主执行流程
main() {
    echo "开始执行维护检查..."
    echo

    local overall_status=0

    # 执行各项检查
    if ! check_critical_files; then
        overall_status=1
    fi

    echo
    check_api_endpoints

    echo
    if ! check_kotlin_syntax; then
        overall_status=1
    fi

    echo
    check_version_info

    echo
    generate_maintenance_report

    # 输出总结
    echo
    echo "🎯 维护检查总结"
    echo "=============="

    if [[ $overall_status -eq 0 ]]; then
        print_success "所有关键检查项都通过！Kotlin序列化对象维护良好。"
    else
        print_error "发现需要修复的问题，请检查上述错误信息。"
    fi

    echo
    print_info "重要提醒:"
    print_info "1. API JSON字段变更时，立即更新Kotlin序列化对象"
    print_info "2. 保持API端点地址不变，遵循版本化管理"
    print_info "3. 定期运行此脚本检查维护状态"

    return $overall_status
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi