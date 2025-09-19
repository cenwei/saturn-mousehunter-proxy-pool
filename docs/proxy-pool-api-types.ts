/**
 * Saturn MouseHunter Proxy Pool API Types
 * TypeScript type definitions for front-end integration
 *
 * @version 2.0.0
 * @generated 2025-09-18
 */

// ============================================================================
// 基础类型定义
// ============================================================================

export type MarketCode = 'cn' | 'hk' | 'us';
export type MarketCodeUpper = 'CN' | 'HK' | 'US';
export type OperationMode = 'live' | 'backfill';
export type PoolName = 'A' | 'B';
export type ProxyType = 'short' | 'long';
export type OperationStatus = 'running' | 'stopped' | 'error';
export type RpcEvent = 'get_proxy' | 'report_failure' | 'get_status' | 'ping';

// 交易日类型
export type TradingDayType = 'NORMAL' | 'HALF_DAY' | 'HOLIDAY' | 'WEEKEND';
export type TradingSessionType = 'full_day' | 'morning_only' | 'afternoon_only';
export type DataSource = 'macl' | 'calendar_api';

// 操作结果状态
export type ServiceOperationStatus = 'started' | 'stopped' | 'already_running' | 'already_stopped' | 'error';
export type ForceOperationStatus = ServiceOperationStatus;
export type RpcResponseStatus = 'ok' | 'error';

// ============================================================================
// 核心数据结构
// ============================================================================

/**
 * 交易时间配置
 */
export interface TradingHours {
  /** 开市时间 (HH:MM) */
  start: string;
  /** 闭市时间 (HH:MM) */
  end: string;
  /** 午休时间 [开始时间, 结束时间] | null */
  lunch_break: [string, string] | null;
}

/**
 * 代理池统计信息
 */
export interface ProxyPoolStats {
  /** A池代理数量 */
  pool_a_size: number;
  /** B池代理数量 */
  pool_b_size: number;
  /** 当前活跃池 */
  active_pool: PoolName;
  /** 总代理数量 */
  total_proxies: number;
  /** 成功率 (0-100) */
  success_rate: number;
  /** 总请求数 */
  total_requests: number;
  /** 成功次数 */
  success_count: number;
  /** 失败次数 */
  failure_count: number;
  /** 最后轮换时间 (ISO 8601) */
  last_rotation_at: string;
  /** 启动时间 (ISO 8601) */
  started_at: string;
  /** 运行时长(秒) */
  uptime_seconds: number;
}

/**
 * 交易日信息
 */
export interface TradingDayInfo {
  /** 市场代码 */
  market: MarketCodeUpper;
  /** 日期 (YYYY-MM-DD) */
  date: string;
  /** 交易日类型 */
  day_type: TradingDayType;
  /** 交易时段类型 */
  session_type: TradingSessionType;
  /** 是否交易日 */
  is_trading_day: boolean;
  /** 状态描述 */
  status_description: string;
  /** 交易时间 (可选) */
  trading_hours?: TradingHours;
}

/**
 * 代理池配置
 */
export interface ProxyPoolConfig {
  /** 海量API地址 */
  hailiang_api_url: string;
  /** 是否启用海量 */
  hailiang_enabled: boolean;
  /** 批量大小 */
  batch_size: number;
  /** 代理生命周期(分钟) */
  proxy_lifetime_minutes: number;
  /** 轮换间隔(分钟) */
  rotation_interval_minutes: number;
  /** 低水位线 */
  low_watermark: number;
  /** 目标大小 */
  target_size: number;
  /** 自动启动 */
  auto_start_enabled: boolean;
  /** 盘前启动分钟数 */
  pre_market_start_minutes: number;
  /** 盘后停止分钟数 */
  post_market_stop_minutes: number;
  /** 回填启用 */
  backfill_enabled: boolean;
  /** 回填时长 */
  backfill_duration_hours: number;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at: string;
  /** 是否激活 */
  is_active: boolean;
}

// ============================================================================
// API请求类型
// ============================================================================

/**
 * RPC请求
 */
