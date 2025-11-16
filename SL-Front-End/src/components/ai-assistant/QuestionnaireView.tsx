"use client";

import { QuestionnaireUILanguage } from "@/lib/api/chatbot";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface QuestionnaireViewProps {
  uiLanguage: QuestionnaireUILanguage;
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
 * 설문조사 화면
 *
 * @description 질문과 옵션 카드를 표시하고 사용자 응답을 받습니다
 */
export function QuestionnaireView({
  uiLanguage,
  isLoading,
  onAnswerSelect,
  messages,
  questionHistory,
}: QuestionnaireViewProps) {
  const { question, current_question, total_questions, progress_percentage } =
    uiLanguage;

  if (!question) return null;

  return (
    <div className="w-full max-w-[1000px] mx-auto">
      {/* 이전 질문들 (라디오 버튼과 함께) */}
      {questionHistory && questionHistory.length > 0 && (
        <div className="mb-8 space-y-6">
          {questionHistory.map((historyItem, idx) => (
            <div key={idx}>
              {/* AI 질문 메시지 */}
              <div className="flex justify-start mb-6">
                <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm bg-white text-gray-900 border border-gray-200">
                  <p className="text-[15px] leading-relaxed font-medium">{historyItem.question.text}</p>
                </div>
              </div>

              {/* 선택된 옵션만 표시 (라디오 버튼 체크 상태) */}
              <div className="space-y-2 mb-6">
                {historyItem.question.options.map((option: any) => (
                  <label
                    key={option.id}
                    className={[
                      "flex items-start gap-3 p-4 rounded-lg cursor-pointer transition-all",
                      "border-2 bg-white",
                      option.id === historyItem.selectedOptionId
                        ? "border-blue-500 bg-blue-50"
                        : "opacity-30",
                    ].join(" ")}
                  >
                    {/* 라디오 버튼 */}
                    <input
                      type="radio"
                      name={historyItem.questionId}
                      value={option.id}
                      checked={option.id === historyItem.selectedOptionId}
                      disabled={true}
                      className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />

                    {/* 아이콘 */}
                    <div className="text-xl flex-shrink-0">{option.icon}</div>

                    <div className="flex-1">
                      {/* 레이블 */}
                      <h3 className="text-sm font-bold text-black mb-0.5">
                        {option.label}
                      </h3>

                      {/* 설명 */}
                      <p className="text-xs text-gray-600 mb-1.5">{option.description}</p>

                      {/* 태그 */}
                      {option.tags && option.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {option.tags.map((tag: string, tagIdx: number) => (
                            <span
                              key={tagIdx}
                              className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI 질문 메시지 */}
      <div className="flex justify-start mb-6">
        <div className="max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm bg-white text-gray-900 border border-gray-200">
          {/* 진행률 */}
          <div className="mb-3 pb-3 border-b border-gray-200">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-medium text-gray-500">
                질문 {current_question} / {total_questions}
              </span>
              {progress_percentage !== undefined && (
                <span className="text-xs font-medium text-blue-600">
                  {progress_percentage}%
                </span>
              )}
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                style={{
                  width: `${progress_percentage ?? (current_question / total_questions) * 100}%`,
                }}
              />
            </div>
          </div>

          {/* 질문 텍스트 */}
          <p className="text-[15px] leading-relaxed font-medium">{question.text}</p>
        </div>
      </div>

      {/* 옵션 라디오 버튼들 */}
      <div className="space-y-2 mb-6">
        {question.options.map((option) => (
          <label
            key={option.id}
            className={[
              "flex items-start gap-3 p-4 rounded-lg cursor-pointer transition-all",
              "border-2 bg-white",
              isLoading ? "opacity-50 cursor-not-allowed" : "hover:bg-gray-50",
            ].join(" ")}
          >
            {/* 라디오 버튼 */}
            <input
              type="radio"
              name={question.question_id}
              value={option.id}
              disabled={isLoading}
              onChange={() => !isLoading && onAnswerSelect(question.question_id, option.id, option.label)}
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
            />

            {/* 아이콘 */}
            <div className="text-xl flex-shrink-0">{option.icon}</div>

            <div className="flex-1">
              {/* 레이블 */}
              <h3 className="text-sm font-bold text-black mb-0.5">
                {option.label}
              </h3>

              {/* 설명 */}
              <p className="text-xs text-gray-600 mb-1.5">{option.description}</p>

              {/* 태그 */}
              {option.tags && option.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {option.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </label>
        ))}
      </div>

      {/* 로딩 상태 */}
      {isLoading && (
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
            <p className="text-sm text-gray-600">응답 처리 중...</p>
          </div>
        </div>
      )}
    </div>
  );
}
