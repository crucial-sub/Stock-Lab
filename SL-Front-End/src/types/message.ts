/**
 * AI 어시스턴트 채팅 메시지 타입 정의
 *
 * 모든 메시지는 채팅 히스토리에 순차 누적되며,
 * UI 교체가 아닌 메시지 추가 방식으로 렌더링됨
 */

// 메시지 메타데이터
export interface MessageMetadata {
  questionId?: string;         // 설문 질문 ID
  selectedOption?: string;     // 선택한 옵션 ID
  strategyId?: string;         // 선택한 전략 ID
  backtestId?: string;         // 백테스트 실행 ID
  tags?: string[];             // 설문 답변 태그
}

// 기본 메시지 인터페이스
export interface BaseMessage {
  id: string;
  role: "user" | "assistant" | "system";
  createdAt: number; // Unix timestamp
  metadata?: MessageMetadata;
}

// 텍스트 메시지
export interface TextMessage extends BaseMessage {
  type: "text";
  content: string;
}

// 마크다운 메시지
export interface MarkdownMessage extends BaseMessage {
  type: "markdown";
  content: string;
}

// 설문 질문 메시지
export interface QuestionMessage extends BaseMessage {
  type: "question";
  questionId: string;
  text: string;
  options: QuestionOption[];
  order: number;
  total: number;
}

export interface QuestionOption {
  id: string;
  icon: string; // 이모지
  label: string;
  description: string;
  tags: string[];
}

// 유저 선택 메시지
export interface UserSelectionMessage extends BaseMessage {
  type: "user_selection";
  questionId: string;
  selectedOptionId: string;
  displayText: string;
}

// 전략 추천 메시지
export interface StrategyRecommendationMessage extends BaseMessage {
  type: "strategy_recommendation";
  strategies: Strategy[];
}

export interface Strategy {
  id: string;
  name: string;
  summary: string;
  description: string;
  tags: string[];
  matchScore: number; // 0-100, 태그 일치도
  conditions: Condition[];
}

export interface Condition {
  condition: string;
  condition_info: string[];
}

// 백테스트 결과 메시지
export interface BacktestResultMessage extends BaseMessage {
  type: "backtest_result";
  backtestId: string;
  results: BacktestResults;
}

export interface BacktestResults {
  statistics: BacktestStatistics;
  charts: BacktestChart[];
  summary: string[];
}

export interface BacktestStatistics {
  total_return: number;      // 누적 수익률 (%)
  cagr: number;              // 연평균 수익률 (%)
  mdd: number;               // 최대 낙폭 (%)
  initial_investment: number; // 투자 원금
  final_assets: number;       // 최종 자산
  profit: number;             // 총 손익
}

export interface BacktestChart {
  type: "period_returns" | "cumulative_returns" | "total_assets";
  data: ChartDataPoint[];
}

export interface ChartDataPoint {
  period?: string;  // 기간 (1D, 1W, 1M 등)
  date?: string;    // 날짜
  return?: number;  // 수익률 (%)
  assets?: number;  // 자산 (원)
}

// 모든 메시지 타입 유니온
export type Message =
  | TextMessage
  | MarkdownMessage
  | QuestionMessage
  | UserSelectionMessage
  | StrategyRecommendationMessage
  | BacktestResultMessage;