export interface RpcRequest {
  /** RPC事件类型 */
  event: RpcEvent;
  /** 代理类型 (可选) */
  proxy_type?: ProxyType;
  /** 代理地址 (report_failure时必需) */
  proxy_addr?: string;
  /** 市场代码 */
  market?: MarketCode;
  /** 运行模式 */
  mode?: OperationMode;
}

/**
 * 批量操作请求
 */
export interface BatchOperationRequest {
  /** 市场列表 */
  markets: MarketCode[];
  /** 运行模式 */
  mode?: OperationMode;
}

/**
 * 配置更新请求 (所有字段可选)
 */
export interface ConfigUpdateRequest {
  hailiang_api_url?: string;
  hailiang_enabled?: boolean;
  batch_size?: number;
  proxy_lifetime_minutes?: number;
  rotation_interval_minutes?: number;
  low_watermark?: number;
  target_size?: number;
  auto_start_enabled?: boolean;
  pre_market_start_minutes?: number;
  post_market_stop_minutes?: number;
  backfill_enabled?: boolean;
  backfill_duration_hours?: number;
}

// ============================================================================
// API响应类型
// ============================================================================

/**
 * 代理池状态响应
 */
export interface ProxyPoolStatusResponse {
  /** 运行状态 */
  status: OperationStatus;
  /** 是否运行中 */
  running: boolean;
  /** 市场代码 */
  market: string;
  /** 运行模式 */
  mode: string;
  /** 市场状态描述 */
  market_status: string;
  /** 统计信息 */
  stats: ProxyPoolStats;
}

/**
 * 服务操作响应 (启动)
 */
export interface ServiceOperationResponse {
  /** 操作状态 */
  status: ServiceOperationStatus;
  /** 状态描述信息 */
  message: string;
  /** 市场代码 */
  market: string;
  /** 运行模式 */
  mode: string;
  /** 启动时间 */
  started_at?: string;
  /** 配置信息 */
  config?: {
    batch_size: number;
    proxy_lifetime_minutes: number;
    rotation_interval_minutes: number;
    target_size: number;
    low_watermark: number;
  };
}

/**
 * 服务停止响应
 */
export interface ServiceStopResponse {
  /** 操作状态 */
  status: ServiceOperationStatus;
  /** 状态描述信息 */
  message: string;
  /** 市场代码 */
  market: string;
  /** 运行模式 */
  mode: string;
  /** 停止时间 */
  stopped_at?: string;
  /** 最终统计 */
  final_stats?: {
    total_runtime_seconds: number;
    total_requests_served: number;
    final_success_rate: number;
    total_rotations: number;
  };
}

/**
 * 获取代理响应
 */
export interface GetProxyResponse {
  /** 响应状态 */
  status: RpcResponseStatus;
  /** 代理地址 ip:port */
  proxy: string | null;
  /** 池信息 */
  pool_info?: {
    active_pool: PoolName;
    pool_size: number;
    proxy_age_seconds: number;
  };
  /** 市场信息 */
  market_info?: {
    market: string;
    is_trading_time: boolean;
    market_status: string;
  };
}

/**
 * 报告失败响应
 */
export interface ReportFailureResponse {
  /** 响应状态 */
  status: RpcResponseStatus;
  /** 处理结果描述 */
  message: string;
  /** 处理的代理地址 */
  proxy_addr: string;
  /** 采取的行动 */
  action_taken: 'marked_failed' | 'removed';
  /** 池影响 */
  pool_impact?: {
    affected_pool: PoolName | 'both';
    remaining_size: number;
  };
}

/**
 * RPC状态响应
 */
export interface RpcStatusResponse {
  /** 响应状态 */
  status: RpcResponseStatus;
  /** 统计信息 */
  stats?: Record<string, any>;
  /** 市场状态 */
  market_status?: string;
  /** 服务模式 */
  service_mode?: string;
}

/**
 * 市场实时状态响应
 */
export interface MarketRealtimeStatus extends TradingDayInfo {
  /** 当前时间 */
  current_time: string;
  /** 市场是否开盘 */
  is_market_open: boolean;
  /** 是否应该启动交易时段 */
  should_start_session: boolean;
  /** 是否应该停止交易时段 */
  should_stop_session: boolean;
}

