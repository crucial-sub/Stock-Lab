"use client";

import { Icon } from "@/components/common";
import { authApi } from "@/lib/api/auth";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

/**
 * 전역 사이드바 네비게이션 (반응형)
 *
 * @description 모든 페이지에서 표시되는 사이드바입니다.
 *
 * @features
 * - 모바일 (<640px): 오버레이 방식, 햄버거 메뉴로 토글
 * - 태블릿 (640-1024px): 축소 모드 기본 (68px), 확장 가능
 * - 데스크톱 (>1024px): 확장 모드 기본 (260px)
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
    path: "/mypage",
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
  serverHasToken: boolean;
}

const SIDEBAR_ICON_COLORS = {
  active: "#FFFFFF",
  inactive: "#C8C8C8",
};

export function SideNav({ serverHasToken }: SideNavProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(serverHasToken);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  // 화면 크기 변경 감지하여 모바일 메뉴 상태 초기화
  useEffect(() => {
    const handleResize = () => {
      // sm 브레이크포인트 (640px) 이상에서 모바일 메뉴 닫기
      if (window.innerWidth >= 640) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // 경로 변경 시 모바일 메뉴 닫기
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);
  // 랜딩 페이지에서는 사이드바를 숨김
  if (pathname === "/landing") {
    return null;
  }

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        await authApi.getCurrentUser();
        setIsLoggedIn(true);
      } catch (_error) {
        setIsLoggedIn(false);
      }
    };

    checkLoginStatus();

    const handleFocus = () => {
      checkLoginStatus();
    };

    window.addEventListener("focus", handleFocus);

    return () => {
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  // 로그인 상태에 따라 유틸리티 아이템 결정
  const utilityNavItems = [
    ...COMMON_UTILITY_NAV_ITEMS,
    ...(isLoggedIn
      ? LOGGED_IN_UTILITY_NAV_ITEMS
      : LOGGED_OUT_UTILITY_NAV_ITEMS),
  ];

  // 현재 경로가 활성 경로인지 확인
  const isActive = (itemPath: string) => {
    if (itemPath === "/") {
      return pathname === "/";
    }
    return pathname.startsWith(itemPath);
  };

  const handleLogout = async () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await authApi.logout();
      setIsLoggedIn(false);
      router.push("/login");
    } catch (error) {
      console.error("Failed to logout:", error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  // 모바일 메뉴 토글
  const toggleMobileMenu = useCallback(() => {
    setIsMobileMenuOpen((prev) => !prev);
  }, []);

  // 데스크톱 사이드바 토글
  const toggleDesktopSidebar = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  // 오버레이 클릭 시 모바일 메뉴 닫기
  const handleOverlayClick = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  // 네비게이션 아이템 컨테이너 클래스
  const navItemContainerClass = (
    active: boolean,
    additional?: string,
  ) =>
    [
      "flex items-center rounded-lg overflow-hidden",
      "transition-all duration-300 ease-in-out",
      // 모바일: 항상 확장 상태
      "gap-3 px-3 py-2 w-full min-h-[2.5rem]",
      // 태블릿/데스크톱: isOpen 상태에 따라 (높이를 auto로 변경하여 줌 대응)
      isOpen
        ? "sm:gap-3 sm:px-4 sm:py-2.5 sm:w-[204px] sm:min-h-[2.75rem]"
        : "sm:gap-0 sm:px-0 sm:py-2.5 sm:w-full sm:min-h-[2.75rem] sm:justify-center",
      active
        ? "bg-sidebar-item-active text-sidebar-item-active border border-sidebar-item-active"
        : "text-sidebar-item hover:bg-sidebar-item-sub-active",
      additional,
    ]
      .filter(Boolean)
      .join(" ");

  // 네비게이션 아이템 라벨 클래스
  const navItemLabelClass = (active: boolean) =>
    [
      "text-sm sm:text-base lg:text-lg whitespace-nowrap transition-all duration-300 ease-in-out truncate",
      // 모바일: 항상 표시
      "opacity-100 w-auto max-w-[140px] sm:max-w-[160px]",
      // 태블릿/데스크톱: isOpen 상태에 따라
      isOpen ? "sm:opacity-100 sm:w-auto" : "sm:opacity-0 sm:w-0 sm:overflow-hidden",
      active
        ? "font-semibold text-sidebar-item-active"
        : "font-normal text-sidebar-item",
    ]
      .filter(Boolean)
      .join(" ");

  // 사이드바 내부 콘텐츠 (모바일/데스크톱 공용)
  const SidebarContent = () => (
    <>
      {/* 햄버거 메뉴 버튼 (태블릿/데스크톱용) */}
      <button
        type="button"
        onClick={toggleDesktopSidebar}
        className={[
          "hidden sm:flex items-center justify-center absolute w-6 h-6 top-[42px]",
          "transition-all duration-300",
          // 터치 타겟 확대
          "p-1 -m-1",
          isOpen ? "right-[28px]" : "left-1/2 -translate-x-1/2",
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

      {/* 모바일 닫기 버튼 */}
      <button
        type="button"
        onClick={handleOverlayClick}
        className="sm:hidden absolute top-4 right-4 w-10 h-10 flex items-center justify-center rounded-lg hover:bg-sidebar-item-sub-active"
        aria-label="메뉴 닫기"
      >
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#C8C8C8"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>

      {/* 메인 네비게이션 */}
      <nav
        className={[
          // 모바일: 상단 여백 조정
          "absolute top-20 sm:top-[200px]",
          "transition-all duration-300",
          "left-4 right-4",
          // 태블릿/데스크톱: isOpen 상태에 따라
          isOpen ? "sm:left-[28px] sm:right-auto" : "sm:left-2 sm:right-2",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="메인 메뉴"
      >
        <ul className="flex flex-col gap-1 sm:gap-2 lg:gap-4">
          {MAIN_NAV_ITEMS.map((item) => {
            const active = isActive(item.path);
            return (
              <li key={item.path}>
                <Link
                  href={item.path}
                  className={navItemContainerClass(active)}
                  aria-current={active ? "page" : undefined}
                >
                  <div className="relative w-5 h-5 shrink-0">
                    <Icon
                      src={item.icon}
                      color={
                        active
                          ? SIDEBAR_ICON_COLORS.active
                          : SIDEBAR_ICON_COLORS.inactive
                      }
                      size={20}
                    />
                  </div>
                  <span className={navItemLabelClass(active)}>
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
          "absolute bottom-6 sm:bottom-24",
          "transition-all duration-300",
          "left-4 right-4",
          // 태블릿/데스크톱: isOpen 상태에 따라
          isOpen ? "sm:left-[28px] sm:right-auto" : "sm:left-2 sm:right-2",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="유틸리티 메뉴"
      >
        <ul className="flex flex-col gap-1 sm:gap-2 lg:gap-4">
          {/* 구분선 */}
          <li>
            <hr
              className={[
                "border-t border-sidebar mb-1 sm:mb-2 lg:mb-4",
                "transition-all duration-300",
                // 모바일/태블릿/데스크톱: 전체 너비
                "w-full",
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
                  className={navItemContainerClass(active)}
                  aria-current={active ? "page" : undefined}
                >
                  <div className="relative w-5 h-5 shrink-0">
                    <Icon
                      src={item.icon}
                      color={
                        active
                          ? SIDEBAR_ICON_COLORS.active
                          : SIDEBAR_ICON_COLORS.inactive
                      }
                      size={20}
                    />
                  </div>
                  <span className={navItemLabelClass(active)}>
                    {item.label}
                  </span>
                </Link>
              </li>
            );
          })}
          {isLoggedIn ? (
            <li>
              <button
                type="button"
                onClick={handleLogout}
                className={navItemContainerClass(false, "text-left disabled:opacity-60 disabled:cursor-not-allowed")}
                disabled={isLoggingOut}
              >
                <div className="relative w-5 h-5 shrink-0">
                  <Icon
                    src="/icons/logout.svg"
                    color={SIDEBAR_ICON_COLORS.inactive}
                    size={20}
                  />
                </div>
                <span className={navItemLabelClass(false)}>
                  {isLoggingOut ? "로그아웃 중..." : "로그아웃"}
                </span>
              </button>
            </li>
          ) : null}
        </ul>
      </nav>
    </>
  );

  return (
    <>
      {/* 모바일 햄버거 버튼 (헤더용) - layout.tsx에서 렌더링 */}
      <button
        type="button"
        onClick={toggleMobileMenu}
        className={[
          "sm:hidden fixed top-4 left-4 z-50",
          "w-11 h-11 flex items-center justify-center",
          "bg-sidebar rounded-lg shadow-lg",
          "transition-opacity duration-300",
          isMobileMenuOpen ? "opacity-0 pointer-events-none" : "opacity-100",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="메뉴 열기"
        aria-expanded={isMobileMenuOpen}
      >
        <Image
          src="/icons/hamburger.svg"
          alt=""
          width={24}
          height={24}
          className="object-contain"
          aria-hidden="true"
        />
      </button>

      {/* 모바일 오버레이 */}
      <div
        className={[
          "sm:hidden fixed inset-0 bg-black/50 z-40",
          "transition-opacity duration-300",
          isMobileMenuOpen ? "opacity-100" : "opacity-0 pointer-events-none",
        ]
          .filter(Boolean)
          .join(" ")}
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* 사이드바 */}
      <aside
        className={[
          // 기본 스타일
          "bg-sidebar shrink-0 overflow-hidden",
          "transition-all duration-300 ease-in-out",
          // 모바일: 오버레이 방식
          "fixed sm:relative",
          "inset-y-0 left-0 z-50 sm:z-auto",
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0",
          // 모바일: 너비 80% (최대 280px)
          "w-[80vw] max-w-[280px]",
          // 태블릿/데스크톱: isOpen 상태에 따른 너비
          isOpen ? "sm:w-[260px]" : "sm:w-[68px]",
          // 높이
          "h-full",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="메인 네비게이션"
      >
        <SidebarContent />
      </aside>
    </>
  );
}
