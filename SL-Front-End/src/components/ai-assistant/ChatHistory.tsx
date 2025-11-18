/**
 * 채팅 히스토리 렌더링 컴포넌트
 *
 * Phase 1.2: ChatHistory 컴포넌트 및 자동 스크롤 구현
 *
 * 기능:
 * - messages 배열을 받아서 순차 렌더링
 * - 새 메시지 추가 시 자동으로 최하단 스크롤
 * - 각 메시지는 MessageRenderer로 위임
 * - 스크롤 컨테이너 ref 관리
 *
 * 중요 제약사항:
 * 1. UI 교체 금지: 메시지는 추가만 되고 교체되지 않음
 * 2. 스크롤 보존: 유저가 스크롤 중일 때는 자동 스크롤 안 함
 * 3. 성능 고려: 메시지가 많아지면 나중에 가상 스크롤 적용 예정
 */

"use client";

import { useRef, useEffect, useState } from "react";
import type { Message } from "@/types/message";
import { MessageRenderer } from "./MessageRenderer";

interface ChatHistoryProps {
  messages: Message[];
}

/**
 * 채팅 히스토리를 렌더링하고 자동 스크롤을 관리하는 컴포넌트
 */
export function ChatHistory({ messages }: ChatHistoryProps) {
  // 스크롤 컨테이너 ref
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 마지막 메시지 추적용 ref
  const lastMessageRef = useRef<HTMLDivElement>(null);

  // 유저가 스크롤 중인지 추적
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  // 마지막 메시지 ID 추적 (새 메시지 감지용)
  const lastMessageIdRef = useRef<string | null>(null);

  /**
   * 자동 스크롤 함수
   * 새 메시지가 추가되고 유저가 스크롤 중이 아닐 때만 실행
   */
  function scrollToBottom(behavior: ScrollBehavior = "smooth") {
    if (!lastMessageRef.current) return;

    lastMessageRef.current.scrollIntoView({
      behavior,
      block: "end",
    });
  }

  /**
   * 유저 스크롤 감지 핸들러
   * 스크롤이 최하단에 있지 않으면 isUserScrolling = true
   */
  function handleScroll() {
    if (!scrollContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;

    // 최하단에서 50px 이내면 자동 스크롤 허용
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 50;

    setIsUserScrolling(!isNearBottom);
  }

  /**
   * 새 메시지 추가 시 자동 스크롤
   */
  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    // 새 메시지가 추가된 경우에만 스크롤
    if (lastMessage.id !== lastMessageIdRef.current) {
      lastMessageIdRef.current = lastMessage.id;

      // 유저가 스크롤 중이 아니면 자동 스크롤
      if (!isUserScrolling) {
        // 첫 메시지는 즉시 스크롤 (smooth 애니메이션 없이)
        const behavior = messages.length === 1 ? "instant" : "smooth";

        // 약간의 지연 후 스크롤 (DOM 업데이트 대기)
        setTimeout(() => {
          scrollToBottom(behavior as ScrollBehavior);
        }, 100);
      }
    }
  }, [messages, isUserScrolling]);

  /**
   * 초기 렌더링 시 스크롤 이벤트 리스너 등록
   */
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    container.addEventListener("scroll", handleScroll);

    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, []);

  /**
   * 메시지가 없을 때 빈 상태 표시
   */
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted text-sm">
          아직 메시지가 없습니다. AI에게 질문을 시작해보세요!
        </p>
      </div>
    );
  }

  return (
    <div
      ref={scrollContainerRef}
      className="h-full overflow-y-auto px-4 py-6"
    >
      <div className="w-full max-w-[1000px] mx-auto space-y-6">
        {messages.map((message) => (
          <MessageRenderer
            key={message.id}
            message={message}
          />
        ))}

        {/* 마지막 메시지 마커 (스크롤 타겟) */}
        <div ref={lastMessageRef} className="h-1" />
      </div>
    </div>
  );
}
