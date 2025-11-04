import { create } from "zustand";
import type { BacktestRunRequest } from "@/types/api";

/**
 * 백테스트 설정 전역 상태 관리 스토어
 * BacktestRunRequest 타입과 완벽하게 일치하는 형식으로 모든 설정값을 저장합니다.
 */
interface BacktestConfigStore extends BacktestRunRequest {
  // 설정값 업데이트 함수들
  setUserId: (userId: string) => void;
  setStrategyName: (name: string) => void;
  setIsDayOrMonth: (value: string) => void;
  setStartDate: (date: string) => void;
  setEndDate: (date: string) => void;
  setInitialInvestment: (amount: number) => void;
  setCommissionRate: (rate: number) => void;

  // 매수 조건 업데이트
  setBuyConditions: (conditions: BacktestRunRequest["buy_conditions"]) => void;
  setBuyLogic: (logic: string) => void;
  setPriorityFactor: (factor: string) => void;
  setPriorityOrder: (order: string) => void;
  setPerStockRatio: (ratio: number) => void;
  setMaxHoldings: (max: number) => void;
  setMaxBuyValue: (value: number | null) => void;
  setMaxDailyStock: (max: number | null) => void;
  setBuyCostBasis: (basis: string) => void;

  // 매도 조건 업데이트
  setTargetAndLoss: (value: BacktestRunRequest["target_and_loss"]) => void;
  setHoldDays: (value: BacktestRunRequest["hold_days"]) => void;
  setSellConditions: (value: BacktestRunRequest["sell_conditions"]) => void;
  setTargetStocks: (stocks: string[]) => void;

  // 모든 설정 초기화
  reset: () => void;

  // BacktestRunRequest 형식으로 데이터 반환
  getBacktestRequest: () => BacktestRunRequest;
}

/**
 * 기본 설정값
 */
const defaultConfig: BacktestRunRequest = {
  user_id: "default_user", // 실제로는 로그인한 사용자 ID를 사용
  strategy_name: "새 전략", // 기본 전략 이름
  is_day_or_month: "daily", // 기본값: 일봉
  start_date: "20190101", // 기본 시작일
  end_date: "20241231", // 기본 종료일
  initial_investment: 10000, // 기본 투자 금액 (만원)
  commission_rate: 0.3, // 기본 수수료율 (%)

  // 매수 조건 기본값
  buy_conditions: [],
  buy_logic: "", // 논리 조건식 (예: "A and B")
  priority_factor: "", // 우선순위 팩터 (예: "{PBR}")
  priority_order: "desc", // 우선순위 방향
  per_stock_ratio: 10, // 종목당 매수 비중 (%)
  max_holdings: 10, // 최대 보유 종목 수
  max_buy_value: null, // 종목당 최대 매수 금액 (null이면 제한 없음)
  max_daily_stock: null, // 일일 최대 매수 종목 수 (null이면 제한 없음)
  buy_cost_basis: "{전일 종가} 0", // 매수 가격 기준

  // 매도 조건 기본값 (모두 null로 시작)
  target_and_loss: null,
  hold_days: null,
  sell_conditions: null,
  target_stocks: [], // 매매 대상 종목 (빈 배열이면 전체)
};

/**
 * 백테스트 설정 스토어
 *
 * 사용 예시:
 * ```tsx
 * const { setStartDate, setEndDate, getBacktestRequest } = useBacktestConfigStore();
 * setStartDate("20200101");
 * const request = getBacktestRequest(); // BacktestRunRequest 형식으로 반환
 * ```
 */
export const useBacktestConfigStore = create<BacktestConfigStore>((set, get) => ({
  // 초기값 설정
  ...defaultConfig,

  // 기본 설정 업데이트 함수들
  setUserId: (userId) => set({ user_id: userId }),
  setStrategyName: (name) => set({ strategy_name: name }),
  setIsDayOrMonth: (value) => set({ is_day_or_month: value }),
  setStartDate: (date) => set({ start_date: date }),
  setEndDate: (date) => set({ end_date: date }),
  setInitialInvestment: (amount) => set({ initial_investment: amount }),
  setCommissionRate: (rate) => set({ commission_rate: rate }),

  // 매수 조건 업데이트 함수들
  setBuyConditions: (conditions) => set({ buy_conditions: conditions }),
  setBuyLogic: (logic) => set({ buy_logic: logic }),
  setPriorityFactor: (factor) => set({ priority_factor: factor }),
  setPriorityOrder: (order) => set({ priority_order: order }),
  setPerStockRatio: (ratio) => set({ per_stock_ratio: ratio }),
  setMaxHoldings: (max) => set({ max_holdings: max }),
  setMaxBuyValue: (value) => set({ max_buy_value: value }),
  setMaxDailyStock: (max) => set({ max_daily_stock: max }),
  setBuyCostBasis: (basis) => set({ buy_cost_basis: basis }),

  // 매도 조건 업데이트 함수들
  setTargetAndLoss: (value) => set({ target_and_loss: value }),
  setHoldDays: (value) => set({ hold_days: value }),
  setSellConditions: (value) => set({ sell_conditions: value }),
  setTargetStocks: (stocks) => set({ target_stocks: stocks }),

  // 초기화 함수
  reset: () => set(defaultConfig),

  // BacktestRunRequest 형식으로 데이터 반환
  getBacktestRequest: () => {
    const state = get();
    return {
      user_id: state.user_id,
      strategy_name: state.strategy_name,
      is_day_or_month: state.is_day_or_month,
      start_date: state.start_date,
      end_date: state.end_date,
      initial_investment: state.initial_investment,
      commission_rate: state.commission_rate,
      buy_conditions: state.buy_conditions,
      buy_logic: state.buy_logic,
      priority_factor: state.priority_factor,
      priority_order: state.priority_order,
      per_stock_ratio: state.per_stock_ratio,
      max_holdings: state.max_holdings,
      max_buy_value: state.max_buy_value,
      max_daily_stock: state.max_daily_stock,
      buy_cost_basis: state.buy_cost_basis,
      target_and_loss: state.target_and_loss,
      hold_days: state.hold_days,
      sell_conditions: state.sell_conditions,
      target_stocks: state.target_stocks,
    };
  },
}));
