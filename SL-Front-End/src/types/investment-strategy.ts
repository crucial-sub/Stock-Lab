/**
 * 투자 전략 관련 타입 정의
 */

/**
 * UI 표시용 조건
 */
export interface DisplayCondition {
  /** 조건 표시 문자열 (예: "ROE > 15%") */
  condition: string;
  /** 조건 설명 배열 */
  condition_info: string[];
}

/**
 * 전략 추천 요청
 */
export interface StrategyRecommendationRequest {
  /** 사용자 설문 결과 태그 */
  user_tags: string[];
  /** 추천할 전략 개수 (기본값: 3) */
  top_n?: number;
}

/**
 * 추천된 전략 정보 (목록용)
 */
export interface StrategyMatch {
  /** 전략 ID */
  id: string;
  /** 전략명 */
  name: string;
  /** 전략 요약 */
  summary: string;
  /** 전략 태그 */
  tags: string[];
  /** 매칭 점수 (0-100) */
  match_score: number;
  /** 일치하는 태그 */
  matched_tags: string[];
  /** 일치하지 않는 태그 */
  unmatched_tags: string[];
  /** UI 표시용 조건 */
  display_conditions: DisplayCondition[];
}

/**
 * 전략 상세 정보 (백테스트 실행용)
 */
export interface StrategyDetail {
  /** 전략 ID */
  id: string;
  /** 전략명 */
  name: string;
  /** 전략 요약 */
  summary: string;
  /** 전략 상세 설명 */
  description?: string;
  /** 전략 태그 */
  tags: string[];
  /** 백테스트 실행 설정 (user_id, start_date, end_date, initial_investment 제외) */
  backtest_config: Record<string, any>;
  /** UI 표시용 조건 */
  display_conditions: DisplayCondition[];
  /** 인기도 점수 */
  popularity_score: number;
  /** 생성일시 */
  created_at: string;
  /** 수정일시 */
  updated_at: string;
}
