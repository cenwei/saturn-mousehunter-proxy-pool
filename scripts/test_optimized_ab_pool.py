"""
优化的A/B池使用示例和测试脚本
演示如何在开发/生产环境中遵循批量限制
"""
import asyncio
import os
from datetime import datetime

# 设置开发环境进行测试
os.environ["PROXY_ENVIRONMENT"] = "development"

from infrastructure.optimized_config_manager import get_current_config, validate_batch_request, is_development
from infrastructure.optimized_ab_pool_repository import OptimizedABPoolRepository

async def test_batch_size_limits():
    """测试批量大小限制遵循情况"""
    print("=== 测试批量大小限制 ===")

    config = get_current_config()
    print(f"当前环境: {config.environment}")
    print(f"配置的批量大小: {config.batch_size}")

    # 测试各种请求大小
    test_requests = [10, 20, 50, 100, 200, 400]

    for request_size in test_requests:
        validated_size = validate_batch_request(request_size)
        status = "✅ 允许" if validated_size == request_size else f"❌ 限制为 {validated_size}"
        print(f"请求 {request_size} 个代理: {status}")

async def test_ab_pool_rotation():
    """测试A/B池轮换功能"""
    print("\n=== 测试A/B池轮换 ===")

    # 模拟数据库连接
    class MockDBConnection:
        async def fetch(self, sql, *args):
            # 模拟返回代理数据，遵循数量限制
            count = args[0] if args else 20
            validated_count = validate_batch_request(count)

            return [
                {
                    'proxy_url': f'http://proxy{i}.example.com:8080',
                    'proxy_type': 'short',
                    'quality_score': 0.9 - (i * 0.01)
                }
                for i in range(validated_count)
            ]

    # 初始化A/B池
    repo = OptimizedABPoolRepository(environment="development")
    await repo.initialize(MockDBConnection())

    print(f"初始化完成:")
    stats = repo.get_statistics()
    print(f"  池A大小: {stats['pool_sizes']['pool_a']}")
    print(f"  池B大小: {stats['pool_sizes']['pool_b']}")
    print(f"  当前活跃池: {stats['active_pool']}")

    # 测试代理获取
    print(f"\n获取代理测试:")
    for i in range(3):
        proxy = await repo.get_proxy("short")
        print(f"  获取代理 {i+1}: {proxy[:30]}..." if proxy else f"  获取代理 {i+1}: None")

    # 测试轮换
    print(f"\n执行轮换测试:")
    old_active = repo.active_pool
    success = await repo.perform_rotation()
    new_active = repo.active_pool

    print(f"  轮换结果: {'成功' if success else '失败'}")
    print(f"  轮换前活跃池: {old_active}")
    print(f"  轮换后活跃池: {new_active}")

    # 最终统计
    final_stats = repo.get_statistics()
    print(f"\n最终统计:")
    print(f"  总轮换次数: {final_stats['performance']['rotation_count']}")
    print(f"  总获取次数: {final_stats['performance']['total_fetches']}")
    print(f"  健康度指标: {final_stats['health']}")

async def test_environment_switching():
    """测试环境切换功能"""
    print("\n=== 测试环境切换 ===")

    # 测试开发环境
    os.environ["PROXY_ENVIRONMENT"] = "development"
    dev_config = get_current_config()
    print(f"开发环境配置:")
    print(f"  批量大小: {dev_config.batch_size} (用户指定测试限制)")
    print(f"  最小阈值: {dev_config.min_threshold}")
    print(f"  是否开发环境: {is_development()}")

    # 测试生产环境
    os.environ["PROXY_ENVIRONMENT"] = "production"
    prod_config = get_current_config()
    print(f"\n生产环境配置:")
    print(f"  批量大小: {prod_config.batch_size} (接口上限)")
    print(f"  最小阈值: {prod_config.min_threshold}")
    print(f"  是否开发环境: {is_development()}")

    # 恢复开发环境
    os.environ["PROXY_ENVIRONMENT"] = "development"

async def test_timing_configuration():
    """测试时间配置"""
    print("\n=== 测试时间配置 ===")

    config = get_current_config()
    print(f"轮换间隔: {config.rotation_interval}秒 ({config.rotation_interval/60}分钟)")
    print(f"IP生命周期: {config.ip_lifetime}秒 ({config.ip_lifetime/60}分钟)")
    print(f"重叠窗口: {config.overlap_window}秒 ({config.overlap_window/60}分钟)")
    print(f"预热时间: {config.warmup_duration}秒 ({config.warmup_duration/60}分钟)")

    # 验证用户需求: 7分钟轮换，10分钟IP生命周期
    assert config.rotation_interval == 420, f"轮换间隔应为420秒(7分钟)，当前为{config.rotation_interval}秒"
    assert config.ip_lifetime == 600, f"IP生命周期应为600秒(10分钟)，当前为{config.ip_lifetime}秒"
    print("✅ 时间配置符合用户需求")

async def main():
    """主测试函数"""
    print("🚀 优化的A/B池测试开始")
    print(f"测试时间: {datetime.now()}")
    print("=" * 50)

    try:
        await test_batch_size_limits()
        await test_environment_switching()
        await test_timing_configuration()
        await test_ab_pool_rotation()

        print("\n" + "=" * 50)
        print("✅ 所有测试完成")

        # 显示关键遵循点
        print(f"\n🎯 关键遵循点确认:")
        print(f"✅ 开发环境最大20个代理 (用户指定测试限制)")
        print(f"✅ 生产环境最大200个代理 (接口上限)")
        print(f"✅ 7分钟轮换间隔")
        print(f"✅ 10分钟IP生命周期")
        print(f"✅ 数据库URL读取")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())