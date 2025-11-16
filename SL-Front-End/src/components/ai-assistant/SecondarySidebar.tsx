"use client";

import Image from "next/image";
import { useState } from "react";

/**
 * AI 어시스턴트 2차 사이드바
 *
 * @description 채팅 내역 목록을 표시하는 사이드바입니다.
 * 오른쪽 상단의 화살표 아이콘으로 열고 닫을 수 있습니다.
 *
 * @features
 * - 펼쳤을 때: 240px
 * - 접혔을 때: 0px (완전히 숨김)
 * - 1차 사이드바와 독립적으로 동작
 */

interface ChatHistory {
  id: string;
  title: string;
}

interface SecondarySidebarProps {
  /** 초기 열림/닫힘 상태 */
  defaultOpen?: boolean;
  /** 채팅 내역 목록 */
  chatHistory?: ChatHistory[];
  /** 채팅 내역 클릭 핸들러 */
  onChatClick?: (chatId: string) => void;
}

const DEFAULT_CHAT_HISTORY: ChatHistory[] = [
  { id: "1", title: "워렌 버핏의 전략" },
  { id: "2", title: "주식 투자에 대해" },
  { id: "3", title: "주식 투자에 대해" },
  { id: "4", title: "Title 1" },
  { id: "5", title: "Title 2" },
  { id: "6", title: "Title 3" },
];

export function SecondarySidebar({
  defaultOpen = true,
  chatHistory = DEFAULT_CHAT_HISTORY,
  onChatClick,
}: SecondarySidebarProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <aside
      className={[
        "relative h-full bg-sidebar shrink-0",
        "border-r border-sidebar",
        "transition-all duration-300 ease-in-out",
        isOpen ? "w-[240px]" : "w-[62px]", // 닫혔을 때 화살표 버튼 + 여백 공간
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="채팅 내역"
    >
      {/* 토글 버튼 (열려있을 때: 왼쪽 화살표, 닫혔을 때: 오른쪽 화살표) */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={[
          "absolute top-[42px] w-6 h-6 z-10",
          "transition-all duration-300 ease-in-out",
          isOpen ? "right-[28px]" : "left-[18px]",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={isOpen ? "채팅 내역 닫기" : "채팅 내역 열기"}
      >
        <div className="relative w-full h-full">
          <Image
            src={isOpen ? "/icons/arrow_left.svg" : "/icons/arrow_right.svg"}
            alt=""
            fill
            className="object-contain transition-opacity duration-300"
            aria-hidden="true"
          />
        </div>
      </button>

      {/* 채팅 내역 목록 */}
      <nav
        className={[
          "absolute left-[18px] top-[110px] w-[204px]",
          "transition-opacity duration-300",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <ul className="flex flex-col gap-1">
          {chatHistory.map((chat) => (
            <li key={chat.id}>
              <button
                type="button"
                onClick={() => onChatClick?.(chat.id)}
                className={[
                  "w-full h-[35px] px-3 py-2",
                  "text-left text-sidebar-item text-base font-normal",
                  "rounded-lg",
                  "hover:bg-sidebar-item-sub-active",
                  "transition-colors duration-200",
                ]
                  .filter(Boolean)
                  .join(" ")}
                disabled={!isOpen}
              >
                {chat.title}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
