"use client";

import { CumulativeReturnsChart } from "@/components/quant/result/charts/CumulativeReturnsChart";
import { MonthlyReturnsChart } from "@/components/quant/result/charts/MonthlyReturnsChart";
import { StockWiseReturnsChart } from "@/components/quant/result/charts/StockWiseReturnsChart";
import { TotalAssetsChart } from "@/components/quant/result/charts/TotalAssetsChart";
import { YearlyReturnsChart } from "@/components/quant/result/charts/YearlyReturnsChart";
import type { BacktestResult } from "@/types/api";
import { useState } from "react";

/**
 * 수익률 탭 컴포넌트
 * - 다양한 차트 탭 (누적 수익률, 연도별, 월별, 종목별, 총 자산)
 * - amCharts5 기반 차트 표시
 */
interface ReturnsTabProps {
  yieldPoints: BacktestResult["yieldPoints"];
  trades: BacktestResult["trades"];
}

type ChartType =
  | "cumulative"
  | "yearly"
  | "monthly"
  | "stockWise"
  | "totalAssets";

export function ReturnsTab({ yieldPoints, trades }: ReturnsTabProps) {
  const [activeChartTab, setActiveChartTab] = useState<ChartType>("cumulative");

  const chartTabs: { id: ChartType; label: string }[] = [
    { id: "cumulative", label: "누적 수익률" },
    { id: "yearly", label: "연도별 수익률" },
    { id: "monthly", label: "월별 수익률" },
    { id: "stockWise", label: "종목별 수익률" },
    { id: "totalAssets", label: "총 자산" },
  ];

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      {/* 차트 타입 탭 */}
      <div className="flex gap-3 mb-6">
        {chartTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveChartTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-sm transition-colors ${activeChartTab === tab.id
              ? "bg-brand-purple text-white"
              : "text-text-body hover:text-text-strong border border-border-default hover:bg-bg-muted"
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 차트 영역 */}
      <div className="space-y-4">
        {/* 차트 헤더 */}
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-bold text-text-strong">
            {chartTabs.find((t) => t.id === activeChartTab)?.label}
          </h3>
        </div>

        {/* 차트 렌더링 */}
        {activeChartTab === "cumulative" && (
          <CumulativeReturnsChart yieldPoints={yieldPoints} />
        )}

        {activeChartTab === "yearly" && (
          <YearlyReturnsChart yieldPoints={yieldPoints} />
        )}

        {activeChartTab === "monthly" && (
          <MonthlyReturnsChart yieldPoints={yieldPoints} />
        )}

        {activeChartTab === "stockWise" && (
          <StockWiseReturnsChart trades={trades} yieldPoints={yieldPoints} />
        )}

        {activeChartTab === "totalAssets" && (
          <TotalAssetsChart yieldPoints={yieldPoints} />
        )}
      </div>
    </div>
  );
}
