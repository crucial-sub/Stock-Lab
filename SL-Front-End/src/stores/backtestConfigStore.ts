import { getCurrentDate, getOneYearAgo } from "@/lib/date-utils";
import type { BacktestRunRequest } from "@/types/api";
import { create } from "zustand";

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
  setSlippage: (slippage: number) => void;

  // 매수 조건 업데이트
  setBuyConditions: (conditions: BacktestRunRequest["buy_conditions"]) => void;
  setBuyLogic: (logic: string) => void;
  setPriorityFactor: (factor: string) => void;
  setPriorityOrder: (order: string) => void;
  setPerStockRatio: (ratio: number) => void;
  setMaxHoldings: (max: number) => void;
  setMaxBuyValue: (value: number | null) => void;
  setMaxDailyStock: (max: number | null) => void;
  setBuyPriceBasis: (basis: string) => void;
  setBuyPriceOffset: (offset: number) => void;

  // 매도 조건 업데이트
  setTargetAndLoss: (value: BacktestRunRequest["target_and_loss"]) => void;
  setHoldDays: (value: BacktestRunRequest["hold_days"]) => void;
  setConditionSell: (value: BacktestRunRequest["condition_sell"]) => void;

  // 매매 대상 업데이트
  setTradeTargets: (value: BacktestRunRequest["trade_targets"]) => void;

  // 모든 설정 초기화
  reset: () => void;

  // BacktestRunRequest 형식으로 데이터 반환
  getBacktestRequest: () => BacktestRunRequest;
}

/**
 * 기본 설정값
 * - 날짜는 동적으로 계산 (현재 날짜, 1년 전)
 * - 토글 기본값: 목표가/손절가 on, 나머지 off
 */
const defaultConfig: BacktestRunRequest = {
  user_id: "default_user", // 실제로는 로그인한 사용자 ID를 사용
  strategy_name: "새 전략", // 기본 전략 이름
  is_day_or_month: "daily", // "일봉"
  start_date: getOneYearAgo(), // 1년 전 날짜 (YYYYMMDD)
  end_date: getCurrentDate(), // 현재 날짜 (YYYYMMDD)
  initial_investment: 5000, // 5000만원
  commission_rate: 0.1, // 0.1%
  slippage: 0.0, // 0.0% (슬리피지)

  // 매수 조건 기본값
  buy_conditions: [],
  buy_logic: "", // 논리 조건식 (예: "A and B")
  priority_factor: "", // 우선순위 팩터 (예: "{PBR}")
  priority_order: "desc", // 내림차순
  per_stock_ratio: 10, // 10%
  max_holdings: 10, // 10종목
  max_buy_value: null, // null (토글 off)
  max_daily_stock: null, // null (토글 off)
  buy_price_basis: "전일 종가", // 매수 가격 기준
  buy_price_offset: 0, // 기준가 대비 증감값(%)

  // 매도 조건 기본값
  target_and_loss: {
    target_gain: 10, // 목표가 10%
    stop_loss: 10, // 손절가 10%
  },
  hold_days: null, // 토글 off
  condition_sell: null, // 토글 off
  trade_targets: {
    use_all_stocks: true,
    selected_universes: [],
    selected_themes: [],
    selected_stocks: [],
  },
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
  setSlippage: (slippage) => set({ slippage: slippage }),

  // 매수 조건 업데이트 함수들
  setBuyConditions: (conditions) => set({ buy_conditions: conditions }),
  setBuyLogic: (logic) => set({ buy_logic: logic }),
  setPriorityFactor: (factor) => set({ priority_factor: factor }),
  setPriorityOrder: (order) => set({ priority_order: order }),
  setPerStockRatio: (ratio) => set({ per_stock_ratio: ratio }),
  setMaxHoldings: (max) => set({ max_holdings: max }),
  setMaxBuyValue: (value) => set({ max_buy_value: value }),
  setMaxDailyStock: (max) => set({ max_daily_stock: max }),
  setBuyPriceBasis: (basis) => set({ buy_price_basis: basis }),
  setBuyPriceOffset: (offset) => set({ buy_price_offset: offset }),

  // 매도 조건 업데이트 함수들
  setTargetAndLoss: (value) => set({ target_and_loss: value }),
  setHoldDays: (value) => set({ hold_days: value }),
  setConditionSell: (value) => set({ condition_sell: value }),

  // 매매 대상 업데이트 함수
  setTradeTargets: (value) => set({ trade_targets: value }),

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
      slippage: state.slippage,
      buy_conditions: state.buy_conditions,
      buy_logic: state.buy_logic,
      priority_factor: state.priority_factor,
      priority_order: state.priority_order,
      per_stock_ratio: state.per_stock_ratio,
      max_holdings: state.max_holdings,
      max_buy_value: state.max_buy_value,
      max_daily_stock: state.max_daily_stock,
      buy_price_basis: state.buy_price_basis,
      buy_price_offset: state.buy_price_offset,
      target_and_loss: state.target_and_loss,
      hold_days: state.hold_days,
      condition_sell: state.condition_sell,
      trade_targets: state.trade_targets,
    };
  },
}));
