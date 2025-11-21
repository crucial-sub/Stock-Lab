/**
 * 백테스트 결과 차트 섹션 컴포넌트
 *
 * 탭 네비게이션으로 5가지 차트를 전환하며 표시합니다.
 * - 누적 수익률 차트
 * - 연도별 수익률 차트
 * - 월별 수익률 차트
 * - 종목별 비중 차트
 * - 총 자산 차트
 *
 * 참조: 2025-01-19-ai-assistant-backtest-execution-plan.md 섹션 8.2
 */

"use client";

import { useState } from "react";
import { CumulativeReturnsChart } from "@/components/quant/result/charts/CumulativeReturnsChart";
import { YearlyReturnsChart } from "@/components/quant/result/charts/YearlyReturnsChart";
import { MonthlyReturnsChart } from "@/components/quant/result/charts/MonthlyReturnsChart";
import { StockWiseReturnsChart } from "@/components/quant/result/charts/StockWiseReturnsChart";
import { TotalAssetsChart } from "@/components/quant/result/charts/TotalAssetsChart";
import type { BacktestCompleteData } from "./BacktestResultView";

/**
 * 차트 탭 타입 정의
 */
type ChartTab =
  | "cumulative"
  | "yearly"
  | "monthly"
  | "stockwise"
  | "totalassets";

/**
 * ResultChartsSection Props
 */
interface ResultChartsSectionProps {
  /** 백테스트 완료 데이터 */
  result: BacktestCompleteData;
}

/**
 * 탭 버튼 컴포넌트
 */
interface TabButtonProps {
  isActive: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

function TabButton({ isActive, onClick, children }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={[
        "px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200",
        isActive
          ? "bg-brand-purple text-white shadow-md"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200 active:scale-95",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

/**
 * 백테스트 결과 차트 섹션
 *
 * - TabNavigation 패턴 재사용
 * - 5가지 차트를 탭으로 전환하며 표시
 * - 기존 Quant 페이지의 차트 컴포넌트 재사용
 * - 조건부 렌더링: 데이터가 없으면 해당 탭 숨김
 *
 * @example
 * ```tsx
 * function BacktestResult() {
 *   return <ResultChartsSection result={completeData} />;
 * }
 * ```
 */
export function ResultChartsSection({ result }: ResultChartsSectionProps) {
  const [activeTab, setActiveTab] = useState<ChartTab>("cumulative");

  /**
   * 탭 정의
   * - 데이터가 있는 차트만 탭으로 표시
   */
  const tabs: Array<{ id: ChartTab; label: string; hasData: boolean }> = [
    {
      id: "cumulative",
      label: "누적 수익률",
      hasData: result.allYieldPoints.length > 0,
    },
    {
      id: "yearly",
      label: "연도별 수익률",
      hasData: result.allYieldPoints.length > 0,
    },
    {
      id: "monthly",
      label: "월별 수익률",
      hasData: result.allYieldPoints.length > 0,
    },
    {
      id: "stockwise",
      label: "종목별 비중",
      hasData: result.allYieldPoints.length > 0,
    },
    {
      id: "totalassets",
      label: "총 자산",
      hasData: result.allYieldPoints.length > 0,
    },
  ];

  // 데이터가 있는 탭만 필터링
  const availableTabs = tabs.filter((tab) => tab.hasData);

  // 활성 탭이 사용 가능한 탭이 아니면 첫 번째 탭으로 설정
  const currentTab = availableTabs.find((tab) => tab.id === activeTab)
    ? activeTab
    : availableTabs[0]?.id ?? "cumulative";

  return (
    <div className="w-full max-w-[900px] mx-auto space-y-4">
      {/* 탭 네비게이션 */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {availableTabs.map((tab) => (
          <TabButton
            key={tab.id}
            isActive={currentTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </TabButton>
        ))}
      </div>

      {/* 차트 렌더링 영역 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {currentTab === "cumulative" && result.allYieldPoints.length > 0 && (
          <CumulativeReturnsChart yieldPoints={result.allYieldPoints} />
        )}

        {currentTab === "yearly" && result.yearlyReturns && (
          <YearlyReturnsChart yieldPoints={result.allYieldPoints} />
        )}

        {currentTab === "monthly" && result.monthlyReturns && (
          <MonthlyReturnsChart yieldPoints={result.allYieldPoints} />
        )}

        {currentTab === "stockwise" && result.stockWiseReturns && (
          <StockWiseReturnsChart
            // StockWiseReturnsChart는 trades도 필요한데, BacktestCompleteData에는 없음
            // 일단 빈 배열로 전달하고, 나중에 백엔드에서 trades도 포함하도록 수정 필요
            trades={[]}
            yieldPoints={result.allYieldPoints}
          />
        )}

        {currentTab === "totalassets" && result.totalAssetsData && (
          <TotalAssetsChart yieldPoints={result.allYieldPoints} />
        )}

        {/* 데이터가 없을 때 */}
        {availableTabs.length === 0 && (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <p>표시할 차트 데이터가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
}
