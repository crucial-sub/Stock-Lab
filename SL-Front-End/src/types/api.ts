/**
 * API 응답 및 요청 타입 정의
 */

/** 팩터 타입 */
export interface Factor {
  id: string;
  name: string;
  category: string;
  description?: string;
}

/** 함수 타입 */
export interface SubFactor {
  id: string;
  name: string;
  description?: string;
  parameters?: string[];
}

/** 테마 타입 */
export interface Themes {
  id: string;
  name: string;
}

/** 백테스트 실행 요청 타입 */
export interface BacktestRunRequest {
  /* 기본 설정*/
  user_id: string; // 사용자 식별자
  strategy_name: string; // 전략 이름
  is_day_or_month: string;
  start_date: string; // 투자 시작일 YYYYMMDD
  end_date: string; // 투자 종료일 YYYYMMDD
  initial_investment: number; // 투자 금액(만원 단위)
  commission_rate: number; // 수수료율(%)
  /* 매수 조건 */
  buy_conditions: { // 매수 조건식
    name: string; // 조건식 이름 e.g. "A"
    expression: string; // 조건식 e.g. "{PER} > 10"
  }[]
  buy_logic: string; // 논리 조건식 e.g. "A and B"
  priority_factor: string; // 매수 종목 선택 우선순위 e.g. "{PBR}"
  priority_order: string; // 우선순위 방향 e.g. "desc"
  per_stock_ratio: number; // 종목당 매수 비중(%)
  max_holdings: number; // 최대 보유 종목 수 
  max_buy_value: number | null; // 종목당 최대 매수 금액(만원 단위) Nullable
  max_daily_stock: number | null; // 일일 최대 매수 종목 종류 수 Nullable
  buy_cost_basis: string; // 매수 가격 기준 e.g. "{전일 종가} 10"
  /* 매도 조건 */
  target_and_loss: {
    target_gain: number | null; // 매도 목표가(%) Nullable
    stop_loss: number | null; // 매도 손절가(%) Nullable
  } | null
  hold_days: {
    min_hold_days: number; // 최소 종목 보유일
    max_hold_days: number; // 최대 종목 보유일
    sell_cost_basis: string; // 매도 가격 기준 e.g. "{전일 종가} 10"
  } | null
  condition_sell: {
    sell_conditions: { // 매수 조건식
      name: string; // 조건식 이름 e.g. "A"
      expression: string; // 조건식 e.g. "{PER} > 10"
    }[]
    sell_logic: string; // 논리 조건식 e.g. "A and B"
    sell_cost_basis: string; // 매도 가격 기준 e.g. "{전일 종가} 10"
  } | null
  target_stocks: string[]; // 매매 대상 e.g. ["삼성전자", "크래프톤"]
}

/** 백테스트 실행 응답 타입 */
export interface BacktestRunResponse {
  /** 백테스트 결과 ID */
  backtestId: string;
  /** 상태 */
  status: "pending" | "running" | "completed" | "failed";
  /** 생성 시간 */
  createdAt: string;
}

/** 백테스트 결과 상세 타입 */
export interface BacktestResult {
  /** 백테스트 ID */
  id: string;
  /** 상태 */
  status: "pending" | "running" | "completed" | "failed";
  /** 통계 지표 */
  statistics: {
    totalReturn: number;
    annualizedReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    volatility: number;
  };
  /** 매매 결과 */
  trades: {
    /** 종목명 */
    stockName: string;
    /** 종목 코드 */
    stockCode: string;
    /** 매수가 */
    buyPrice: number;
    /** 매도가 */
    sellPrice: number;
    /** 수익 */
    profit: number;
    /** 수익률 */
    profitRate: number;
    /** 매수 일자 */
    buyDate: string;
    /** 매도 일자 */
    sellDate: string;
    /** 보유 비중 */
    weight: number;
    /** 평가 금액 */
    valuation: number;
  }[];
  /** 수익률 차트 데이터 */
  yieldPoints: {
    date: string;
    value: number;
    portfolioValue?: number;
    cash?: number;
    positionValue?: number;
    dailyReturn?: number;
    cumulativeReturn?: number;
  }[];
  /** 생성 시간 */
  createdAt: string;
  /** 완료 시간 */
  completedAt?: string;
}

/** 페이지네이션 요청 파라미터 */
export interface PaginationParams {
  page?: number;
  limit?: number;
}

/** 페이지네이션 응답 타입 */
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

/** API 에러 응답 타입 */
export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: unknown;
}
