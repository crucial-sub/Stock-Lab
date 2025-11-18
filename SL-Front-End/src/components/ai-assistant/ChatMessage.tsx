"use client";

import { useRouter } from "next/navigation";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  backtestConditions?: any; // array 또는 { buy, sell }
}

/**
 * 채팅 메시지 컴포넌트
 */
export function ChatMessage({ role, content, backtestConditions }: ChatMessageProps) {
  const isUser = role === "user";
  const router = useRouter();

  // 간단한 마크다운 렌더링 (제목/리스트 위주)
  const renderContent = (text: string) =>
    text.split("\n").map((line, index) => {
      // inline bold(**text**) 처리
      const renderInline = (input: string) => {
        const parts = input.split(/(\*\*[^*]+\*\*)/g);
        return parts.map((part, idx) => {
          if (part.startsWith("**") && part.endsWith("**")) {
            return (
              <strong key={idx}>{part.replace(/\*\*/g, "")}</strong>
            );
          }
          return <span key={idx}>{part}</span>;
        });
      };

      if (line.startsWith("### ")) {
        return (
          <h3 key={index} className="font-semibold text-base mt-3 mb-1">
            {renderInline(line.replace("### ", ""))}
          </h3>
        );
      }
      if (line.startsWith("## ")) {
        return (
          <h2 key={index} className="font-bold text-lg mt-4 mb-2">
            {renderInline(line.replace("## ", ""))}
          </h2>
        );
      }
      if (line.startsWith("📌")) {
        return (
          <h3 key={index} className="font-semibold text-base mt-3 mb-1">
            {renderInline(line.replace("📌", "").trim())}
          </h3>
        );
      }
      if (line.startsWith("- ") || line.startsWith("• ")) {
        return (
          <li key={index} className="ml-4 list-disc">
            {renderInline(line.replace(/^[-•]\s?/, ""))}
          </li>
        );
      }
      if (line.trim() === "") {
        return <br key={index} />;
      }
      return (
        <p key={index} className="leading-relaxed whitespace-pre-line">
          {renderInline(line)}
        </p>
      );
    });

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
          "max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white text-gray-900 border border-gray-200",
        ].join(" ")}
      >
        <div className="text-[15px] leading-relaxed">{renderContent(content)}</div>

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