/**
 * 市场调度器信息
 */
export interface MarketSchedulerInfo {
  /** 代理池是否运行 */
  running: boolean;
  /** 是否启用自动启动 */
  auto_start_enabled: boolean;
  /** 盘前启动分钟数 */
  pre_market_minutes: number;
  /** 盘后停止分钟数 */
  post_market_minutes: number;
  /** 交易总结 */
  trading_summary: TradingDayInfo;
  /** 当前是否应该启动 */
  should_start: boolean;
  /** 当前是否应该停止 */
  should_stop: boolean;
  /** 交易日类型 */
  trading_day_type: string;
  /** 交易时段类型 */
  session_type: string;
  /** 状态描述 */
  status_description: string;
  /** 交易时间 */
  trading_hours: TradingHours;
}

/**
 * 增强调度器状态响应
 */
export interface EnhancedSchedulerStatus {
  /** 调度器是否运行 */
  scheduler_running: boolean;
  /** 是否启用增强功能 */
  enhanced_features: boolean;
  /** 各市场调度信息 */
  markets: Record<MarketCode, MarketSchedulerInfo>;
}

/**
 * 增强强制操作响应
 */
export interface EnhancedForceOperationResponse {
  /** 操作状态 */
  status: ForceOperationStatus;
  /** 操作结果描述 */
  message: string;
  /** 交易信息 */
  trading_info?: TradingDayInfo;
}

/**
 * MACL交易日类型响应
 */
export interface MaclDayTypeResponse {
  /** 市场代码 */
  market: string;
  /** 查询日期 */
  date: string;
  /** 交易日类型 */
  day_type: TradingDayType;
  /** 交易时段类型 */
  session_type: TradingSessionType;
  /** 是否交易日 */
  is_trading_day: boolean;
  /** 交易时间 */
  trading_hours: TradingHours;
  /** 数据来源 */
  data_source: DataSource;
}

/**
 * 交易模式总结响应
 */
export interface TradingModesSummary {
  /** 查询日期 */
  date: string;
  /** 各市场信息 */
  markets: Record<MarketCode, TradingDayInfo | { error: string; market: string; date: string }>;
}

/**
 * 批量操作响应
 */
export interface BatchOperationResponse {
  /** 各市场操作结果 */
  results: Record<MarketCode, {
    status: string;
    message: string;
  }>;
}

/**
 * 配置响应
 */
export interface ConfigResponse {
  /** 市场代码 */
  market: string;
  /** 运行模式 */
  mode: string;
  /** 配置信息 */
  config: ProxyPoolConfig;
}

/**
 * 配置更新响应
 */
export interface ConfigUpdateResponse extends ConfigResponse {
  /** 操作状态 */
  status: 'success';
  /** 操作消息 */
  message: string;
}

/**
 * 错误响应
 */
export interface ErrorResponse {
  /** 错误详情描述 */
  detail: string;
  /** HTTP状态码 */
  status_code: number;
  /** 错误发生时间 */
  timestamp: string;
  /** 请求ID (可选) */
  request_id?: string;
  /** 内部错误码 (可选) */
  error_code?: string;
}

// ============================================================================
// API客户端接口
// ============================================================================

/**
 * 代理池API客户端接口
 */
export interface ProxyPoolApiClient {
  // 标准代理池接口
  getStatus(market: MarketCode, mode?: OperationMode): Promise<ProxyPoolStatusResponse>;
  startService(market: MarketCode, mode?: OperationMode): Promise<ServiceOperationResponse>;
  stopService(market: MarketCode, mode?: OperationMode): Promise<ServiceStopResponse>;

  // RPC接口
  getProxy(market: MarketCode, proxyType?: ProxyType, mode?: OperationMode): Promise<GetProxyResponse>;
  reportFailure(proxyAddr: string, market: MarketCode, mode?: OperationMode): Promise<ReportFailureResponse>;
  getServiceStatus(market: MarketCode, mode?: OperationMode): Promise<RpcStatusResponse>;
  ping(market: MarketCode, mode?: OperationMode): Promise<RpcStatusResponse>;

