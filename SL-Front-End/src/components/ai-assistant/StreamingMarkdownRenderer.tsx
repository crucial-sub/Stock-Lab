/**
 * 스트리밍 마크다운 렌더러
 *
 * 실시간으로 전송되는 마크다운 콘텐츠를 GPT 스타일로 렌더링합니다.
 * - 실시간 마크다운 파싱 및 렌더링
 * - 커서 깜빡임 애니메이션 (스트리밍 중일 때만)
 * - GPT 스타일: AI 응답은 배경/테두리 없이 마크다운만 렌더링
 * - 공통 마크다운 컴포넌트 사용 (중복 제거)
 *
 * 참조: AI_assistant_feature_spec.md 섹션 3.1, 3.3
 */

"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { normalizeMarkdown, limitBullets } from "@/lib/markdown-utils";
import { markdownComponents, markdownProseClasses } from "./renderers/shared/MarkdownComponents";

interface StreamingMarkdownRendererProps {
  /** 실시간으로 업데이트되는 콘텐츠 */
  content: string;
  /** 스트리밍 진행 중 여부 (커서 표시 제어) */
  isStreaming: boolean;
  /** 메시지 역할 (user 또는 assistant) */
  role?: "user" | "assistant";
  /** compact 모드: 불릿 개수 제한 */
  compactMaxBullets?: number;
}

/**
 * 스트리밍 마크다운 메시지를 실시간으로 렌더링하는 컴포넌트
 * GPT 스타일: 배경/테두리 없이 마크다운만 렌더링
 *
 * @example
 * ```tsx
 * function ChatMessage() {
 *   const { content, isStreaming } = useChatStream("session_123");
 *
 *   return (
 *     <StreamingMarkdownRenderer
 *       content={content}
 *       isStreaming={isStreaming}
 *       role="assistant"
 *     />
 *   );
 * }
 * ```
 */
export function StreamingMarkdownRenderer({
  content,
  isStreaming,
  role = "assistant",
  compactMaxBullets,
}: StreamingMarkdownRendererProps) {
  const isUser = role === "user";

  // 마크다운 정규화: 헤딩과 리스트 앞뒤에 줄바꿈 추가
  const normalizedContent = normalizeMarkdown(content);
  const finalContent =
    typeof compactMaxBullets === "number"
      ? limitBullets(normalizedContent, compactMaxBullets)
      : normalizedContent;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div
        className={[
          "max-w-[75%]",
          isUser
            ? "px-5 py-3.5 bg-blue-600 text-white rounded-2xl shadow-sm"
            : "", // AI 응답: 배경/테두리 없이 마크다운만 렌더링 (GPT 스타일)
        ].join(" ")}
      >
        {isUser ? (
          // 사용자 메시지는 단순 텍스트
          <div className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {content}
          </div>
        ) : (
          // AI 응답: GPT 스타일 마크다운 렌더링 (공통 컴포넌트 사용)
          <div className={markdownProseClasses}>
            <div className="relative">
              {/* 마크다운 콘텐츠 */}
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight, rehypeRaw]}
                components={markdownComponents}
              >
                {finalContent}
              </ReactMarkdown>

              {/* 커서 깜빡임 애니메이션 (스트리밍 중일 때만 표시) */}
              {isStreaming && (
                <span
                  className="inline-block w-2 h-5 ml-1 bg-gray-900 animate-blink"
                  aria-label="타이핑 중"
                >
                  ▌
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 커서 깜빡임 애니메이션을 위한 CSS 클래스
 * tailwind.config.ts에 추가 필요:
 *
 * ```ts
 * module.exports = {
 *   theme: {
 *     extend: {
 *       animation: {
 *         blink: 'blink 1s step-end infinite',
 *       },
 *       keyframes: {
 *         blink: {
 *           '0%, 50%': { opacity: '1' },
 *           '50.01%, 100%': { opacity: '0' },
 *         },
 *       },
 *     },
 *   },
 * }
 * ```
 */
