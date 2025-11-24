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

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { markdownComponents, markdownProseClasses } from "./shared/MarkdownComponents";

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
  // summary 앞뒤 빈 줄 제거
  let processedSummary = summary.trim();

  // 모든 헤딩을 h3로 통일 (###)
  // 백엔드에서 ###로 보내지만 첫 번째가 ##로 변경되는 문제 해결
  processedSummary = processedSummary
    .replace(/^#{1,6}\s+/gm, "### "); // 모든 헤딩을 h3로 통일

  // normalizeMarkdown을 우회하고 직접 ReactMarkdown으로 렌더링
  return (
    <div className="w-full">
      <div className={markdownProseClasses}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight, rehypeRaw]}
          components={markdownComponents}
        >
          {processedSummary}
        </ReactMarkdown>
      </div>
    </div>
  );
}
