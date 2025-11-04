import type { Tab } from "@/types";

export * from "./factors";
export * from "./mockData";
export * from "./subFactors";

// Tab configurations
export const HOME_SORT_TABS: Tab[] = [
  { id: "recent", label: "최근 본 주식" },
  { id: "asc", label: "상승률순" },
  { id: "desc", label: "하락률순" },
];

export const HOME_PERIOD_TABS: Tab[] = [
  { id: "1d", label: "1일" },
  { id: "1w", label: "1주일" },
  { id: "1m", label: "1개월" },
  { id: "3m", label: "3개월" },
  { id: "6m", label: "6개월" },
  { id: "1y", label: "1년" },
];

export const SCRIPT_EDITOR_TABS: Tab[] = [
  { id: "buy", label: "매수 조건" },
  { id: "sell", label: "매도 조건" },
  { id: "target", label: "매매 대상 설정" },
];

/** 백테스트 결과 탭 구성을 위한 상수 */
export const BACKTEST_RESULT_TABS: Tab[] = [
  { id: "stocks", label: "매매 종목 정보" },
  { id: "yield", label: "수익률" },
  { id: "settings", label: "설정 조건" },
];

// Form default values
export const DEFAULT_INVESTMENT_AMOUNT = 5000;
export const DEFAULT_DATE = "251231";
export const DEFAULT_COMMISSION_RATE = 0.1;
export const DEFAULT_POSITION_SIZE = 10;
export const DEFAULT_MAX_POSITIONS = 10;
export const DEFAULT_PROFIT_TARGET = 10;
export const DEFAULT_STOP_LOSS = 10;

// Initial condition states
export const INITIAL_BUY_CONDITIONS = [
  { id: "A", expression: "조건식이 표시됩니다." },
  { id: "B", expression: "조건식이 표시됩니다." },
];
