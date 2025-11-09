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

      // 중앙 컨텐츠 영역의 해당 섹션으로 스크롤
      scrollToSection(firstItem);
    }
  };

  // 세부 항목 클릭 핸들러 - 탭 전환 + 아이템 선택 + 스크롤
  const handleSubItemClick = (tab: "buy" | "sell" | "target", subItem: string) => {
    setSelectedSubItem(subItem);
    setActiveTab(tab);

    // 중앙 컨텐츠 영역의 해당 섹션으로 스크롤
    scrollToSection(subItem);
  };

  // 중앙 컨텐츠 영역의 섹션으로 스크롤하는 함수
  const scrollToSection = (sectionName: string) => {
    // 섹션 이름을 ID로 변환 (공백 제거, 소문자 변환)
    const sectionId = sectionName.replace(/\s+/g, '-').toLowerCase();
    const element = document.getElementById(sectionId);

    if (element) {
      // 부드러운 스크롤, 화면 중앙에 배치하여 최적의 가독성 제공
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });
    }
  };


  return (
    <div
      className={`relative
        min-h-full
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
