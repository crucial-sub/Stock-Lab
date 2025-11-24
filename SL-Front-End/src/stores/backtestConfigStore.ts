import { create } from "zustand";
import type { BacktestRunRequest } from "@/types/api";

// ========================================
// UI 전용 조건 타입 정의
// ========================================
interface BuyConditionUI {
  id: string;
  factorName: string | null;
  subFactorName: string | null;
  operator: string;
  value: string;
  argument?: string;
}

interface SellConditionUI {
  id: string;
  factorName: string | null;
  subFactorName: string | null;
  operator: string;
  value: string;
  argument?: string;
}

/**
 * 백테스트 설정 전역 상태 관리 스토어
 * BacktestRunRequest 타입과 완벽하게 일치하는 형식으로 모든 설정값을 저장합니다.
 */
interface BacktestConfigStore extends BacktestRunRequest {
  // UI 전용 상태
  buyConditionsUI: BuyConditionUI[];
  sellConditionsUI: SellConditionUI[];

  // Buy 조건 관리 함수
  addBuyConditionUI: () => void;
  addBuyConditionUIWithData: (data: Partial<BuyConditionUI>) => void;
  updateBuyConditionUI: (id: string, updates: Partial<BuyConditionUI>) => void;
  removeBuyConditionUI: (id: string) => void;
  setBuyConditionsUI: (conditions: BuyConditionUI[]) => void;

  // Sell 조건 관리 함수
  addSellConditionUI: () => void;
  addSellConditionUIWithData: (data: Partial<SellConditionUI>) => void;
  updateSellConditionUI: (
    id: string,
    updates: Partial<SellConditionUI>,
  ) => void;
  removeSellConditionUI: (id: string) => void;
  setSellConditionsUI: (conditions: SellConditionUI[]) => void;

  // API 변환 함수
  syncUIToAPI: () => void;
  // 설정값 업데이트 함수들
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
  setTradeTargets: (
    value:
      | BacktestRunRequest["trade_targets"]
      | ((prev: BacktestRunRequest["trade_targets"]) => BacktestRunRequest["trade_targets"])
  ) => void;

  // 모든 설정 초기화
  reset: () => void;

  // BacktestRunRequest 형식으로 데이터 반환
  getBacktestRequest: () => BacktestRunRequest;
}

/**
 * 기본 설정값
 * - 날짜는 고정된 초기값 사용 (하이드레이션 이슈 방지)
 * - 실제 날짜는 클라이언트 사이드에서 설정
 * - 토글 기본값: 목표가/손절가 on, 나머지 off
 */
