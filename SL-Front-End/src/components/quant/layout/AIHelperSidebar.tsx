"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { AISearchInput } from "@/components/home/ui";
import { sendChatMessage } from "@/lib/api/chatbot";

interface Message {
  role: "user" | "assistant";
  content: string;
  backtestConditions?: any[];
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
  currentBuyConditions?: BuyConditionUI[];
  currentSellConditions?: SellConditionUI[];
}

// 간단한 의도 감지: 매수/매도/전략 키워드 파악
const detectTradeIntent = (text: string) => {
  const lowered = text.toLowerCase();
  const hasBuy =
    /매수|사고싶어|사고 싶어|매입|buy/.test(lowered);
  const hasSell =
    /매도|팔고싶어|팔고 싶어|청산|sell/.test(lowered);
  const hasStrategy = /전략/.test(lowered);
  return { hasBuy, hasSell, hasStrategy };
};

/**
 * AI 헬퍼 전용 메시지 컴포넌트
 */
function AIHelperMessage({
  message,
  onBuyConditionsAdd,
  onSellConditionsAdd,
}: {
  message: Message;
  onBuyConditionsAdd?: (conditions: any[]) => void;
  onSellConditionsAdd?: (conditions: any[]) => void;
}) {
  const isUser = message.role === "user";

  const handleAddBuyConditions = () => {
    if (message.backtestConditions && onBuyConditionsAdd) {
      onBuyConditionsAdd(message.backtestConditions);
    }
  };

  const handleAddSellConditions = () => {
    if (message.backtestConditions && onSellConditionsAdd) {
      onSellConditionsAdd(message.backtestConditions);
    }
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
        {!isUser && message.backtestConditions && message.backtestConditions.length > 0 && (
          <div className="mt-3 flex gap-2">
            <button
              onClick={handleAddBuyConditions}
              className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
            >
              매수 조건에 추가
            </button>
            <button
              onClick={handleAddSellConditions}
              className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors"
            >
              매도 조건에 추가
            </button>
          </div>
        )}
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
  currentBuyConditions = [],
  currentSellConditions = []
}: AIHelperSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
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
      setMessages((prev) => [...prev, { role: "user", content: value }]);
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
        });

        setSessionId(response.session_id);

        // AI 응답 메시지 추가
        const { hasBuy, hasSell, hasStrategy } = detectTradeIntent(value);
        const dslConditions = response.backtest_conditions || [];

        // 전략/매수/매도 키워드를 기반으로 자동 추가
        if (dslConditions.length > 0) {
          const shouldAddToBuy = hasBuy || !hasSell || hasStrategy;
          if (shouldAddToBuy) {
            onBuyConditionsAdd?.(dslConditions);
          }
          if (hasSell) {
            onSellConditionsAdd?.(dslConditions);
          }
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.answer,
            backtestConditions: response.backtest_conditions,
          },
        ]);
      } catch (error) {
        console.error("Failed to send message:", error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "메시지 전송에 실패했습니다. 다시 시도해주세요.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, currentBuyConditions, currentSellConditions, onBuyConditionsAdd, onSellConditionsAdd]
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
