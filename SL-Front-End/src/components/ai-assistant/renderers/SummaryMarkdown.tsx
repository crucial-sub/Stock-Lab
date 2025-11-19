/**
 * 백테스트 결과 마크다운 요약 컴포넌트
 *
 * BacktestCompleteData의 summary를 마크다운으로 렌더링합니다.
 * - StreamingMarkdownRenderer 재사용
 * - 완료된 결과이므로 isStreaming=false
 * - GPT 스타일로 배경 없이 마크다운만 표시
 *
 * 참조: 2025-01-19-ai-assistant-backtest-execution-plan.md 섹션 8.3
 */

"use client";

import { StreamingMarkdownRenderer } from "../StreamingMarkdownRenderer";

/**
 * SummaryMarkdown Props
 */
interface SummaryMarkdownProps {
  /** 마크다운 형식의 백테스트 요약 텍스트 */
  summary: string;
}

/**
 * 백테스트 결과 마크다운 요약 컴포넌트
 *
 * - StreamingMarkdownRenderer를 재사용하여 일관된 스타일 유지
 * - 완료된 결과이므로 스트리밍 효과 없음
 * - GPT 스타일: 배경/테두리 없이 마크다운만 렌더링
 *
 * @example
 * ```tsx
 * function BacktestResult() {
 *   return (
 *     <SummaryMarkdown
 *       summary="## 백테스트 결과 요약\n\n- 총 수익률: +15.3%\n- MDD: -8.2%"
 *     />
 *   );
 * }
 * ```
 */
export function SummaryMarkdown({ summary }: SummaryMarkdownProps) {
  return (
    <div className="w-full">
      <StreamingMarkdownRenderer
        content={summary}
        isStreaming={false}
        role="assistant"
      />
    </div>
  );
}