  // 增强交易日类型接口
  getTradingDayInfo(market: MarketCode, date?: string): Promise<TradingDayInfo>;
  getMarketRealtimeStatus(market: MarketCode): Promise<MarketRealtimeStatus>;
  getEnhancedSchedulerStatus(): Promise<EnhancedSchedulerStatus>;
  forceStartMarket(market: MarketCode): Promise<EnhancedForceOperationResponse>;
  forceStopMarket(market: MarketCode): Promise<EnhancedForceOperationResponse>;

  // MACL接口
  getMaclDayType(market: MarketCode, date?: string): Promise<MaclDayTypeResponse>;
  getTradingModesSummary(date?: string): Promise<TradingModesSummary>;

  // 批量操作
  batchStart(markets: MarketCode[], mode?: OperationMode): Promise<BatchOperationResponse>;
  batchStop(markets: MarketCode[], mode?: OperationMode): Promise<BatchOperationResponse>;

  // 配置管理
  getConfig(market: MarketCode, mode?: OperationMode): Promise<ConfigResponse>;
  updateConfig(market: MarketCode, updates: ConfigUpdateRequest, mode?: OperationMode): Promise<ConfigUpdateResponse>;
}

// ============================================================================
// 实用工具类型
// ============================================================================

/**
 * API响应包装器
 */
export type ApiResponse<T> = {
  success: true;
  data: T;
} | {
  success: false;
  error: ErrorResponse;
};

/**
 * 市场状态枚举
 */
export const MarketStatus = {
  TRADING: 'trading',
  CLOSED: 'closed',
  PRE_MARKET: 'pre_market',
  POST_MARKET: 'post_market',
  LUNCH_BREAK: 'lunch_break',
  HOLIDAY: 'holiday',
  WEEKEND: 'weekend'
} as const;

export type MarketStatusType = typeof MarketStatus[keyof typeof MarketStatus];

/**
 * 交易日类型描述映射
 */
export const TradingDayTypeDescriptions: Record<TradingDayType, string> = {
  NORMAL: '正常交易日',
  HALF_DAY: '半日交易',
  HOLIDAY: '假期',
  WEEKEND: '周末'
};

/**
 * 交易时段类型描述映射
 */
export const TradingSessionTypeDescriptions: Record<TradingSessionType, string> = {
  full_day: '全日交易',
  morning_only: '仅上午交易',
  afternoon_only: '仅下午交易'
};

/**
 * 市场代码映射
 */
export const MarketCodeMapping: Record<MarketCode, MarketCodeUpper> = {
  cn: 'CN',
  hk: 'HK',
  us: 'US'
};

/**
 * 市场名称映射
 */
export const MarketNames: Record<MarketCodeUpper, string> = {
  CN: '中国A股',
  HK: '香港股市',
  US: '美国股市'
};

// ============================================================================
// 导出所有类型
// ============================================================================

export default {
  // 类型导出
  MarketStatus,
  TradingDayTypeDescriptions,
  TradingSessionTypeDescriptions,
  MarketCodeMapping,
  MarketNames,
};

/**
 * 使用示例：
 *
 * ```typescript
 * import { ProxyPoolApiClient, TradingDayInfo, MarketCode } from './proxy-pool-api-types';
 *
 * // 创建API客户端
 * const apiClient: ProxyPoolApiClient = new ProxyPoolApiClientImpl('http://192.168.8.168:8001/api/v1');
 *
 * // 获取交易日信息
 * const tradingInfo: TradingDayInfo = await apiClient.getTradingDayInfo('cn');
 *
 * // 检查是否为半日交易
 * if (tradingInfo.day_type === 'HALF_DAY') {
 *   console.log(`${tradingInfo.market} 今日为半日交易，时段：${tradingInfo.session_type}`);
 * }
 *
 * // 获取代理IP
 * const proxyResponse = await apiClient.getProxy('cn', 'short');
 * if (proxyResponse.proxy) {
 *   console.log(`获取到代理: ${proxyResponse.proxy}`);
 * }
 * ```
 */