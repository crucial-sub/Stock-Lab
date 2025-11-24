"use client";

import { useCallback, useRef, useEffect } from "react";
import { AISearchInput } from "@/components/home/ui";
import { sendChatMessage } from "@/lib/api/chatbot";
import { useAIHelperStore } from "@/stores/aiHelperStore";

interface Message {
  role: "user" | "assistant";
  content: string;
  backtestConditionsBuy?: any[];
  backtestConditionsSell?: any[];
  appliedBuy?: boolean;
  appliedSell?: boolean;
  backtestConfig?: any;
}

interface BuyConditionUI {
  id: string;
  factorName: string | null;
  subFactorName: string | null;
  operator: string;
  value: string;
  argument?: string;
}

interface SellConditionUI {
  id: string;
  factorName: string | null;
  subFactorName: string | null;
  operator: string;
  value: string;
  argument?: string;
}

interface AIHelperSidebarProps {
  onBuyConditionsAdd?: (conditions: any[]) => void;
  onSellConditionsAdd?: (conditions: any[]) => void;
  onBacktestConfigApply?: (config: any) => void;
  onResetConditions?: () => void;
  currentBuyConditions?: BuyConditionUI[];
  currentSellConditions?: SellConditionUI[];
  onConditionsApplied?: () => void;
}

/**
 * AI 헬퍼 전용 메시지 컴포넌트
 */
