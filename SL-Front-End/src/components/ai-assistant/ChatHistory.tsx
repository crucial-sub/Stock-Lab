/**
 * 채팅 히스토리 렌더링 컴포넌트
 *
 * Phase 1.2: ChatHistory 컴포넌트 구현 (스크롤은 부모에서 관리)
 *
 * 기능:
 * - messages 배열을 받아서 순차 렌더링
 * - 각 메시지는 MessageRenderer로 위임
 * - 스크롤 관리는 부모 컴포넌트(AIAssistantPageClient)에서 처리
 *
 * 중요 제약사항:
 * 1. UI 교체 금지: 메시지는 추가만 되고 교체되지 않음
 * 2. 성능 고려: 메시지가 많아지면 나중에 가상 스크롤 적용 예정
 */

"use client";

import type { Message } from "@/types/message";
import { MessageRenderer } from "./MessageRenderer";
import { AITypingIndicator } from "./AITypingIndicator";

interface ChatHistoryProps {
  messages: Message[];
  /** AI 응답 대기 중 여부 (타이핑 인디케이터 표시) */
  isWaitingForAI?: boolean;
  /** 백테스트 시작 콜백 */
  onBacktestStart?: (
    strategyName: string,
    config: {
      investmentAmount: number;
      startDate: string;
      endDate: string;
    }
  ) => void;
}

/**
 * 채팅 히스토리를 렌더링하는 컴포넌트
 * (스크롤은 부모 컴포넌트에서 관리)
 */
export function ChatHistory({ messages, isWaitingForAI = false, onBacktestStart }: ChatHistoryProps) {
  return (
    <div className="py-6 space-y-6">
      {messages.map((message) => (
        <MessageRenderer
          key={message.id}
          message={message}
          onBacktestStart={onBacktestStart}
        />
      ))}

      {/* AI 응답 대기 중일 때 타이핑 인디케이터 표시 */}
      {isWaitingForAI && <AITypingIndicator />}
    </div>
  );
}
