"use client";

import Image from "next/image";
import { useState } from "react";
import { useQuantTabStore } from "@/stores";

/**
 * 퀀트 전략 생성 페이지의 2차 사이드바
 *
 * @description
 * - 매수 조건, 매도 조건, 매매 대상 탭 네비게이션
 * - 각 탭의 세부 항목 선택 및 스크롤 이동 기능
 * - 열림/닫힘 상태에서 부드러운 전환 효과
 * - Zustand를 통한 전역 탭 상태 관리
 */

interface TabItemsType {
  tabName: "buy" | "sell" | "target";
  tabDisplayName: string;
  items: string[];
}

interface SecondarySideNavProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

export function SecondarySideNav({ isOpen, setIsOpen }: SecondarySideNavProps) {
  const { activeTab, setActiveTab } = useQuantTabStore();
  const [selectedSubItem, setSelectedSubItem] =
    useState<string>("일반 조건 설정");

  const tabItems: TabItemsType[] = [
    {
      tabName: "buy",
      tabDisplayName: "매수 조건",
      items: [
        "일반 조건 설정",
        "매수 조건 설정",
        "매수 비중 설정",
        "매수 방법 선택",
      ],
    },
    {
      tabName: "sell",
      tabDisplayName: "매도 조건",
      items: ["목표가 / 손절가", "보유 기간", "조건 매도"],
    },
    {
      tabName: "target",
      tabDisplayName: "매매 대상 설정",
      items: ["매매 대상 선택"],
    },
  ];

  // 탭 제목 클릭 핸들러 - 탭 전환 + 첫 번째 아이템 선택
  const handleTabClick = (tab: "buy" | "sell" | "target") => {
    const targetTab = tabItems.find((t) => t.tabName === tab);
    if (targetTab && targetTab.items.length > 0) {
      const firstItem = targetTab.items[0];
      setSelectedSubItem(firstItem);
      setActiveTab(tab);

      // 탭 전환 후 DOM 렌더링을 기다린 후 스크롤 (100ms 딜레이)
      setTimeout(() => {
        scrollToSection(firstItem);
      }, 100);
    }
  };

  // 세부 항목 클릭 핸들러 - 탭 전환 + 아이템 선택 + 스크롤
  const handleSubItemClick = (
    tab: "buy" | "sell" | "target",
    subItem: string,
  ) => {
    const currentTab = activeTab;
    setSelectedSubItem(subItem);
    setActiveTab(tab);

    // 같은 탭 내에서는 즉시 스크롤, 다른 탭으로 전환 시 DOM 렌더링 대기 후 스크롤
    if (currentTab === tab) {
      scrollToSection(subItem);
    } else {
      setTimeout(() => {
        scrollToSection(subItem);
      }, 100);
    }
  };

  // 중앙 컨텐츠 영역의 섹션으로 스크롤하는 함수
  const scrollToSection = (sectionName: string) => {
    // 섹션 이름을 영문 ID로 매핑
    const sectionIdMap: Record<string, string> = {
      "일반 조건 설정": "section-general-settings",
      "매수 조건 설정": "section-buy-conditions",
      "매수 비중 설정": "section-buy-weight",
      "매수 방법 선택": "section-buy-method",
      "목표가 / 손절가": "section-target-loss",
      "보유 기간": "section-hold-period",
      "조건 매도": "section-conditional-sell",
      "매매 대상 선택": "section-trade-target",
    };

    const sectionId = sectionIdMap[sectionName];

    if (!sectionId) {
      console.warn(`[Scroll] 섹션 ID 매핑을 찾을 수 없습니다: ${sectionName}`);
      return;
    }

    // 타겟 섹션 요소 찾기
    const targetElement = document.getElementById(sectionId);
    if (!targetElement) {
      console.warn(`[Scroll] 타겟 요소를 찾을 수 없습니다: ${sectionId}`);
      return;
    }

    // 스크롤 컨테이너 찾기 (fixed 위치의 중앙 컨텐츠 영역)
    const scrollContainer = document.getElementById("quant-main-content");
    if (!scrollContainer) {
      console.warn(
        "[Scroll] 스크롤 컨테이너를 찾을 수 없습니다: quant-main-content",
      );
      return;
    }

    // 컨테이너 내에서 타겟 요소의 상대적 위치 계산
    const containerRect = scrollContainer.getBoundingClientRect();
    const targetRect = targetElement.getBoundingClientRect();

    // 타겟 요소가 컨테이너 상단에서 80px 아래에 오도록 스크롤 위치 계산
    const scrollOffset =
      targetRect.top - containerRect.top + scrollContainer.scrollTop - 80;

    // 스크롤 컨테이너를 스크롤
    scrollContainer.scrollTo({
      top: scrollOffset,
      behavior: "smooth",
    });

    console.log(
      `[Scroll] 스크롤 실행: ${sectionName} → ${sectionId}, offset: ${scrollOffset}`,
    );
  };

  return (
    <aside
      className={[
        "bg-sidebar flex flex-col border-l border-sidebar relative",
        "transition-all duration-300 ease-in-out",
        isOpen ? "w-[204px]" : "w-[52px]",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* 헤더: 토글 버튼 - 항상 보이도록 */}
      <div className="h-14 border-b border-surface flex items-center justify-center">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-8 h-8 flex items-center justify-center hover:opacity-70 transition-all shrink-0
            ${isOpen ? "ml-auto mr-4" : ""}
          `}
          aria-label={isOpen ? "사이드바 닫기" : "사이드바 열기"}
        >
          <Image
            src={isOpen ? "/icons/arrow_left.svg" : "/icons/arrow_right.svg"}
            alt=""
            width={24}
            height={24}
            className="object-contain"
            aria-hidden="true"
          />
        </button>
      </div>

      {/* 컨텐츠 - 열린 상태에서만 표시 */}
      {isOpen && (
        <nav className="flex-1 overflow-y-auto px-5 pt-8">
          {tabItems.map((tab) => (
            <div key={tab.tabName} className="mb-6">
              {/* 탭 제목 */}
              <button
                onClick={() => handleTabClick(tab.tabName)}
                className={[
                  "w-full text-left text-base font-semibold mb-3 text-sidebar-item transition-colors",
                  activeTab === tab.tabName ? "text-white" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {tab.tabDisplayName}
              </button>

              {/* 탭 아이템 목록 */}
              <ul className="flex flex-col gap-2">
                {tab.items.map((item) => (
                  <li key={item}>
                    <button
                      onClick={() => handleSubItemClick(tab.tabName, item)}
                      className={[
                        "w-full text-left px-[1.125rem] py-[5px] rounded-md text-sm",
                        "transition-all duration-200",
                        selectedSubItem === item
                          ? "bg-sidebar-item-sub-active text-white font-semibold"
                          : "text-sidebar-item hover:bg-sidebar-item-active hover:text-white",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      {item}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      )}

      {/* 닫힌 상태에서 시각적 힌트 (선택적) */}
      {!isOpen && (
        <div className="flex-1 flex items-start justify-center pt-8">
          <div className="w-1 h-16 bg-brand/20 rounded-full" />
        </div>
      )}
    </aside>
  );
}
