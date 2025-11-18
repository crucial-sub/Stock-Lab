/**
 * 스트리밍 마크다운 렌더러
 *
 * 실시간으로 전송되는 마크다운 콘텐츠를 즉시 렌더링합니다.
 * - 실시간 마크다운 파싱 및 렌더링
 * - 커서 깜빡임 애니메이션 (스트리밍 중일 때만)
 * - 즉시 렌더링 (인위적 딜레이 없음)
 *
 * 참조: AI_assistant_feature_spec.md 섹션 3.1, 3.3
 */

"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";

interface StreamingMarkdownRendererProps {
  /** 실시간으로 업데이트되는 콘텐츠 */
  content: string;
  /** 스트리밍 진행 중 여부 (커서 표시 제어) */
  isStreaming: boolean;
  /** 메시지 역할 (user 또는 assistant) */
  role?: "user" | "assistant";
}

/**
 * 스트리밍 마크다운 메시지를 실시간으로 렌더링하는 컴포넌트
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
}: StreamingMarkdownRendererProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div
        className={[
          "max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white text-gray-900 border border-gray-200",
        ].join(" ")}
      >
        <div className="text-[15px] leading-relaxed markdown-content">
          <div className="relative">
            {/* 마크다운 콘텐츠 */}
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight, rehypeRaw]}
              components={{
                // 제목 스타일링
                h1: ({ node, ...props }) => (
                  <h1 className="text-2xl font-bold mb-4 mt-6" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-xl font-semibold mb-3 mt-5" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-lg font-semibold mb-2 mt-4" {...props} />
                ),

                // 코드 블록 스타일링
                code: ({ node, className, children, ...props }: any) => {
                  const isInline = !className?.includes("language-");

                  if (isInline) {
                    return (
                      <code
                        className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code
                      className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },

                // 테이블 스타일링
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-4">
                    <table
                      className="min-w-full border border-gray-300"
                      {...props}
                    />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th
                    className="border border-gray-300 bg-gray-100 px-4 py-2 text-left font-semibold"
                    {...props}
                  />
                ),
                td: ({ node, ...props }) => (
                  <td
                    className="border border-gray-300 px-4 py-2"
                    {...props}
                  />
                ),

                // 리스트 스타일링
                ul: ({ node, ...props }) => (
                  <ul
                    className="list-disc list-inside mb-4 space-y-1"
                    {...props}
                  />
                ),
                ol: ({ node, ...props }) => (
                  <ol
                    className="list-decimal list-inside mb-4 space-y-1"
                    {...props}
                  />
                ),

                // 링크 스타일링
                a: ({ node, ...props }) => (
                  <a
                    className="text-blue-600 hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                    {...props}
                  />
                ),

                // 인용구 스타일링
                blockquote: ({ node, ...props }) => (
                  <blockquote
                    className="border-l-4 border-gray-300 pl-4 italic my-4"
                    {...props}
                  />
                ),

                // 수평선 스타일링
                hr: ({ node, ...props }) => (
                  <hr className="my-6 border-t border-gray-300" {...props} />
                ),

                // 단락 스타일링
                p: ({ node, ...props }) => (
                  <p className="mb-4 leading-relaxed" {...props} />
                ),
              }}
            >
              {content}
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
      </div>
    </div>
  );
}

/**
 * 커서 깨깜임 애니메이션을 위한 CSS 클래스
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
