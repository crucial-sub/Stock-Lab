/**
 * 설문 질문 메시지 렌더러
 *
 * 설문 질문과 선택지를 카드 형태로 렌더링
 * 유저가 선택하면 다음 질문으로 진행
 */

"use client";

import { useState } from "react";
import type { QuestionMessage } from "@/types/message";

interface QuestionRendererProps {
  message: QuestionMessage;
}

/**
 * 설문 질문을 렌더링하는 컴포넌트
 */
export function QuestionRenderer({ message }: QuestionRendererProps) {
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);

  // 다음 질문으로 진행하는 핸들러 (추후 구현)
  function handleNext() {
    if (!selectedOptionId) return;

    // TODO: 선택한 답변을 채팅 히스토리에 추가
    // TODO: 다음 질문을 요청하거나 로컬에서 표시
    console.log("Selected:", selectedOptionId);
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[95%] w-full space-y-4">
        {/* 질문 텍스트 */}
        <div className="rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
          <p className="text-[15px] font-semibold text-gray-900">
            Q{message.order}. {message.text}
          </p>
          <p className="mt-1 text-xs text-gray-500">
            {message.order}/{message.total}
          </p>
        </div>

        {/* 선택지 */}
        <div className="space-y-2">
          {message.options.map((option) => (
            <label
              key={option.id}
              className={[
                "flex items-start gap-3 rounded-2xl border px-4 py-4 cursor-pointer transition-all",
                selectedOptionId === option.id
                  ? "border-purple-500 bg-purple-50"
                  : "border-gray-200 bg-white hover:border-purple-300",
              ].join(" ")}
            >
              <input
                type="radio"
                name={message.questionId}
                value={option.id}
                checked={selectedOptionId === option.id}
                onChange={() => setSelectedOptionId(option.id)}
                className="mt-1 h-5 w-5 text-purple-600"
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

        {/* 다음 버튼 */}
        <button
          onClick={handleNext}
          disabled={!selectedOptionId}
          className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-purple-700 transition-colors"
        >
          다음
        </button>
      </div>
    </div>
  );
}
