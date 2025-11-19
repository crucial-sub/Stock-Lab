"use client";

import { useRef, useEffect } from "react";
import { QuestionnaireUILanguage } from "@/lib/api/chatbot";
import { Message } from "@/types/message";

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

  const currentQuestionRef = useRef<HTMLDivElement>(null);

  // 새 질문이 로드되면 자동 스크롤
  useEffect(() => {
    if (currentQuestionRef.current && !isLoading) {
      setTimeout(() => {
        currentQuestionRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 100);
    }
  }, [current_question, isLoading]);

  if (!question) return null;

  return (
    <div className="w-full max-w-[1000px] mx-auto space-y-8">
      {/* 이전 질문들 (기록) */}
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

      {/* 현재 질문 */}
      <div ref={currentQuestionRef} className="space-y-4">
        <div className="flex justify-start">
          <div className="max-w-[95%] rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
            <div className="mb-2 flex items-center justify-between text-xs font-semibold text-gray-500">
              <span>{`질문 ${current_question} / ${total_questions}`}</span>
              <span className="text-purple-600">
                {progress_percentage ?? Math.round((current_question / total_questions) * 100)}%
              </span>
            </div>
            <p className="text-[15px] font-semibold text-gray-900">
              {`Q${current_question}. ${question.text}`}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {question.options.map((option) => (
            <label
              key={option.id}
              className={[
                "flex items-start gap-3 rounded-2xl border px-4 py-4 transition-all",
                "bg-white",
                isLoading
                  ? "opacity-50 cursor-not-allowed"
                  : "hover:border-purple-400 hover:bg-purple-50",
              ].join(" ")}
            >
              <input
                type="radio"
                name={`${question.question_id}-${current_question}`}
                value={option.id}
                disabled={isLoading}
                onChange={() =>
                  !isLoading &&
                  onAnswerSelect(question.question_id, option.id, option.label)
                }
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
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center">
          <div className="flex items-center gap-2 rounded-full bg-gray-100 px-4 py-2">
            <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-purple-600" />
            <p className="text-sm text-gray-600">응답 처리 중...</p>
          </div>
        </div>
      )}
    </div>
  );
}
