"use client";

import { useState } from "react";
import { Icon } from '@/components/common/Icon';

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
        <div className="relative w-full h-full text-muted">
          <Icon
            src={isOpen ? "/icons/arrow_left.svg" : "/icons/arrow_right.svg"}
            alt=""
            className="transition-opacity duration-300"
            color="rgb(var(--color-gray-400))"
            size="100%"
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
        <div className="flex flex-col gap-2 mb-4 flex-shrink-0">
          {onNewChat && (
            <button
              type="button"
              onClick={onNewChat}
              className="w-full flex items-center gap-2 text-start pl-3 pt-2 pb-1.5 rounded-[12px] text-gray-400 text-[1rem] font-normal hover:text-white hover:font-semibold hover:bg-sidebar-item-sub-active transition-colors"
            >
              <span className="-mt-1 inline-flex">
                <Icon
                  src="/icons/add.svg"
                  alt=""
                  color="currentColor"
                  size={16}
                />
              </span>
              새 채팅 추가하기
            </button>

          )}
          {onDeleteAll && (
            <button
              type="button"
              onClick={onDeleteAll}
              className="w-full flex items-center gap-2 text-start pl-3 pt-2 pb-1.5 rounded-[12px] text-price-up/80 text-[1rem] font-normal hover:text-price-up hover:font-semibold hover:bg-[#FF646433] transition-colors"
            >
              <span className="-mt-1 inline-flex">
                <Icon
                  src="/icons/delete.svg"
                  alt=""
                  color="currentColor"
                  size={16}
                />
              </span>
              전체 채팅 삭제하기
            </button>
          )}
          {onDeleteAll && (
            <div className="h-px w-full bg-[#FFFFFF1D] rounded-full mt-2" />
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
                  "flex-1 pl-3 pt-2 pb-1.5",
                  "text-left text-sidebar-item text-base font-normal",
                  "rounded-[12px]",
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
                  className="flex-shrink-0 p-2 flex items-center justify-center rounded-[8px] hover:bg-[#FF646433] transition-colors"
                  aria-label="채팅 삭제"
                >
                  <Icon
                    src="/icons/delete.svg"
                    alt=""
                    color="rgb(var(--text-price-up))"
                    size={18}
                  />
                </button>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
