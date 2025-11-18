"use client";

import { useRouter } from "next/navigation";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  backtestConditions?: any[];
}

/**
 * 채팅 메시지 컴포넌트
 */
export function ChatMessage({ role, content, backtestConditions }: ChatMessageProps) {
  const isUser = role === "user";
  const router = useRouter();

  const handleBacktest = () => {
    if (!backtestConditions) return;

    const queryParams = new URLSearchParams({
      conditions: JSON.stringify(backtestConditions),
    });
    // 백테스트 신규 페이지로 이동하며 조건을 전달
    router.push(`/quant/new?${queryParams.toString()}`);
  };

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
        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{content}</p>

        {/* 백테스트 조건이 있으면 버튼 표시 */}
        {!isUser && backtestConditions && backtestConditions.length > 0 && (
          <button
            onClick={handleBacktest}
            className="mt-3 w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
          >
            백테스트하기
          </button>
        )}
      </div>
    </div>
  );
}
