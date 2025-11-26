/**
 * API 응답 및 요청 타입 정의
 */

/** 팩터 타입 */
export interface Factor {
  id: number; // DB 기본키용 정수 ID
  name: string; // 비즈니스 로직용 이름 (예: "per", "pbr")
  display_name: string; // UI 표시용 한글 이름 (예: "주가수익비율")
  category: string;
  description?: string;
}

/** 함수 타입 (서브 팩터) */
export interface SubFactor {
  id: number; // DB 기본키용 정수 ID
  name: string; // 비즈니스 로직용 이름 (예: "past_val", "moving_avg_val")
  display_name: string; // UI 표시용 한글 이름 (예: "과거값", "이동평균")
  description: string; // 함수 설명
  arguments: string[]; // 선택 가능한 인자 목록 (예: ["1일", "2일", "3일"])
}

/** 테마 타입 */
export interface Themes {
  id: number; // DB 기본키용 정수 ID
  name: string; // 비즈니스 로직용 이름 (예: "construction", "finance")
  display_name: string; // UI 표시용 한글 이름 (예: "건설", "금융")
}

/** 백테스트 실행 요청 타입 */
export interface BacktestRunRequest {
  /* 기본 설정*/
  strategy_name: string; // 전략 이름
  is_day_or_month: string; // 백테스트 데이터 기준 ("일봉" | "월봉")
  start_date: string; // 투자 시작일 YYYYMMDD
  end_date: string; // 투자 종료일 YYYYMMDD
  initial_investment: number; // 투자 금액(만원 단위)
  commission_rate: number; // 수수료율(%)
  slippage: number; // 슬리피지(%)

  /* 매수 조건 */
  buy_conditions: {
    // 매수 조건식
    name: string; // 조건식 이름 e.g. "A"
    exp_left_side: string; // 조건식 좌변 = "함수({팩터}, {함수인자})" e.g. "이동평균({PER},{20일})"
    inequality: string; // 부등호 e.g. ">"
    exp_right_side: number; // 조건식 우변 e.g. 10
  }[];
  buy_logic: string; // 논리 조건식 e.g. "A and B"
  priority_factor: string; // 매수 종목 선택 우선순위 e.g. "{PBR}"
  priority_order: string; // 우선순위 방향 e.g. "desc"
  per_stock_ratio: number; // 종목당 매수 비중(%)
  max_holdings: number; // 최대 보유 종목 수
  max_buy_value: number | null; // 종목당 최대 매수 금액(만원 단위); Nullable(토글 off 시)
  max_daily_stock: number | null; // 일일 최대 매수 종목 종류 수; Nullable
  buy_price_basis: string; // 매수 가격 기준 e.g. "전일 종가"
  buy_price_offset: number; // 기준가 대비 증감값(%) e.g. 10

  /* 매도 조건 */
  target_and_loss: {
    // 목표가 / 손절가; Nullable
    target_gain: number | null; // 매도 목표가(%); Nullable
    stop_loss: number | null; // 매도 손절가(%); Nullable
  } | null;
  hold_days: {
    // 보유 기간; Nullable
    min_hold_days: number; // 최소 종목 보유일
    max_hold_days: number; // 최대 종목 보유일
    sell_price_basis: string; // 매도 가격 기준 e.g. "전일 종가"
    sell_price_offset: number; // 기준가 대비 증감값(%) e.g. 10
  } | null;
  condition_sell: {
    // 조건 매도; Nullable
    sell_conditions: {
      // 매도 조건식
      name: string; // 조건식 이름 e.g. "A"
      exp_left_side: string; // 조건식 좌변 = "함수({팩터}, {함수인자})" e.g. "이동평균({PER},{20일})"
      inequality: string; // 부등호 e.g. ">"
      exp_right_side: number; // 조건식 우변 e.g. 10
    }[];
    sell_logic: string; // 논리 조건식 e.g. "A and B"
    sell_price_basis: string; // 매도 가격 기준 e.g. "전일 종가"
    sell_price_offset: number; // 기준가 대비 증감값(%) e.g. 10
  } | null;

  /* 매매 대상 */
  trade_targets: {
    use_all_stocks: boolean; // 전체 종목을 그대로 쓸지 여부(true면 아래 선택 목록 무시하거나 참고만 함)
    selected_themes: string[]; // 선택한 테마 ID/코드 목록
    selected_stocks: string[]; // 개별로 지정한 종목 코드 목록 e.g. ["005930", "207940"]
    // UI 전용 필드 (백엔드 요청에는 포함되지 않음)
    selected_stock_count?: number; // 선택된 종목 수
    total_stock_count?: number; // 전체 종목 수
    total_theme_count?: number; // 전체 테마 수
  };
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

/** 유니버스 종목 정보 */
export interface UniverseStock {
  stockCode: string;
  stockName: string;
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
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    initialCapital: number;
    finalCapital: number;
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
    /** 수량 */
    quantity: number;
    /** 매매 사유 */
    reason?: string;
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
    dailyDrawdown?: number;
    buyCount?: number;
    sellCount?: number;
    /** 벤치마크 누적 수익률 (KOSPI 등) */
    benchmarkCumReturn?: number;
  }[];
  /** 유니버스 종목 목록 */
  universeStocks?: UniverseStock[];
  /** 생성 시간 */
  createdAt: string;
  /** 완료 시간 */
  completedAt?: string;
  /** AI 분석 요약 (마크다운 형식) */
  summary?: string;
}

/** 전략 팩터 설정 */
export interface StrategyFactorSettings {
  factorId: string;
  factorName: string;
  usageType: string;
  operator?: string;
  thresholdValue?: number;
  weight?: number;
  direction?: string;
}

/** 매매 규칙 설정 */
export interface TradingRuleSettings {
  ruleType: string;
  rebalanceFrequency?: string;
  rebalanceDay?: number;
  positionSizing?: string;
  maxPositions?: number;
  minHoldDays?: number;
  maxHoldDays?: number;
  minPositionWeight?: number;
  maxPositionWeight?: number;
  stopLossPct?: number;
  takeProfitPct?: number;
  commissionRate?: number;
  taxRate?: number;
  buyCondition?: Record<string, any>;
  sellCondition?: Record<string, any>;
}

/** 백테스트 설정 정보 */
export interface BacktestSettings {
  sessionName?: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  benchmark?: string;
  strategyName: string;
  strategyType?: string;
  strategyDescription?: string;
  universeType?: string;
  marketCapFilter?: string;
  sectorFilter?: string[];
  factors: StrategyFactorSettings[];
  tradingRules: TradingRuleSettings[];
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
