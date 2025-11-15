"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

/**
 * 전역 사이드바 네비게이션
 *
 * @description 모든 페이지에서 표시되는 사이드바입니다.
 * 햄버거 메뉴를 클릭하여 접기/펼치기가 가능합니다.
 *
 * @features
 * - 펼쳤을 때: 260px (아이콘 + 텍스트)
 * - 접혔을 때: 108px (아이콘만)
 * - 부드러운 transition 애니메이션
 * - 현재 경로에 따른 활성 상태 표시
 */

// 메인 네비게이션 아이템
const MAIN_NAV_ITEMS = [
  {
    icon: "/icons/home.svg",
    label: "홈",
    path: "/",
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

// 하단 유틸리티 아이템 (로그인 상태에 관계없이 공통)
const COMMON_UTILITY_NAV_ITEMS = [
  {
    icon: "/icons/help.svg",
    label: "이용 가이드",
    path: "/guide",
  },
];

// 로그인된 사용자용 아이템
const LOGGED_IN_UTILITY_NAV_ITEMS = [
  {
    icon: "/icons/account-circle.svg",
    label: "프로필 보기",
    path: "/profile",
  },
];

// 로그인 안 된 사용자용 아이템
const LOGGED_OUT_UTILITY_NAV_ITEMS = [
  {
    icon: "/icons/account-circle.svg",
    label: "로그인 하기",
    path: "/login",
  },
];

interface SideNavProps {
  /** 로그인 여부 (서버에서 전달) */
  isLoggedIn: boolean;
}

export function SideNav({ isLoggedIn }: SideNavProps) {
  const [isOpen, setIsOpen] = useState(true);
  const pathname = usePathname();

  // 로그인 상태에 따라 유틸리티 아이템 결정
  const utilityNavItems = [
    ...COMMON_UTILITY_NAV_ITEMS,
    ...(isLoggedIn ? LOGGED_IN_UTILITY_NAV_ITEMS : LOGGED_OUT_UTILITY_NAV_ITEMS),
  ];

  // 현재 경로가 활성 경로인지 확인
  const isActive = (itemPath: string) => {
    if (itemPath === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(itemPath);
  };

  return (
    <aside
      className={[
        "relative h-full bg-sidebar shrink-0 overflow-hidden",
        "transition-all duration-300 ease-in-out",
        isOpen ? "w-[260px]" : "w-[108px]",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="메인 네비게이션"
    >
      {/* 햄버거 메뉴 버튼 */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={[
          "absolute w-6 h-6 top-[42px]",
          "transition-all duration-300",
          isOpen ? "right-[28px]" : "left-[42px]",
        ]
          .filter(Boolean)
          .join(" ")}
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
      <nav
        className={[
          "absolute top-[200px]",
          "transition-all duration-300",
          isOpen ? "left-[28px]" : "left-[28px]",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="메인 메뉴"
      >
        <ul className="flex flex-col gap-[20px]">
          {MAIN_NAV_ITEMS.map((item) => {
            const active = isActive(item.path);
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={[
                    "flex items-center rounded-lg overflow-hidden",
                    "transition-all duration-300 ease-in-out",
                    isOpen
                      ? "gap-3 px-4 py-3 w-[204px] h-14"
                      : "gap-0 px-0 py-0 w-[52px] h-14 justify-center",
                    active
                      ? "bg-sidebar-item-active text-sidebar-item-active border border-sidebar-item-active"
                      : "text-sidebar-item hover:bg-sidebar-item-sub-active",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-current={active ? "page" : undefined}
                >
                  <div className="relative w-5 h-5 shrink-0">
                    <Image
                      src={item.icon}
                      alt=""
                      fill
                      className="object-contain"
                      aria-hidden="true"
                    />
                  </div>
                  <span
                    className={[
                      "text-xl font-semibold whitespace-nowrap",
                      "transition-all duration-300 ease-in-out",
                      isOpen
                        ? "opacity-100 w-auto"
                        : "opacity-0 w-0 overflow-hidden",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 하단 유틸리티 네비게이션 */}
      <nav
        className={[
          "absolute bottom-[96px]",
          "transition-all duration-300",
          isOpen ? "left-[28px]" : "left-[28px]",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="유틸리티 메뉴"
      >
        <ul className="flex flex-col gap-[20px]">
          {/* 구분선 */}
          <li>
            <hr
              className={[
                "border-t border-sidebar mb-[20px]",
                "transition-all duration-300",
                isOpen ? "w-[204px]" : "w-[52px]",
              ]
                .filter(Boolean)
                .join(" ")}
            />
          </li>

          {utilityNavItems.map((item) => {
            const active = isActive(item.path);
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={[
                    "flex items-center rounded-lg overflow-hidden",
                    "transition-all duration-300 ease-in-out",
                    isOpen
                      ? "gap-3 px-4 py-3 w-[204px] h-14"
                      : "gap-0 px-0 py-0 w-[52px] h-14 justify-center",
                    active
                      ? "bg-sidebar-item-active text-sidebar-item-active border border-sidebar-item-active"
                      : "text-sidebar-item hover:bg-sidebar-item-sub-active",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-current={active ? "page" : undefined}
                >
                  <div className="relative w-5 h-5 shrink-0">
                    <Image
                      src={item.icon}
                      alt=""
                      fill
                      className="object-contain"
                      aria-hidden="true"
                    />
                  </div>
                  <span
                    className={[
                      "text-xl font-semibold whitespace-nowrap",
                      "transition-all duration-300 ease-in-out",
                      isOpen
                        ? "opacity-100 w-auto"
                        : "opacity-0 w-0 overflow-hidden",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
