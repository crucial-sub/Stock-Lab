"use client";

import { useState } from "react";
// TODO: amcharts5로 재작성 필요
// import { ReturnsChartWrapper } from "@/components/quant/result/ReturnsChartWrapper";
import type { BacktestResult } from "@/types/api";

/**
 * 수익률 탭 컴포넌트
 * - 다양한 차트 탭 (누적 수익률, 연도별, 월별, 종목별, 총 자산)
 * - amCharts5 기반 차트 표시
 */
interface ReturnsTabProps {
  yieldPoints: BacktestResult["yieldPoints"];
}

type ChartType = "cumulative" | "yearly" | "monthly" | "byStock" | "totalAssets";

export function ReturnsTab({ yieldPoints }: ReturnsTabProps) {
  const [activeChartTab, setActiveChartTab] = useState<ChartType>("cumulative");
  const [viewMode, setViewMode] = useState<"daily" | "log">("daily");

  const chartTabs: { id: ChartType; label: string }[] = [
    { id: "cumulative", label: "누적 수익률" },
    { id: "yearly", label: "연도별 수익률" },
    { id: "monthly", label: "월별 수익률" },
    { id: "byStock", label: "종목별 수익률" },
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
                ? "bg-accent-primary text-white"
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

          {/* 뷰 모드 토글 (일별/로그) */}
          {activeChartTab === "cumulative" && (
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode("daily")}
                className={`px-3 py-1 text-sm rounded-sm transition-colors ${viewMode === "daily"
                    ? "bg-accent-primary text-white"
                    : "border border-border-default hover:bg-bg-muted text-text-body"
                  }`}
              >
                일별
              </button>
              <button
                onClick={() => setViewMode("log")}
                className={`px-3 py-1 text-sm rounded-sm transition-colors ${viewMode === "log"
                    ? "bg-accent-primary text-white"
                    : "border border-border-default hover:bg-bg-muted text-text-body"
                  }`}
              >
                로그
              </button>
            </div>
          )}
        </div>

        {/* 범례 (누적 수익률 차트) */}
        {activeChartTab === "cumulative" && (
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 bg-accent-primary rounded-full" />
              수익률
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 bg-orange-500 rounded-full" />
              KOSPI
            </span>
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 bg-blue-500 rounded-full" />
              KOSDAQ
            </span>
          </div>
        )}

        {/* 차트 렌더링 */}
        {activeChartTab === "cumulative" && (
          <div className="w-full h-96 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
            <p className="text-text-muted">누적 수익률 차트 (amcharts5로 재작성 예정)</p>
          </div>
        )}

        {activeChartTab !== "cumulative" && (
          <div className="w-full h-96 bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
            <p className="text-text-muted">
              {chartTabs.find((t) => t.id === activeChartTab)?.label} 차트 (구현 예정)
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
