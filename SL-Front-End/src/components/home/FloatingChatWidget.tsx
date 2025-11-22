"use client";

import { useEffect, useRef, useState, useMemo, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { sendChatMessage } from "@/lib/api/chatbot";
import { markdownComponents, markdownProseClasses } from "@/components/ai-assistant/renderers/shared/MarkdownComponents";
import { normalizeMarkdown } from "@/lib/markdown-utils";
import { useBacktestConfigStore } from "@/stores/backtestConfigStore";

type MessageRole = "assistant" | "user" | "system";

interface WidgetMessage {
  id: string;
  role: MessageRole;
  content: string;
  backtestConditions?: any;
}

const createMessageId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;

const WELCOME_MESSAGE: WidgetMessage = {
  id: "welcome",
  role: "assistant",
  content: "안녕하세요! 궁금한 점을 질문해 주세요.",
};

export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<WidgetMessage[]>([WELCOME_MESSAGE]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const {
    buyConditionsUI,
    sellConditionsUI,
    setBuyConditionsUI,
    setSellConditionsUI,
  } = useBacktestConfigStore();

  useEffect(() => {
    if (isOpen && endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const pushMessage = (message: WidgetMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  const handleError = () => {
    pushMessage({
      id: createMessageId(),
      role: "system",
      content: "답변을 가져오는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    });
  };

  const handleSend = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isSending) return;

    const userMessage: WidgetMessage = {
      id: createMessageId(),
      role: "user",
      content: trimmed,
    };

    pushMessage(userMessage);
    setInputValue("");
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        message: trimmed,
        session_id: sessionId ?? undefined,
        client_type: "home_widget",
      });
      setSessionId(response.session_id);

      pushMessage({
        id: createMessageId(),
        role: "assistant",
        content: response.answer,
        backtestConditions: response.backtest_conditions,
      });
    } catch (error) {
      console.error("FloatingChatWidget send error:", error);
      handleError();
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void handleSend();
  };

  return (
    <>
      <button
        type="button"
        onClick={handleToggle}
        className="fixed bottom-6 right-6 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg transition hover:scale-105 hover:shadow-xl focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        aria-label="AI 챗봇 열기"
      >
        <svg
          className="h-6 w-6"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.7}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5z" />
        </svg>
      </button>

      {isOpen ? (
        <div className="fixed bottom-24 right-6 z-30 w-[23rem] max-w-[92vw] rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <div className="flex items-center justify-between rounded-t-2xl bg-gradient-to-r from-blue-600 to-indigo-500 px-4 py-3 text-white">
            <div>
              <p className="text-sm font-semibold">AI 어시스턴트</p>
              <p className="text-xs text-white/80">주식·시장 질문을 바로 물어보세요</p>
            </div>
            <button
              type="button"
              onClick={handleToggle}
              className="rounded-full p-1 text-white/80 transition hover:bg-white/20"
              aria-label="챗봇 닫기"
            >
              ✕
            </button>
          </div>
          <div className="flex max-h-[520px] flex-col">
            <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3 text-sm text-gray-900">
              {messages.map((message) => {
                const isUser = message.role === "user";
                const isSystem = message.role === "system";

                const bc = message.backtestConditions;
                const buyConditions: any[] = [];
                const sellConditions: any[] = [];
                if (bc) {
                  if (Array.isArray(bc)) {
                    buyConditions.push(...bc);
                  } else {
                    if (Array.isArray(bc.buy)) buyConditions.push(...bc.buy);
                    if (Array.isArray(bc.sell)) sellConditions.push(...bc.sell);
                  }
                }

                const convertToUI = (conditions: any[], existingLength: number, prefix: string) =>
                  conditions.map((cond, idx) => {
                    const id = String.fromCharCode(65 + existingLength + idx);
                    const factorName = cond?.factor ?? null;
                    const operator = cond?.operator ?? "";
                    const value =
                      cond?.value !== undefined && cond?.value !== null ? String(cond.value) : "";
                    const argument =
                      Array.isArray(cond?.params) && cond.params.length
                        ? cond.params.join(",")
                        : undefined;
                    return {
                      id: `${prefix}${id}`,
                      factorName,

                      subFactorName: cond?.subFactorName || "기본값",
                      operator,
                      value,
                      argument,
                    };
                  });

                const handleApplyBuy = () => {
                  if (!buyConditions.length) return;
                  const mapped = convertToUI(buyConditions, buyConditionsUI.length, "B");
                  setBuyConditionsUI([...buyConditionsUI, ...mapped]);
                };

                const handleApplySell = () => {
                  if (!sellConditions.length) return;
                  const mapped = convertToUI(sellConditions, sellConditionsUI.length, "S");
                  setSellConditionsUI([...sellConditionsUI, ...mapped]);
                };

                const hasBuyConditions = buyConditions.length > 0;
                const hasSellConditions = sellConditions.length > 0;

                const renderContent = () => {
                  if (isUser || isSystem) {
                    return <div className="whitespace-pre-wrap">{message.content}</div>;
                  }
                  const markdown = normalizeMarkdown(message.content);
                  return (
                    <div className={markdownProseClasses}>
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={markdownComponents}
                      >
                        {markdown}
                      </ReactMarkdown>
                    </div>
                  );
                };

                return (
                  <div
                    key={message.id}
                    className={[
                      "flex",
                      isUser ? "justify-end" : "justify-start",
                    ].join(" ")}
                  >
                    <div
                      className={[
                        "rounded-2xl px-4 py-2 shadow-sm",
                        isUser
                          ? "bg-blue-600 text-white"
                          : isSystem
                            ? "bg-amber-50 text-amber-900 border border-amber-200"
                            : "bg-slate-100 text-slate-900",
                      ].join(" ")}
                    >
                      {renderContent()}
                      {!isUser && (hasBuyConditions || hasSellConditions) && (
                        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                          {hasBuyConditions && (
                            <button
                              onClick={handleApplyBuy}
                              className="w-full rounded-lg bg-purple-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-purple-700"
                            >
                              매수 조건에 추가
                            </button>
                          )}
                          {hasSellConditions && (
                            <button
                              onClick={handleApplySell}
                              className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700"
                            >
                              매도 조건에 추가
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
              <div ref={endRef} />
            </div>
            <form onSubmit={handleSubmit} className="border-t border-slate-200 p-3">
              <div className="flex gap-2">
                <textarea
                  className="h-16 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="예: 퀀트투자가 뭐야?"
                  value={inputValue}
                  onChange={(event) => setInputValue(event.target.value)}
                  disabled={isSending}
                />
                <button
                  type="submit"
                  disabled={isSending || !inputValue.trim()}
                  className="h-16 rounded-xl bg-blue-600 px-4 text-sm font-semibold text-white transition enabled:hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isSending ? "전송중" : "보내기"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
