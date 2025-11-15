"use client";

import { useQuantTabStore } from "@/stores";
import Image from "next/image";
import { useState } from "react";

interface QuantStrategySidebarProps {
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

interface TabItemsType {
  tabName: "buy" | "sell" | "target",
  tabDisplayName: string,
  items: string[]
}

/**
 * 퀀트 전략 생성 페이지의 좌측 사이드바
 * - 매수 조건, 매도 조건, 매매 대상 메뉴
 * - 화살표 버튼으로 열기/닫기 가능
 * - 닫혀도 완전히 사라지지 않고 화살표만 표시
 * - Zustand로 탭 상태 전역 관리
 */
export default function QuantStrategySidebar({
  isOpen,
  setIsOpen,
}: QuantStrategySidebarProps) {
  // Zustand store에서 탭 상태 가져오기
  const { activeTab, setActiveTab } = useQuantTabStore();
  const [selectedSubItem, setSelectedSubItem] = useState<string>("일반 조건 설정");

  const tabItems: TabItemsType[] = [
    {
      tabName: "buy",
      tabDisplayName: "매수 조건",
      items: ['일반 조건 설정', '매수 조건 설정', '매수 비중 설정', '매수 방법 선택']
    },
    {
      tabName: "sell",
      tabDisplayName: "매도 조건",
      items: ['목표가 / 손절가', '보유 기간', '조건 매도']
    },
    {
      tabName: "target",
      tabDisplayName: "매매 대상 설정",
      items: ['매매 대상 선택']
    },
  ];

  // 탭 제목 클릭 핸들러 - 탭 전환 + 첫 번째 아이템 선택
  const handleTabClick = (tab: "buy" | "sell" | "target") => {
    const targetTab = tabItems.find(t => t.tabName === tab);
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
  const handleSubItemClick = (tab: "buy" | "sell" | "target", subItem: string) => {
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
      '일반 조건 설정': 'section-general-settings',
      '매수 조건 설정': 'section-buy-conditions',
      '매수 비중 설정': 'section-buy-weight',
      '매수 방법 선택': 'section-buy-method',
      '목표가 / 손절가': 'section-target-loss',
      '보유 기간': 'section-hold-period',
      '조건 매도': 'section-conditional-sell',
      '매매 대상 선택': 'section-trade-target',
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
    const scrollContainer = document.getElementById('quant-main-content');
    if (!scrollContainer) {
      console.warn('[Scroll] 스크롤 컨테이너를 찾을 수 없습니다: quant-main-content');
      return;
    }

    // 컨테이너 내에서 타겟 요소의 상대적 위치 계산
    const containerRect = scrollContainer.getBoundingClientRect();
    const targetRect = targetElement.getBoundingClientRect();

    // 타겟 요소가 컨테이너 상단에서 80px 아래에 오도록 스크롤 위치 계산
    const scrollOffset = targetRect.top - containerRect.top + scrollContainer.scrollTop - 80;

    // 스크롤 컨테이너를 스크롤
    scrollContainer.scrollTo({
      top: scrollOffset,
      behavior: 'smooth'
    });

    console.log(`[Scroll] 스크롤 실행: ${sectionName} → ${sectionId}, offset: ${scrollOffset}`);
  };


  return (
    <div
      className={`relative
        transition-all duration-300 ease-in-out
        ${isOpen ? "w-[12.5rem]" : "w-10"}
      `}
    >
      {/* 화살표 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`absolute ${isOpen ? "right-5 top-5" : "right-2 left-2 top-5"} top-5 z-10 hover:opacity-70 transition-opacity`}
        aria-label={isOpen ? "사이드바 닫기" : "사이드바 열기"}
      >
        <Image
          src={isOpen ? "/icons/arrow_left.svg" : "/icons/arrow_right.svg"}
          alt={isOpen ? "닫기" : "열기"}
          width={24}
          height={24}
        />
      </button>

      {/* 사이드바 컨텐츠 - 열린 상태에서만 표시 */}
      {isOpen && (
        <div className="pt-[7.5rem] px-5">
          {tabItems.map((tab) => (
            <div key={tab.tabName} className="mb-3">
              {/* 탭 제목 - 클릭 가능 */}
              <button
                onClick={() => handleTabClick(tab.tabName)}
                className={`
                  w-full text-left text-base font-semibold mb-3 rounded
                `}
              >
                {tab.tabDisplayName}
              </button>

              {/* 탭 아이템 목록 */}
              <ul className="flex flex-col gap-3">
                {tab.items && tab.items.map((item) => (
                  <li key={item}>
                    <button
                      onClick={() => handleSubItemClick(tab.tabName, item)}
                      className={`
                        text-left px-[1.125rem] py-[5px] rounded text-sm
                        transition-colors
                        ${selectedSubItem === item
                          ? "bg-bg-positive text-brand-primary font-semibold"
                          : ""
                        }
                      `}
                    >
                      {item}
                    </button>
                  </li>
                ))
                }
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
