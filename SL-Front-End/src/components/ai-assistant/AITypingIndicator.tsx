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
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes bigBounce {
            0%, 100% {
              transform: translateY(0) scale(1);
            }
            50% {
              transform: translateY(-20px) scale(1.1);
            }
          }
          .big-bounce {
            animation: bigBounce 1s ease-in-out infinite;
          }
        `
      }} />

      <div className="flex items-center space-x-3 px-5 py-4">
        {/* 점 애니메이션 - 더 큰 폭으로 튀기기 */}
        <div className="flex items-center space-x-1.5" style={{ minHeight: "12px" }}>
          <div
            className="w-3 h-3 bg-gray-500 rounded-full big-bounce"
            style={{ animationDelay: "0ms" }}
          />
          <div
            className="w-3 h-3 bg-gray-500 rounded-full big-bounce"
            style={{ animationDelay: "200ms" }}
          />
          <div
            className="w-3 h-3 bg-gray-500 rounded-full big-bounce"
            style={{ animationDelay: "400ms" }}
          />
        </div>

        {/* 텍스트 */}
        <span className="text-base text-gray-600 font-medium ml-2 flex items-center">
          AI가 답변을 생성하고 있습니다...
        </span>
      </div>
    </div>
  );
}
