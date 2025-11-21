import { axiosInstance } from "../axios";

// Request Types
export interface AutoTradingActivateRequest {
  session_id: string;
  initial_capital?: number;
  allocated_capital: number;
}

export interface AutoTradingDeactivateRequest {
  sell_all_positions: boolean;
}

// Response Types
export interface AutoTradingActivateResponse {
  message: string;
  strategy_id: string;
  is_active: boolean;
  activated_at: string;
}

export interface AutoTradingDeactivateResponse {
  message: string;
  strategy_id: string;
  is_active: boolean;
  deactivated_at: string;
  positions_sold: number;
}

export interface LivePositionResponse {
  position_id: string;
  stock_code: string;
  stock_name?: string;
  quantity: number;
  avg_buy_price: number;
  current_price?: number;
  buy_date: string;
  hold_days: number;
  unrealized_profit?: number;
  unrealized_profit_pct?: number;
  selection_reason?: string;
}

export interface LiveTradeResponse {
  trade_id: string;
  trade_date: string;
  trade_time?: string;
  trade_type: string;
  stock_code: string;
  stock_name?: string;
  quantity: number;
  price: number;
  amount: number;
  commission: number;
  tax: number;
  profit?: number;
  profit_rate?: number;
  hold_days?: number;
  selection_reason?: string;
  order_status: string;
}

export interface LiveDailyPerformanceResponse {
  performance_id: string;
  date: string;
  cash_balance: number;
  stock_value: number;
  total_value: number;
  daily_return?: number;
  cumulative_return?: number;
  buy_count: number;
  sell_count: number;
  trade_count: number;
  position_count: number;
}

export interface AutoTradingStrategyResponse {
  strategy_id: string;
  user_id: string;
  simulation_session_id: string;
  is_active: boolean;
  initial_capital: number;
  current_capital: number;
  cash_balance: number;
  per_stock_ratio: number;
  max_positions: number;
  rebalance_frequency: string;
  created_at: string;
  activated_at?: string;
  deactivated_at?: string;
  last_executed_at?: string;
}

export interface AutoTradingStatusResponse {
  strategy: AutoTradingStrategyResponse;
  positions: LivePositionResponse[];
  today_trades: LiveTradeResponse[];
  latest_performance?: LiveDailyPerformanceResponse;
  total_positions: number;
  total_trades: number;
}

export interface AutoTradingExecuteResponse {
  message: string;
  selected_count: number;
  bought_count: number;
  stocks: Array<{
    stock_code: string;
    company_name: string;
    current_price: number;
    market_cap: number;
    per?: number;
    pbr?: number;
  }>;
}

export interface TradeSignalItem {
  stock_code: string;
  stock_name?: string;
  quantity?: number;
  target_weight?: number;
  current_price?: number;
  per?: number;
  pbr?: number;
  metadata?: Record<string, unknown>;
}

export interface RebalancePreviewResponse {
  generated_at: string;
  candidates: TradeSignalItem[];
  note?: string;
}

