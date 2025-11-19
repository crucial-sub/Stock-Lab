"use client";

import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  backtestConditions?: any; // array 또는 { buy, sell }
}

/**
 * 채팅 메시지 컴포넌트 - 완전한 마크다운 렌더링 지원
 */
export function ChatMessage({ role, content, backtestConditions }: ChatMessageProps) {
  const isUser = role === "user";
  const router = useRouter();

  const extractBuyConditions = () => {
    if (!backtestConditions) return [];
    if (Array.isArray(backtestConditions)) return backtestConditions;
    if (Array.isArray(backtestConditions?.buy)) return backtestConditions.buy;
    return [];
  };

  const buyConditions = extractBuyConditions();
  const hasConditions = buyConditions.length > 0;

  const handleBacktest = () => {
    if (!hasConditions) return;

    const queryParams = new URLSearchParams({
      conditions: JSON.stringify(buyConditions),
    });
    // 백테스트 신규 페이지로 이동하며 조건을 전달
    router.push(`/quant/new?${queryParams.toString()}`);
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}>
      <div
        className={[
          "max-w-[75%]",
          isUser
            ? "px-5 py-3.5 bg-blue-600 text-white rounded-2xl shadow-sm"
            : "", // assistant는 배경/테두리 없이
        ].join(" ")}
      >
        {isUser ? (
          // 사용자 메시지는 단순 텍스트
          <div className="text-[15px] leading-relaxed whitespace-pre-wrap">{content}</div>
        ) : (
          // AI 응답은 GPT 스타일 마크다운 렌더링
          <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-gray-900 prose-p:text-gray-800 prose-p:leading-7 prose-li:text-gray-800 prose-li:leading-7 prose-strong:text-gray-900 prose-strong:font-semibold prose-code:text-pink-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw, rehypeHighlight]}
              components={{
                // 제목 스타일
                h1: ({ children }) => (
                  <h1 className="text-2xl font-bold mt-6 mb-4 text-gray-900">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-xl font-semibold mt-5 mb-3 text-gray-900">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-lg font-semibold mt-4 mb-2 text-gray-900">{children}</h3>
                ),
                // 단락 스타일
                p: ({ children }) => (
                  <p className="mb-4 text-gray-800 leading-7">{children}</p>
                ),
                // 리스트 스타일
                ul: ({ children }) => (
                  <ul className="list-disc list-outside ml-6 mb-4 space-y-2">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-outside ml-6 mb-4 space-y-2">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="text-gray-800 leading-7">{children}</li>
                ),
                // 강조 스타일
                strong: ({ children }) => (
                  <strong className="font-semibold text-gray-900">{children}</strong>
                ),
                em: ({ children }) => (
                  <em className="italic text-gray-700">{children}</em>
                ),
                // 코드 블록 스타일
                code: ({ node, children, ...props }) => {
                  const isInline = !node || node.position?.start.line === node.position?.end.line;
                  return isInline ? (
                    <code className="bg-gray-100 text-pink-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4">
                    {children}
                  </pre>
                ),
                // 인용구 스타일
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 my-4">
                    {children}
                  </blockquote>
                ),
                // 링크 스타일
                a: ({ href, children }) => (
                  <a
                    href={href}
                    className="text-blue-600 hover:text-blue-800 underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {children}
                  </a>
                ),
                // 테이블 스타일
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-gray-50">{children}</thead>
                ),
                tbody: ({ children }) => (
                  <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>
                ),
                tr: ({ children }) => <tr>{children}</tr>,
                th: ({ children }) => (
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-4 py-2 text-sm text-gray-800">{children}</td>
                ),
                // 수평선 스타일
                hr: () => <hr className="my-6 border-gray-200" />,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}

        {/* 백테스트 조건이 있으면 버튼 표시 */}
        {!isUser && hasConditions && (
          <button
            onClick={handleBacktest}
            className="mt-3 w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            설정하기
          </button>
        )}
      </div>
    </div>
  );
}
