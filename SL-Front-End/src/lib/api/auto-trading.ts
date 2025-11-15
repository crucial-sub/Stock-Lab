import { axiosInstance } from "../axios";

// Request Types
export interface AutoTradingActivateRequest {
  session_id: string;
  initial_capital?: number;
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

export const autoTradingApi = {
  /**
   * 자동매매 활성화
   */
  activateAutoTrading: async (
    request: AutoTradingActivateRequest
  ): Promise<AutoTradingActivateResponse> => {
    const response = await axiosInstance.post<AutoTradingActivateResponse>(
      "/auto-trading/activate",
      request
    );
    return response.data;
  },

  /**
   * 자동매매 비활성화
   */
  deactivateAutoTrading: async (
    strategyId: string,
    request: AutoTradingDeactivateRequest
  ): Promise<AutoTradingDeactivateResponse> => {
    const response = await axiosInstance.post<AutoTradingDeactivateResponse>(
      `/auto-trading/strategies/${strategyId}/deactivate`,
      request
    );
    return response.data;
  },

  /**
   * 자동매매 전략 상태 조회
   */
  getAutoTradingStatus: async (
    strategyId: string
  ): Promise<AutoTradingStatusResponse> => {
    const response = await axiosInstance.get<AutoTradingStatusResponse>(
      `/auto-trading/strategies/${strategyId}/status`
    );
    return response.data;
  },

  /**
   * 내 자동매매 전략 목록 조회
   */
  getMyAutoTradingStrategies: async (): Promise<AutoTradingStrategyResponse[]> => {
    const response = await axiosInstance.get<AutoTradingStrategyResponse[]>(
      "/auto-trading/my-strategies"
    );
    return response.data;
  },

  /**
   * 자동매매 수동 실행 (테스트용)
   */
  executeAutoTrading: async (
    strategyId: string
  ): Promise<AutoTradingExecuteResponse> => {
    const response = await axiosInstance.post<AutoTradingExecuteResponse>(
      `/auto-trading/strategies/${strategyId}/execute`
    );
    return response.data;
  },
};
