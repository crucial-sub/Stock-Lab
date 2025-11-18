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
  /** 채팅 삭제 핸들러 */
  onChatDelete?: (chatId: string) => void;
  /** 전체 채팅 삭제 핸들러 */
  onDeleteAll?: () => void;
  /** 새 채팅 생성 핸들러 */
  onNewChat?: () => void;
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
  onChatDelete,
  onDeleteAll,
  onNewChat,
}: SecondarySidebarProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [hoveredChatId, setHoveredChatId] = useState<string | null>(null);

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

      {/* 채팅 내역 목록 - 독립 스크롤 추가 */}
      <nav
        className={[
          "absolute left-[18px] top-[110px] w-[204px]",
          "h-[calc(100vh-130px)]", // 화면 높이에서 상단 여백 제외
          "flex flex-col",
          "transition-opacity duration-300",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {/* 버튼 그룹 */}
        <div className="flex gap-2 mb-3 flex-shrink-0">
          {onNewChat && (
            <button
              type="button"
              onClick={onNewChat}
              className="flex-1 h-[38px] rounded-lg bg-brand text-white text-sm font-semibold hover:bg-brand-dark transition-colors"
            >
              새 채팅
            </button>
          )}
          {onDeleteAll && chatHistory.length > 0 && (
            <button
              type="button"
              onClick={onDeleteAll}
              className="w-[38px] h-[38px] rounded-lg bg-red-500 text-white text-sm font-semibold hover:bg-red-600 transition-colors flex items-center justify-center"
              title="전체 삭제"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-5 h-5"
              >
                <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>

        <ul className="flex flex-col gap-1 overflow-y-auto flex-1 pr-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
          {chatHistory.map((chat) => (
            <li
              key={chat.id}
              onMouseEnter={() => setHoveredChatId(chat.id)}
              onMouseLeave={() => setHoveredChatId(null)}
              className="relative group flex items-center gap-1"
            >
              <button
                type="button"
                onClick={() => onChatClick?.(chat.id)}
                className={[
                  "flex-1 h-[35px] px-3 py-2",
                  "text-left text-sidebar-item text-base font-normal",
                  "rounded-lg",
                  "hover:bg-sidebar-item-sub-active",
                  "transition-colors duration-200",
                  "truncate",
                ]
                  .filter(Boolean)
                  .join(" ")}
                disabled={!isOpen}
              >
                {chat.title}
              </button>
              {hoveredChatId === chat.id && onChatDelete && isOpen && (
                <button
                  type="button"
                  onClick={() => onChatDelete(chat.id)}
                  className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded hover:bg-red-500/20 transition-colors"
                  aria-label="채팅 삭제"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="w-4 h-4 text-red-500"
                  >
                    <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
                  </svg>
                </button>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
