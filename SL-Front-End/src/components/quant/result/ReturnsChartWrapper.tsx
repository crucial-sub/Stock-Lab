"use client";

import type { BacktestResult } from "@/types/api";
import dynamic from "next/dynamic";

/**
 * ReturnsChart를 dynamic import로 감싸는 래퍼 컴포넌트
 * - SSR 비활성화로 브라우저 전용 amCharts5 라이브러리 호환성 해결
 */
interface ReturnsChartWrapperProps {
  yieldPoints: BacktestResult["yieldPoints"];
  className?: string;
}

// dynamic import with SSR disabled
const ReturnsChart = dynamic(
  () => import("./ReturnsChart").then((mod) => ({ default: mod.ReturnsChart })),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[400px] bg-bg-app rounded-lg border border-border-default flex items-center justify-center">
        <p className="text-text-muted">차트 로딩 중...</p>
      </div>
    ),
  }
);

export function ReturnsChartWrapper({ yieldPoints, className }: ReturnsChartWrapperProps) {
  return <ReturnsChart yieldPoints={yieldPoints} className={className} />;
}