function AIHelperMessage({
  message,
  onBuyConditionsAdd,
  onSellConditionsAdd,
  onBuyApplied,
  onSellApplied,
  onConditionsApplied,
  onBacktestConfigApply,
  onResetConditions,
}: {
  message: Message;
  onBuyConditionsAdd?: (conditions: any[]) => void;
  onSellConditionsAdd?: (conditions: any[]) => void;
  onBuyApplied?: () => void;
  onSellApplied?: () => void;
  onConditionsApplied?: () => void;
  onBacktestConfigApply?: (config: any) => void;
  onResetConditions?: () => void;
}) {
  const isUser = message.role === "user";
  const configAppliedRef = useRef(false);
  const resetAppliedRef = useRef(false);

  const applyBacktestConfigOnce = () => {
    if (configAppliedRef.current) return;
    if (message.backtestConfig && onBacktestConfigApply) {
      onBacktestConfigApply(message.backtestConfig);
      configAppliedRef.current = true;
    }
  };

  const resetConditionsOnce = () => {
    if (resetAppliedRef.current) return;
    if (onResetConditions) {
      onResetConditions();
      resetAppliedRef.current = true;
    }
  };

  const handleAddBuyConditions = () => {
    if (message.backtestConditionsBuy && message.backtestConditionsBuy.length > 0 && onBuyConditionsAdd) {
      resetConditionsOnce();
      const normalized = message.backtestConditionsBuy.map((cond) => ({
        ...cond,
        subFactorName: cond?.subFactorName || "기본값",
      }));
      onBuyConditionsAdd(normalized);
      applyBacktestConfigOnce();
      onBuyApplied?.();
      onConditionsApplied?.();
    }
  };

  const handleAddSellConditions = () => {
    if (message.backtestConditionsSell && message.backtestConditionsSell.length > 0 && onSellConditionsAdd) {
      resetConditionsOnce();
      const normalized = message.backtestConditionsSell.map((cond) => ({
        ...cond,
        subFactorName: cond?.subFactorName || "기본값",
      }));
      onSellConditionsAdd(normalized);
      applyBacktestConfigOnce();
      onSellApplied?.();
      onConditionsApplied?.();
    }
  };

  const handleApplyBoth = () => {
    resetConditionsOnce();
    applyBacktestConfigOnce();
    handleAddBuyConditions();
    handleAddSellConditions();
  };

  // 간단한 마크다운 변환 함수
  const formatContent = (content: string) => {
    return content
      .split('\n')
      .map((line, index) => {
        // ### 제목
        if (line.startsWith('### ')) {
          return <h3 key={index} className="font-semibold text-base mt-3 mb-1">{line.replace('### ', '')}</h3>;
        }
        // ## 제목
        if (line.startsWith('## ')) {
          return <h2 key={index} className="font-bold text-lg mt-4 mb-2">{line.replace('## ', '')}</h2>;
        }
        // - 리스트
        if (line.startsWith('- ')) {
          return <li key={index} className="ml-4">{line.replace('- ', '')}</li>;
        }
        // 일반 텍스트
        return <p key={index} className="leading-relaxed">{line || '\u00A0'}</p>;
      });
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6 w-full`}>
      <div
        className={[
          "max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm overflow-visible",
          isUser
            ? "bg-blue-600 text-white"
            : "bg-white text-gray-900 border border-gray-200",
        ].join(" ")}
      >
        <div className="text-[15px] whitespace-pre-line break-words">
          {formatContent(message.content)}
        </div>

        {/* 조건 추가 버튼 - 매수/매도 분리 */}
        {!isUser ? (
          (() => {
            const hasBuy = Array.isArray(message.backtestConditionsBuy) && message.backtestConditionsBuy.length > 0;
            const hasSell = Array.isArray(message.backtestConditionsSell) && message.backtestConditionsSell.length > 0;
            if (!hasBuy && !hasSell) return null;
            const bothApplied = message.appliedBuy && message.appliedSell;
            return (
              <div className="mt-3 flex gap-2">
                {hasBuy && (
                  <button
                    onClick={handleAddBuyConditions}
                    disabled={message.appliedBuy}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      message.appliedBuy
                        ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                        : "bg-red-500 hover:bg-red-600 text-white"
                    }`}
                  >
                    {message.appliedBuy ? "매수 적용됨" : "매수 조건에 추가"}
                  </button>
                )}
                {hasSell && (
                  <button
                    onClick={handleAddSellConditions}
                    disabled={message.appliedSell}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      message.appliedSell
                        ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                        : "bg-blue-500 hover:bg-blue-600 text-white"
                    }`}
                  >
                    {message.appliedSell ? "매도 적용됨" : "매도 조건에 추가"}
                  </button>
                )}
                {hasBuy && hasSell && (
                  <button
                    onClick={handleApplyBoth}
                    disabled={bothApplied}
                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                      bothApplied
                        ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                        : "bg-green-600 hover:bg-green-700 text-white"
                    }`}
                  >
                    {bothApplied ? "매수·매도 적용됨" : "매수·매도 한번에 적용"}
                  </button>
                )}
              </div>
            );
          })()
        ) : null}
      </div>
    </div>
  );
}

/**
 * Quant 페이지의 AI 헬퍼 사이드바
 * DSL 생성 전용 모드로 동작
 */
