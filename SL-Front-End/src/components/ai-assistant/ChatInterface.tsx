"use client";

import { ChatResponse } from "@/lib/api/chatbot";
import { QuestionnaireView } from "./QuestionnaireView";
import { RecommendationView } from "./RecommendationView";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  chatResponse: ChatResponse | null;
  isLoading: boolean;
  onAnswerSelect: (questionId: string, optionId: string, answerText: string) => void;
  messages?: Message[];
  questionHistory?: Array<{
    questionId: string;
    selectedOptionId: string;
    question: any;
  }>;
}

/**
 * AI 챗봇 대화 인터페이스
 *
 * @description UI Language에 따라 적절한 화면을 렌더링합니다:
 * - questionnaire_start/progress: 설문조사 화면
 * - strategy_recommendation: 전략 추천 결과
 * - backtest_configuration: 백테스트 설정 화면
 */
export function ChatInterface({
  chatResponse,
  isLoading,
  onAnswerSelect,
  messages,
  questionHistory,
}: ChatInterfaceProps) {
  console.log("ChatInterface - chatResponse:", chatResponse);
  console.log("ChatInterface - ui_language:", chatResponse?.ui_language);
  console.log("ChatInterface - ui_language.type:", chatResponse?.ui_language?.type);

  if (!chatResponse?.ui_language) {
    console.log("ChatInterface - No ui_language, returning null");
    return null;
  }

  const { ui_language } = chatResponse;

  // 설문조사 화면
  if (
    ui_language.type === "questionnaire_start" ||
    ui_language.type === "questionnaire_progress"
  ) {
    return (
      <QuestionnaireView
        uiLanguage={ui_language}
        isLoading={isLoading}
        onAnswerSelect={onAnswerSelect}
        messages={messages}
        questionHistory={questionHistory}
      />
    );
  }

  // 전략 추천 결과
  if (ui_language.type === "strategy_recommendation") {
    return <RecommendationView uiLanguage={ui_language} />;
  }

  // 백테스트 설정 (향후 구현)
  if (ui_language.type === "backtest_configuration") {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">백테스트 설정</h2>
        <p className="text-gray-600">백테스트 설정 화면 구현 예정</p>
      </div>
    );
  }

  return null;
}
