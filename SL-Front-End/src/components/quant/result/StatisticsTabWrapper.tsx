"use client";

import type { BacktestResult } from "@/types/api";
import dynamic from "next/dynamic";

/**
 * StatisticsTab을 dynamic import로 감싸는 래퍼 컴포넌트
 * - SSR 비활성화로 브라우저 전용 amCharts5 라이브러리 호환성 해결
 */
interface StatisticsTabWrapperProps {
  statistics: BacktestResult["statistics"];
}

// dynamic import with SSR disabled
const StatisticsTab = dynamic(
  () => import("./StatisticsTab").then((mod) => ({ default: mod.StatisticsTab })),
  {
    ssr: false,
    loading: () => (
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <p className="text-text-muted">통계 로딩 중...</p>
      </div>
    ),
  }
);

export function StatisticsTabWrapper({ statistics }: StatisticsTabWrapperProps) {
  return <StatisticsTab statistics={statistics} />;
}