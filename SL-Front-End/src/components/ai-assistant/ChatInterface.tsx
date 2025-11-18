"use client";

import { ChatResponse } from "@/lib/api/chatbot";
import { Message } from "@/types/message";
import { QuestionnaireView } from "./QuestionnaireView";
import { RecommendationView } from "./RecommendationView";

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

  // 전략 추천 결과 (설문 히스토리 포함)
  if (ui_language.type === "strategy_recommendation") {
    return (
      <div className="w-full max-w-[1000px] mx-auto space-y-8">
        {/* 설문 히스토리 표시 */}
        {questionHistory && questionHistory.length > 0 && (
          <div className="space-y-6">
            {questionHistory.map((historyItem, idx) => (
              <div key={idx} className="space-y-3">
                <div className="flex justify-start">
                  <div className="max-w-[95%] rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
                    <p className="text-[15px] font-semibold text-gray-900">
                      {`Q${idx + 1}. ${historyItem.question.text}`}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {historyItem.question.options.map((option: any) => {
                    const isSelected = option.id === historyItem.selectedOptionId;
                    return (
                      <label
                        key={option.id}
                        className={[
                          "flex items-start gap-3 rounded-2xl border px-4 py-4 transition-all",
                          "bg-white",
                          isSelected
                            ? "border-purple-500 bg-purple-50"
                            : "border-gray-200 opacity-60",
                        ].join(" ")}
                      >
                        <input
                          type="radio"
                          name={historyItem.questionId}
                          value={option.id}
                          checked={isSelected}
                          disabled
                          className="mt-1 h-5 w-5 text-purple-600 border-gray-300 focus:ring-purple-500"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className="text-lg">{option.icon}</div>
                            <h3 className="text-sm font-bold text-gray-900">
                              {option.label}
                            </h3>
                          </div>
                          <p className="mt-1 text-sm text-gray-600">
                            {option.description}
                          </p>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 추천 결과 */}
        <RecommendationView uiLanguage={ui_language} />
      </div>
    );
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
