/**
 * 퀀트 전략 타입 정의
 */

/**
 * 전략 데이터 구조
 */
export interface Strategy {
  /** 전략 고유 ID (session_id) */
  id: string;
  /** 전략 이름 */
  name: string;
  /** 일평균 수익률 (%) */
  dailyAverageReturn: number;
  /** 누적 수익률 (%) */
  cumulativeReturn: number;
  /** 투자 수익률 (MDD - Max Drawdown) (%) */
  maxDrawdown: number;
  /** 생성일 */
  createdAt: string;
  /** 백테스트 실행 상태 (PENDING/RUNNING/COMPLETED/FAILED) */
  status?: string;
  /** 백테스트 진행률 (0-100) */
  progress?: number;
}

/**
 * 전략 목록 응답 데이터
 */
export interface StrategyListResponse {
  strategies: Strategy[];
  totalCount: number;
  currentPage: number;
  totalPages: number;
}

/**
 * 전략 검색 파라미터
 */
export interface StrategySearchParams {
  /** 검색 키워드 (전략 이름) */
  keyword?: string;
  /** 페이지 번호 (1부터 시작) */
  page?: number;
  /** 페이지당 항목 수 */
  pageSize?: number;
}

/**
 * 전략 삭제 파라미터
 */
export interface DeleteStrategyParams {
  /** 삭제할 전략 ID 배열 */
  strategyIds: number[];
}
