/**
 * AI Chatbot API Client
 * 챗봇 API 엔드포인트: http://localhost:8003/api/v1/chat/message
 */

import axios from "axios";

const CHATBOT_API_URL = process.env.NEXT_PUBLIC_CHATBOT_API_URL ?? "http://localhost:8003";

// Chatbot용 별도 axios 인스턴스 (인증 불필요)
const chatbotAxios = axios.create({
  baseURL: CHATBOT_API_URL,
  timeout: 60000, // LLM 응답 대기 시간 60초
  headers: {
    "Content-Type": "application/json",
  },
});

// ============ Types ============

export interface ChatRequest {
  message: string;
  session_id?: string;
  answer?: {
    question_id: string;
    option_id: string;
  };
  client_type?: "assistant" | "ai_helper";
}

export interface OptionCard {
  id: string;
  label: string;
  description: string;
  icon: string;
  tags: string[];
}

export interface Question {
  question_id: string;
  text: string;
  options: OptionCard[];
}

export interface QuestionnaireUILanguage {
  type: "questionnaire_start" | "questionnaire_progress";
  total_questions: number;
  current_question: number;
  progress_percentage?: number;
  question: Question;
}

export interface ConditionPreview {
  condition: string;
  condition_info: string[];
}

export interface StrategyRecommendation {
  rank: number;
  strategy_id: string;
  strategy_name: string;
  summary: string;
  match_score: number;
  match_percentage: number;
  match_reasons: string[];
  tags: string[];
  conditions_preview: ConditionPreview[];
  icon: string;
  badge?: string;
}

export interface UserProfileSummary {
  investment_period: string;
  investment_style: string;
  risk_tolerance: string;
  dividend_preference: string;
  sector_preference: string;
}

export interface RecommendationUILanguage {
  type: "strategy_recommendation";
  recommendations: StrategyRecommendation[];
  user_profile_summary: UserProfileSummary;
}

export interface BacktestConfigurationUILanguage {
  type: "backtest_configuration";
  strategy: {
    strategy_id: string;
    strategy_name: string;
  };
  configuration_fields: ConfigurationField[];
}

export interface ConfigurationField {
  field_id: string;
  label: string;
  type: "number" | "date" | "select" | "text";
  unit?: string;
  default_value?: any;
  min_value?: any;
  max_value?: any;
  step?: any;
  required: boolean;
  description?: string;
  options?: { value: string; label: string }[];
}

export type UILanguage =
  | QuestionnaireUILanguage
  | RecommendationUILanguage
  | BacktestConfigurationUILanguage;

export interface ChatResponse {
  answer: string;
  intent: string;
  session_id: string;
  ui_language?: UILanguage;
  context?: string;
  sources?: any[];
  backtest_conditions?: DSLCondition[];  // 매수/매도 조건이 있을 경우
}

// ============ API Functions ============

/**
 * 챗봇에 메시지 전송
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await chatbotAxios.post<ChatResponse>("/api/v1/chat/message", request);
  return response.data;
}

/**
 * 세션 삭제
 */
export async function deleteSession(sessionId: string): Promise<void> {
  await chatbotAxios.delete(`/api/v1/chat/session/${sessionId}`);
}

/**
 * 헬스 체크
 */
export async function checkHealth(): Promise<{ status: string; version: string }> {
  const response = await chatbotAxios.get("/api/v1/health");
  return response.data;
}

// ============ DSL API ============

export interface DSLCondition {
  factor: string;
  params: any[];
  operator: string;
  right_factor?: string;
  right_params?: any[];
  value?: number;
}

export interface DSLRequest {
  text: string;
}

export interface DSLResponse {
  conditions: DSLCondition[];
}

/**
 * 자연어 전략 설명을 DSL JSON으로 변환
 */
export async function parseDSL(text: string): Promise<DSLResponse> {
  const response = await chatbotAxios.post<DSLResponse>("/api/v1/dsl/parse", {
    text,
  });
  return response.data;
}
