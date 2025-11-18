/**
 * 텍스트 메시지 렌더러
 *
 * 일반 텍스트 메시지를 렌더링
 */

"use client";

import type { TextMessage } from "@/types/message";

interface TextRendererProps {
  message: TextMessage;
}

/**
 * 텍스트 메시지를 렌더링하는 컴포넌트
 */
export function TextRenderer({ message }: TextRendererProps) {
  const isUser = message.role === "user";

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
        <div className="text-[15px] leading-relaxed whitespace-pre-line">
          {message.content}
        </div>
      </div>
    </div>
  );
}
