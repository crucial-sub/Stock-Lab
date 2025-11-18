/**
 * AI 응답 대기 타이핑 인디케이터
 *
 * GPT 스타일의 인터랙티브한 로딩 UI
 * - 부드러운 점 애니메이션
 * - 깔끔한 디자인
 * - 스트리밍 시작 전에만 표시
 */

"use client";

/**
 * AI가 응답을 생각하고 있음을 나타내는 타이핑 인디케이터 컴포넌트
 */
export function AITypingIndicator() {
  return (
    <div className="flex justify-start mb-6">
      <div className="flex items-center space-x-2 px-4 py-3">
        {/* 점 애니메이션 */}
        <div className="flex space-x-1">
          <div
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: "0ms", animationDuration: "1.4s" }}
          />
          <div
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: "200ms", animationDuration: "1.4s" }}
          />
          <div
            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: "400ms", animationDuration: "1.4s" }}
          />
        </div>

        {/* 텍스트 */}
        <span className="text-sm text-gray-500 ml-2">
          AI가 답변을 생성하고 있습니다...
        </span>
      </div>
    </div>
  );
}
