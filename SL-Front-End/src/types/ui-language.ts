/**
 * UI Language 스키마 정의
 *
 * AI가 구조화된 JSON을 반환하여 프론트엔드가 특정 UI 컴포넌트를 렌더링하도록 지시하는 방식
 * 버저닝 시스템을 포함하여 스키마 변경 시 backward compatibility 유지
 */

import type { Strategy, BacktestResults } from "./message";

// UI Language 버전
export type UILanguageVersion = "1.0";

// UI Language 타입
export type UILanguageType =
  | "questionnaire_start"
  | "questionnaire_progress"
  | "strategy_recommendation"
  | "backtest_configuration"
  | "backtest_result"
  | "general_response";

// UI Language 기본 구조
export interface UILanguage {
  version: UILanguageVersion;
  type: UILanguageType;
  fragments: UIFragment[];
}

// Fragment 타입 유니온
export type UIFragment =
  | TextFragment
  | MarkdownFragment
  | QuestionFragment
  | StrategyCardFragment
  | BacktestFormFragment
  | BacktestResultFragment
  | DividerFragment
  | ButtonFragment;

// 텍스트 Fragment
export interface TextFragment {
  kind: "text";
  content: string;
}

// 마크다운 Fragment
export interface MarkdownFragment {
  kind: "markdown";
  content: string;
}

// 설문 질문 Fragment
export interface QuestionFragment {
  kind: "question";
  questionId: string;
  text: string;
  order: number;
  total: number;
  options: QuestionFragmentOption[];
}

export interface QuestionFragmentOption {
  id: string;
  icon: string; // 이모지
  label: string;
  description: string;
  tags: string[];
}

// 전략 카드 Fragment
export interface StrategyCardFragment {
  kind: "strategy_card";
  strategies: Strategy[];
}

// 백테스트 설정 폼 Fragment
export interface BacktestFormFragment {
  kind: "backtest_form";
  strategyId: string;
  fields: BacktestField[];
}

export interface BacktestField {
  id: string;
  type: "number" | "date" | "select";
  label: string;
  placeholder?: string;
  defaultValue: string | number;
  validation: {
    required: boolean;
    min?: number;
    max?: number;
    pattern?: string;
  };
}

// 백테스트 결과 Fragment
export interface BacktestResultFragment {
  kind: "backtest_result";
  backtestId: string;
  results: BacktestResults;
}

// 구분선 Fragment
export interface DividerFragment {
  kind: "divider";
}

// 버튼 Fragment
export interface ButtonFragment {
  kind: "button";
  action: string;
  label: string;
  style: "primary" | "secondary" | "outline";
}