export interface AutoTradingLog {
  log_id: string;
  event_type: string;
  event_level: string;
  message?: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export interface AutoTradingLogListResponse {
  logs: AutoTradingLog[];
}

export interface AutoTradingRiskAlert {
  type: string;
  severity: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface AutoTradingPositionRisk {
  stock_code: string;
  stock_name?: string;
  quantity: number;
  market_value: number;
  avg_buy_price: number;
  current_price: number;
  unrealized_profit: number;
  unrealized_profit_pct: number;
  hold_days: number;
}

export interface AutoTradingRiskSnapshotResponse {
  as_of: string;
  cash_balance: number;
  invested_value: number;
  total_value: number;
  exposure_ratio: number;
  alerts: AutoTradingRiskAlert[];
  positions: AutoTradingPositionRisk[];
}

export interface ExecutionReportRow {
  date: string;
  live_total_value?: number;
  live_daily_return?: number;
  backtest_total_value?: number;
  backtest_daily_return?: number;
  tracking_error?: number;
}

export interface ExecutionReportSummary {
  days: number;
  average_tracking_error?: number;
  cumulative_live_return?: number;
  cumulative_backtest_return?: number;
  realized_vs_expected?: number;
}

export interface AutoTradingExecutionReportResponse {
  strategy_id: string;
  session_id?: string;
  generated_at: string;
  rows: ExecutionReportRow[];
  summary: ExecutionReportSummary;
}

export const autoTradingApi = {
  /**
   * 자동매매 활성화
   */
  activateAutoTrading: async (
    request: AutoTradingActivateRequest,
  ): Promise<AutoTradingActivateResponse> => {
    const response = await axiosInstance.post<AutoTradingActivateResponse>(
      "/auto-trading/activate",
      request,
    );
    return response.data;
  },

  /**
   * 자동매매 비활성화
   */
  deactivateAutoTrading: async (
    strategyId: string,
    request: AutoTradingDeactivateRequest,
  ): Promise<AutoTradingDeactivateResponse> => {
    const response = await axiosInstance.post<AutoTradingDeactivateResponse>(
      `/auto-trading/strategies/${strategyId}/deactivate`,
      request,
    );
    return response.data;
  },

  /**
   * 자동매매 전략 상태 조회
   */
  getAutoTradingStatus: async (
    strategyId: string,
  ): Promise<AutoTradingStatusResponse> => {
    const response = await axiosInstance.get<AutoTradingStatusResponse>(
      `/auto-trading/strategies/${strategyId}/status`,
    );
    return response.data;
  },

  /**
   * 내 자동매매 전략 목록 조회
   */
  getMyAutoTradingStrategies: async (): Promise<
    AutoTradingStrategyResponse[]
  > => {
    const response = await axiosInstance.get<AutoTradingStrategyResponse[]>(
      "/auto-trading/my-strategies",
    );
    return response.data;
  },

  /**
   * 내 자동매매 전략 목록 조회 (서버 사이드)
   */
  getMyAutoTradingStrategiesServer: async (
    token: string,
  ): Promise<AutoTradingStrategyResponse[]> => {
    const axios = (await import("axios")).default;
    // Docker 환경에서는 컨테이너 이름 사용
    const baseURL = process.env.API_BASE_URL?.replace('/api/v1', '') || "http://backend:8000";
    const response = await axios.get<AutoTradingStrategyResponse[]>(
      `${baseURL}/api/v1/auto-trading/my-strategies`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return response.data;
  },

  /**
   * 자동매매 수동 실행 (테스트용)
   */
  executeAutoTrading: async (
    strategyId: string,
  ): Promise<AutoTradingExecuteResponse> => {
    const response = await axiosInstance.post<AutoTradingExecuteResponse>(
      `/auto-trading/strategies/${strategyId}/execute`,
    );
    return response.data;
  },

  /**
   * 리밸런싱 프리뷰 조회
   */
  getRebalancePreview: async (
    strategyId: string,
  ): Promise<RebalancePreviewResponse> => {
    const response =
      await axiosInstance.get<RebalancePreviewResponse>(
        `/auto-trading/strategies/${strategyId}/rebalance-preview`,
      );
    return response.data;
  },

  /**
   * 전략 이벤트 로그 조회
   */
  getStrategyLogs: async (
    strategyId: string,
    params?: { event_type?: string; limit?: number },
  ): Promise<AutoTradingLogListResponse> => {
    const response = await axiosInstance.get<AutoTradingLogListResponse>(
      `/auto-trading/strategies/${strategyId}/logs`,
      { params },
    );
    return response.data;
  },

  /**
   * 위험 스냅샷 조회
   */
  getRiskSnapshot: async (
    strategyId: string,
  ): Promise<AutoTradingRiskSnapshotResponse> => {
    const response =
      await axiosInstance.get<AutoTradingRiskSnapshotResponse>(
        `/auto-trading/strategies/${strategyId}/risk`,
      );
    return response.data;
  },

  /**
   * 실거래 리포트 조회
   */
  getExecutionReport: async (
    strategyId: string,
    days = 30,
  ): Promise<AutoTradingExecutionReportResponse> => {
    const response =
      await axiosInstance.get<AutoTradingExecutionReportResponse>(
        `/auto-trading/strategies/${strategyId}/execution-report`,
        { params: { days } },
      );
    return response.data;
  },

  /**
   * 포트폴리오 대시보드 조회
   */
  getPortfolioDashboard: async (): Promise<{
    total_assets: number;
    total_return: number;
    total_profit: number;
    active_strategy_count: number;
    total_positions: number;
    total_trades_today: number;
  }> => {
    const response = await axiosInstance.get(`/auto-trading/dashboard`);
    return response.data;
  },

  /**
   * 포트폴리오 대시보드 조회 (서버 사이드)
   */
  getPortfolioDashboardServer: async (token: string): Promise<{
    total_assets: number;
    total_return: number;
    total_profit: number;
    active_strategy_count: number;
    total_positions: number;
    total_trades_today: number;
  }> => {
    const axios = (await import("axios")).default;
    const baseURL = process.env.API_BASE_URL?.replace('/api/v1', '') || "http://backend:8000";
    const response = await axios.get(
      `${baseURL}/api/v1/auto-trading/dashboard`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return response.data;
  },
};
