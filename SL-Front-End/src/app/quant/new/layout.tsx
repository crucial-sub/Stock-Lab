"use client";

import QuantStrategySidebar from "@/components/quant/QuantStrategySidebar";
import QuantStrategySummaryPanel from "@/components/quant/QuantStrategySummaryPanel";
import { cloneElement, isValidElement, ReactNode, useState } from "react";

interface QuantNewLayoutProps {
  children: ReactNode;
}

/**
 * 퀀트 전략 생성 페이지 레이아웃
 * - 좌측 사이드바: 매수 조건, 매도 조건, 매매 대상 메뉴
 * - 중앙 컨텐츠: 각 탭의 실제 내용
 * - 우측 요약 패널: 설정한 조건들의 요약
 * - Grid 레이아웃으로 반응형 구현
 */
export default function QuantNewLayout({ children }: QuantNewLayoutProps) {
  const [activeTab, setActiveTab] = useState<"buy" | "sell" | "target">("buy");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isPanelOpen, setIsPanelOpen] = useState(true);

  // children에게 activeTab과 setActiveTab을 props로 전달
  const childrenWithProps = isValidElement(children)
    ? cloneElement(children as React.ReactElement<any>, {
      activeTab,
      setActiveTab,
    })
    : children;

  return (
    <>
      {/* 좌측 사이드바 - SideNav 바로 옆에 fixed */}
      <div className="fixed top-[6rem] bottom-0 lg:left-64 hidden lg:block overflow-y-auto bg-bg-surface border-r border-DEFAULT z-10">
        <QuantStrategySidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          isOpen={isSidebarOpen}
          setIsOpen={setIsSidebarOpen}
        />
      </div>

      {/* 중앙 메인 컨텐츠 - 고정 위치 (양옆 패널 상태 무관) */}
      <div
        className="fixed top-[6rem] bottom-0 lg:left-[28.75rem] lg:right-[26.25rem] hidden lg:block overflow-y-auto bg-bg-app"
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
        }}
      >
        {childrenWithProps}
      </div>

      {/* 우측 요약 패널 - 화면 오른쪽 끝에 fixed */}
      <div className="fixed top-[6rem] bottom-0 right-0 hidden lg:block overflow-y-auto bg-bg-surface border-l border-DEFAULT z-10">
        <QuantStrategySummaryPanel
          activeTab={activeTab}
          isOpen={isPanelOpen}
          setIsOpen={setIsPanelOpen}
        />
      </div>
    </>
  );
}