const defaultConfig: BacktestRunRequest = {
  strategy_name: "새 전략", // 기본 전략 이름
  is_day_or_month: "daily", // "일봉"
  start_date: "", // 초기값 공백 (클라이언트에서 설정)
  end_date: "", // 초기값 공백 (클라이언트에서 설정)
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
export const useBacktestConfigStore = create<BacktestConfigStore>(
  (set, get) => ({
    // 초기값 설정
    ...defaultConfig,

    // UI 전용 초기 상태
    buyConditionsUI: [],
    sellConditionsUI: [],

    // ========================================
    // Buy 조건 관리 함수
    // ========================================
    addBuyConditionUI: () =>
      set((state) => {
        const newId = String.fromCharCode(65 + state.buyConditionsUI.length); // 65 = 'A'
        return {
          buyConditionsUI: [
            ...state.buyConditionsUI,
            {
              id: newId,
              factorName: null,
              subFactorName: null,
              operator: ">",
              value: "",
            },
          ],
        };
      }),

    addBuyConditionUIWithData: (data) =>
      set((state) => {
        const newId = String.fromCharCode(65 + state.buyConditionsUI.length);
        return {
          buyConditionsUI: [
            ...state.buyConditionsUI,
            {
              id: newId,
              factorName: null,
              subFactorName: null,
              operator: ">",
              value: "",
              ...data,
            },
          ],
        };
      }),

    updateBuyConditionUI: (id, updates) =>
      set((state) => ({
        buyConditionsUI: state.buyConditionsUI.map((c) =>
          c.id === id ? { ...c, ...updates } : c,
        ),
      })),

    removeBuyConditionUI: (id) =>
      set((state) => ({
        buyConditionsUI: state.buyConditionsUI.filter((c) => c.id !== id),
      })),

    setBuyConditionsUI: (conditions) =>
      set(() => ({
        buyConditionsUI: conditions,
      })),

    // ========================================
    // Sell 조건 관리 함수
    // ========================================
    addSellConditionUI: () =>
      set((state) => {
        const newId = String.fromCharCode(65 + state.sellConditionsUI.length); // 65 = 'A'
        return {
          sellConditionsUI: [
            ...state.sellConditionsUI,
            {
              id: newId,
              factorName: null,
              subFactorName: null,
              operator: ">",
              value: "",
            },
          ],
        };
      }),

    addSellConditionUIWithData: (data) =>
      set((state) => {
        const newId = String.fromCharCode(65 + state.sellConditionsUI.length);
        return {
          sellConditionsUI: [
            ...state.sellConditionsUI,
            {
              id: newId,
              factorName: null,
              subFactorName: null,
              operator: ">",
              value: "",
              ...data,
            },
          ],
        };
      }),

    updateSellConditionUI: (id, updates) =>
      set((state) => ({
        sellConditionsUI: state.sellConditionsUI.map((c) =>
          c.id === id ? { ...c, ...updates } : c,
        ),
      })),

    removeSellConditionUI: (id) =>
      set((state) => ({
        sellConditionsUI: state.sellConditionsUI.filter((c) => c.id !== id),
      })),

    setSellConditionsUI: (conditions) =>
      set(() => ({
        sellConditionsUI: conditions,
      })),

    // ========================================
    // UI → API 변환 및 동기화
    // ========================================
    syncUIToAPI: () => {
      const { buyConditionsUI, sellConditionsUI } = get();

      // Buy 조건 변환
      const buyConditions = buyConditionsUI
        .filter((c) => c.factorName !== null)
        .map((c) => {
          let expLeftSide = "";
          if (c.subFactorName) {
            expLeftSide = c.argument
              ? `${c.subFactorName}({${c.factorName}},{${c.argument}})`
              : `${c.subFactorName}({${c.factorName}})`;
          } else {
            expLeftSide = `{${c.factorName}}`;
          }

          return {
            name: c.id,
            exp_left_side: expLeftSide,
            inequality: c.operator,
            exp_right_side: Number(c.value) || 0, // API 명세 확정 후 수정 예정
          };
        });

      // Sell 조건 변환
      const sellConditions = sellConditionsUI
        .filter((c) => c.factorName !== null)
        .map((c) => {
          let expLeftSide = "";
          if (c.subFactorName) {
            expLeftSide = c.argument
              ? `${c.subFactorName}({${c.factorName}},{${c.argument}})`
              : `${c.subFactorName}({${c.factorName}})`;
          } else {
            expLeftSide = `{${c.factorName}}`;
          }

          return {
            name: c.id,
            exp_left_side: expLeftSide,
            inequality: c.operator,
            exp_right_side: Number(c.value) || 0, // API 명세 확정 후 수정 예정
          };
        });

      // API 상태 업데이트
      set({ buy_conditions: buyConditions });

      // Sell 조건도 condition_sell에 반영
      const currentConditionSell = get().condition_sell;
      if (currentConditionSell !== null) {
        set({
          condition_sell: {
            ...currentConditionSell,
            sell_conditions: sellConditions,
          },
        });
      }
    },

    // 기본 설정 업데이트 함수들
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
    setTradeTargets: (value) =>
      set((state) => ({
        trade_targets: typeof value === "function" ? value(state.trade_targets) : value,
      })),

    // 초기화 함수
    reset: () => {
      // 현재 날짜 계산 (클라이언트 사이드에서만 유효)
      const today = new Date();
      const oneYearAgo = new Date(today);
      oneYearAgo.setFullYear(today.getFullYear() - 1);

      const formatDate = (date: Date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}${month}${day}`;
      };

      set({
        ...defaultConfig,
        start_date: formatDate(oneYearAgo),
        end_date: formatDate(today),
        buyConditionsUI: [],
        sellConditionsUI: [],
      });
    },

    // BacktestRunRequest 형식으로 데이터 반환
    getBacktestRequest: () => {
      // UI → API 동기화
      get().syncUIToAPI();

      const state = get();
      return {
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
  }),
);
