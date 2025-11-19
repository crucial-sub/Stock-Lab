/**
 * 마크다운 메시지 렌더러
 *
 * react-markdown을 사용하여 마크다운 형식의 메시지를 GPT 스타일로 렌더링
 * - 코드 하이라이팅, 테이블, GFM 지원
 * - GPT 스타일: AI 응답은 배경/테두리 없이 마크다운만 렌더링
 * - 공통 마크다운 컴포넌트 사용 (중복 제거)
 */

"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import { normalizeMarkdown } from "@/lib/markdown-utils";
import { markdownComponents, markdownProseClasses } from "./shared/MarkdownComponents";

import type { MarkdownMessage } from "@/types/message";

interface MarkdownRendererProps {
  message: MarkdownMessage;
}

/**
 * 마크다운 메시지를 GPT 스타일로 렌더링하는 컴포넌트
 */
export function MarkdownRenderer({ message }: MarkdownRendererProps) {
  const isUser = message.role === "user";

  // 마크다운 정규화: 헤딩과 리스트 앞뒤에 줄바꿈 추가
  const normalizedContent = normalizeMarkdown(message.content);

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
            {message.content}
          </div>
        ) : (
          // AI 응답: GPT 스타일 마크다운 렌더링 (공통 컴포넌트 사용)
          <div className={markdownProseClasses}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight, rehypeRaw]}
              components={markdownComponents}
            >
              {normalizedContent}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
