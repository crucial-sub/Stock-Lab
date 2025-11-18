/**
 * AI 어시스턴트 채팅 세션 타입 정의
 *
 * 채팅 세션은 유저의 모든 대화를 포함하며,
 * Secondary Sidebar에서 관리됩니다.
 */

import type { Message } from "./message";

// 백테스트 설정 타입
export interface BacktestConfig {
  investmentAmount: number;  // 투자 금액 (만원 단위)
  startDate: string;          // 투자 시작일 (YYYY-MM-DD)
  endDate: string;            // 투자 종료일 (YYYY-MM-DD)
}

// 설문 답변 타입
export interface QuestionnaireAnswer {
  questionId: string;         // 질문 ID (q1, q2, q3, q4, q5)
  selectedOptionId: string;   // 선택한 옵션 ID
  tags: string[];             // 선택한 옵션의 태그 배열
}

// 채팅 세션 상태
export type SessionStatus =
  | "idle"                    // 초기 상태
  | "questionnaire"           // 설문 진행 중
  | "strategy_recommend"      // 전략 추천 중
  | "backtest"                // 백테스트 중
  | "completed";              // 완료됨

// 채팅 세션 타입
export interface ChatSession {
  id: string;                 // 세션 고유 ID
  title: string;              // 세션 제목 (첫 메시지 또는 자동 생성)
  messages: Message[];        // 메시지 히스토리
  createdAt: number;          // 생성 시각 (Unix timestamp)
  updatedAt: number;          // 업데이트 시각 (Unix timestamp)
  status: SessionStatus;      // 현재 세션 상태
  metadata?: {
    questionnaireAnswers?: QuestionnaireAnswer[];  // 설문 답변 배열
    selectedStrategy?: string;                      // 선택한 전략 ID
    backtestConfig?: BacktestConfig;                // 백테스트 설정
  };
}
