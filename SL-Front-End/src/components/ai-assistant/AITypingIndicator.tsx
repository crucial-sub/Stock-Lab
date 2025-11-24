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
          @keyframes gradientShift {
            0% {
              background-position: 0% 50%;
            }
            50% {
              background-position: 100% 50%;
            }
            100% {
              background-position: 0% 50%;
            }
          }
          .typing-gradient {
            background: linear-gradient(
              90deg,
              rgb(var(--color-brand-purple) / 0.35),
              rgb(var(--color-brand-purple)),
              rgb(var(--color-brand-purple) / 0.35)
            );
            background-size: 200% 200%;
            animation: gradientShift 1.5s ease infinite;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
          }
        `
      }} />

      <div className="flex items-center space-x-0 py-5">
        {/* 텍스트 */}
        <span className="text-base font-semibold flex items-center typing-gradient">
          AI가 답변을 생각하고 있습니다...
        </span>
      </div>
    </div>
  );
}
