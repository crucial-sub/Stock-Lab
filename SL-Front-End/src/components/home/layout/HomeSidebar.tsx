"use client";

import Image from "next/image";
import { useState } from "react";
import { NavItem } from "../ui";

/**
 * 홈 화면 사이드바
 *
 * @description 홈 화면의 좌측 사이드바 네비게이션입니다.
 * 메인 메뉴와 하단 유틸리티 메뉴를 포함합니다.
 *
 * @example
 * ```tsx
 * <HomeSidebar
 *   currentPath="/home"
 *   onNavigate={(path) => router.push(path)}
 * />
 * ```
 */

interface HomeSidebarProps {
  /** 현재 활성화된 경로 */
  currentPath?: string;
  /** 네비게이션 클릭 시 호출되는 콜백 함수 */
  onNavigate?: (path: string) => void;
}

// 메인 네비게이션 메뉴 데이터
const MAIN_NAV_ITEMS = [
  {
    icon: "/icons/home.svg",
    label: "홈",
    path: "/home",
  },
  {
    icon: "/icons/neurology.svg",
    label: "AI 어시스턴트",
    path: "/ai-assistant",
  },
  {
    icon: "/icons/portfolio.svg",
    label: "전략 포트폴리오",
    path: "/quant",
  },
  {
    icon: "/icons/finance.svg",
    label: "시세",
    path: "/market-price",
  },
  {
    icon: "/icons/news.svg",
    label: "뉴스",
    path: "/news",
  },
  {
    icon: "/icons/community.svg",
    label: "커뮤니티",
    path: "/community",
  },
];

// 하단 유틸리티 메뉴 데이터
const UTILITY_NAV_ITEMS = [
  {
    icon: "/icons/help.svg",
    label: "이용 가이드",
    path: "/guide",
  },
  {
    icon: "/icons/account-circle.svg",
    label: "프로필 보기",
    path: "/profile",
  },
];

export function HomeSidebar({
  currentPath = "/home",
  onNavigate,
}: HomeSidebarProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-[260px] bg-sidebar overflow-hidden"
      aria-label="메인 네비게이션"
    >
      {/* 햄버거 메뉴 버튼 */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="absolute right-[28px] top-[42px] w-6 h-6"
        aria-label={isOpen ? "메뉴 닫기" : "메뉴 열기"}
        aria-expanded={isOpen}
      >
        <div className="relative w-full h-full">
          <Image
            src="/icons/hamburger.svg"
            alt=""
            fill
            className="object-contain"
            aria-hidden="true"
          />
        </div>
      </button>

      {/* 메인 네비게이션 */}
      <nav className="absolute left-[28px] top-[200px]" aria-label="메인 메뉴">
        <ul className="flex flex-col gap-[20px]">
          {MAIN_NAV_ITEMS.map((item) => (
            <li key={item.path}>
              <NavItem
                icon={item.icon}
                label={item.label}
                isActive={currentPath === item.path}
                onClick={() => onNavigate?.(item.path)}
              />
            </li>
          ))}
        </ul>
      </nav>

      {/* 하단 유틸리티 네비게이션 */}
      <nav
        className="absolute left-[28px] bottom-[96px]"
        aria-label="유틸리티 메뉴"
      >
        <ul className="flex flex-col gap-[20px]">
          {/* 구분선 */}
          <li>
            <hr className="w-[204px] border-t border-sidebar mb-[20px]" />
          </li>

          {UTILITY_NAV_ITEMS.map((item) => (
            <li key={item.path}>
              <NavItem
                icon={item.icon}
                label={item.label}
                isActive={currentPath === item.path}
                onClick={() => onNavigate?.(item.path)}
              />
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