export function AIHelperSidebar({
  onBuyConditionsAdd,
  onSellConditionsAdd,
  onBacktestConfigApply,
  onResetConditions,
  currentBuyConditions = [],
  currentSellConditions = [],
  onConditionsApplied,
}: AIHelperSidebarProps) {
  const messages = useAIHelperStore((s) => s.messages);
  const addMessage = useAIHelperStore((s) => s.addMessage);
  const updateMessage = useAIHelperStore((s) => s.updateMessage);
  const sessionId = useAIHelperStore((s) => s.sessionId);
  const setSessionId = useAIHelperStore((s) => s.setSessionId);
  const isLoading = useAIHelperStore((s) => s.isLoading);
  const setIsLoading = useAIHelperStore((s) => s.setIsLoading);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // 메시지 추가 시 자동 스크롤
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleAISubmit = useCallback(
    async (value: string) => {
      if (isLoading) return;

      // 사용자 메시지 추가
      addMessage({ role: "user", content: value });
      setIsLoading(true);

      try {
        // 현재 조건들을 문자열로 변환하여 컨텍스트로 추가
        let contextMessage = value;

        // 검증 관련 키워드가 있으면 현재 조건 정보 추가
        const isVerificationRequest = /맞아|맞나|맞는지|확인|검증|체크/.test(value);

        if (isVerificationRequest && (currentBuyConditions.length > 0 || currentSellConditions.length > 0)) {
          contextMessage += "\n\n[현재 설정된 조건]";

          if (currentBuyConditions.length > 0) {
            contextMessage += "\n매수 조건:";
            currentBuyConditions.forEach((cond) => {
              if (cond.factorName) {
                let condStr = `\n- ${cond.factorName}`;
                if (cond.argument) {
                  condStr += `(${cond.argument})`;
                }
                condStr += ` ${cond.operator} ${cond.value}`;
                contextMessage += condStr;
              }
            });
          }

          if (currentSellConditions.length > 0) {
            contextMessage += "\n매도 조건:";
            currentSellConditions.forEach((cond) => {
              if (cond.factorName) {
                let condStr = `\n- ${cond.factorName}`;
                if (cond.argument) {
                  condStr += `(${cond.argument})`;
                }
                condStr += ` ${cond.operator} ${cond.value}`;
                contextMessage += condStr;
              }
            });
          }
        }

        const response = await sendChatMessage({
          message: contextMessage,
          session_id: sessionId || undefined,
          client_type: "ai_helper",
        });

        setSessionId(response.session_id);

        // AI 응답 메시지 추가
        const backtestConditions: any = response.backtest_conditions || {};
        const buyConditions = Array.isArray(backtestConditions)
          ? backtestConditions
          : Array.isArray(backtestConditions.buy)
            ? backtestConditions.buy
            : [];
        const sellConditions = Array.isArray(backtestConditions.sell)
          ? backtestConditions.sell
          : [];

        addMessage({
          role: "assistant",
          content: response.answer,
          backtestConditionsBuy: buyConditions,
          backtestConditionsSell: sellConditions,
          appliedBuy: false,
          appliedSell: false,
          backtestConfig: response.backtest_config,
        });

      } catch (error) {
        console.error("Failed to send message:", error);
        addMessage({
          role: "assistant",
          content: "메시지 전송에 실패했습니다. 다시 시도해주세요.",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, currentBuyConditions, currentSellConditions, addMessage, setSessionId, setIsLoading]
  );

  return (
    <div className="h-full flex flex-col px-4 py-6 overflow-hidden">
      {/* 안내 메시지 */}
      <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <p className="text-sm text-blue-900 font-medium">AI 전략 헬퍼</p>
        <p className="text-xs text-blue-700 mt-1">
          자연어로 매수/매도 조건을 설명하면 백테스트 조건을 생성해드립니다.
        </p>
        <p className="text-xs text-blue-600 mt-2">
          예시: "PER 10 이하이고 ROE 15% 이상인 종목을 매수"
        </p>
      </div>

      {/* 채팅 히스토리 */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto mb-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            조건을 입력해주세요
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((message, index) => (
              <AIHelperMessage
                key={index}
                message={message}
                onBuyConditionsAdd={onBuyConditionsAdd}
                onSellConditionsAdd={onSellConditionsAdd}
                onBacktestConfigApply={onBacktestConfigApply}
                onConditionsApplied={onConditionsApplied}
                onBuyApplied={() => updateMessage(index, { appliedBuy: true })}
                onSellApplied={() => updateMessage(index, { appliedSell: true })}
              />
            ))}
          </div>
        )}
      </div>

      {/* 입력창 */}
      <div className="border-t pt-4">
        {isLoading ? (
          <div className="text-center text-gray-500 py-4">
            AI가 응답 중입니다...
          </div>
        ) : (
          <AISearchInput
            placeholder="매수/매도 조건을 입력하세요..."
            onSubmit={handleAISubmit}
          />
        )}
      </div>
    </div>
  );
}
