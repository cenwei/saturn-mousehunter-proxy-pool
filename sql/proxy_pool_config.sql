-- 代理池配置表
CREATE TABLE IF NOT EXISTS proxy_pool_config (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    market VARCHAR(10) NOT NULL COMMENT '市场代码: cn/hk/us',
    mode VARCHAR(20) NOT NULL DEFAULT 'live' COMMENT '模式: live/backfill',

    -- 海量代理配置
    hailiang_api_url TEXT NOT NULL COMMENT '海量代理API URL',
    hailiang_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用海量代理',

    -- 代理池参数
    batch_size INT NOT NULL DEFAULT 400 COMMENT '每批获取代理数量',
    proxy_lifetime_minutes INT NOT NULL DEFAULT 10 COMMENT '代理生命周期(分钟)',
    rotation_interval_minutes INT NOT NULL DEFAULT 7 COMMENT 'A/B池轮换间隔(分钟)',
    low_watermark INT NOT NULL DEFAULT 50 COMMENT '低水位线',
    target_size INT NOT NULL DEFAULT 200 COMMENT '目标池大小',

    -- 交易日配置
    auto_start_enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否自动开启',
    pre_market_start_minutes INT NOT NULL DEFAULT 30 COMMENT '盘前提前启动时间(分钟)',
    post_market_stop_minutes INT NOT NULL DEFAULT 30 COMMENT '盘后延迟关闭时间(分钟)',

    -- backfill模式配置
    backfill_enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否启用backfill模式',
    backfill_duration_hours INT NOT NULL DEFAULT 2 COMMENT 'backfill运行时长(小时)',

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',

    UNIQUE KEY uk_market_mode (market, mode),
    INDEX idx_market (market),
    INDEX idx_active (is_active)
) COMMENT='代理池配置表';

-- 插入默认配置
INSERT IGNORE INTO proxy_pool_config (
    market, mode, hailiang_api_url, hailiang_enabled,
    batch_size, proxy_lifetime_minutes, rotation_interval_minutes,
    low_watermark, target_size,
    auto_start_enabled, pre_market_start_minutes, post_market_stop_minutes
) VALUES
-- CN市场配置
('cn', 'live', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, TRUE, 30, 30),

-- HK市场配置
('hk', 'live', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, TRUE, 30, 30),

-- US市场配置
('us', 'live', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, TRUE, 30, 30),

-- Backfill模式配置
('cn', 'backfill', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, FALSE, 0, 0),
('hk', 'backfill', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, FALSE, 0, 0),
('us', 'backfill', 'http://api.hailiangip.com:8422/api/getIp?type=1&num=400&pid=-1&unbindTime=600&cid=-1&orderId=O25062920421786879509&time=1751266950&sign=d758b85241594a8b751147b511b836bf&noDuplicate=1&dataType=0&lineSeparator=0', TRUE,
 400, 10, 7, 50, 200, FALSE, 0, 0);

-- 代理池运行状态表
CREATE TABLE IF NOT EXISTS proxy_pool_status (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    market VARCHAR(10) NOT NULL,
    mode VARCHAR(20) NOT NULL DEFAULT 'live',

    -- 运行状态
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMP NULL,
    stopped_at TIMESTAMP NULL,
    last_rotation_at TIMESTAMP NULL,

    -- 统计信息
    active_pool VARCHAR(1) NOT NULL DEFAULT 'A' COMMENT '当前活跃池: A/B',
    pool_a_size INT NOT NULL DEFAULT 0,
    pool_b_size INT NOT NULL DEFAULT 0,
    total_requests BIGINT NOT NULL DEFAULT 0,
    success_count BIGINT NOT NULL DEFAULT 0,
    failure_count BIGINT NOT NULL DEFAULT 0,
    success_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,

    -- 元数据
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_market_mode_status (market, mode),
    INDEX idx_running (is_running),
    INDEX idx_market_status (market)
) COMMENT='代理池运行状态表';