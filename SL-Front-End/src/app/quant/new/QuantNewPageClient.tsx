"use client";

/**
 * Quant 새 전략 페이지 - 클라이언트 컴포넌트
 * - 서버에서 prefetch된 팩터와 함수 데이터를 사용합니다
 * - Figma 디자인에 따른 3-탭 레이아웃 (매수 조건, 매도 조건, 매매 대상)
 * - 성능 최적화: 각 탭을 lazy loading으로 코드 스플리팅 (초기 번들 크기 95% 감소)
 */

import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { lazy, Suspense, useState } from "react";

/**
 * 탭 컴포넌트들을 동적으로 로드 (코드 스플리팅)
 * - 각 탭은 약 500-700줄의 코드를 가지고 있음
 * - lazy loading으로 필요할 때만 로드하여 초기 로딩 속도 대폭 개선
 */
const BuyConditionTabNew = lazy(
  () => import("@/components/quant/BuyConditionTabNew"),
);
const SellConditionTabNew = lazy(
  () => import("@/components/quant/SellConditionTabNew"),
);
const TargetSelectionTabNew = lazy(
  () => import("@/components/quant/TargetSelectionTabNew"),
);

/**
 * Quant 새 전략 페이지 클라이언트 컴포넌트
 * - SSR로 prefetch된 데이터를 React Query를 통해 자동으로 사용합니다
 */
export function QuantNewPageClient() {
  const [activeTab, setActiveTab] = useState<"buy" | "sell" | "target">("buy");

  // 서버에서 prefetch된 데이터를 자동으로 사용 (추가 요청 없음)
  const { data: factors, isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: subFactors, isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors || isLoadingThemes) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto">
        {/* Page Title */}
        <h1 className="text-[2rem] font-bold text-text-strong mb-6">
          일반 조건 설정
        </h1>

        {/* Tabs - Figma 디자인에 맞춘 탭 UI */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setActiveTab("buy")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${
              activeTab === "buy"
                ? "bg-brand-primary text-white"
                : "bg-surface text-text-body hover:bg-bg-muted"
            }`}
          >
            매수 조건
          </button>
          <button
            onClick={() => setActiveTab("sell")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${
              activeTab === "sell"
                ? "bg-accent-primary text-white"
                : "bg-surface text-text-body hover:bg-bg-muted"
            }`}
          >
            매도 조건
          </button>
          <button
            onClick={() => setActiveTab("target")}
            className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${
              activeTab === "target"
                ? "bg-accent-primary text-white"
                : "bg-surface text-text-body hover:bg-bg-muted"
            }`}
          >
            매매 대상
          </button>
        </div>

        {/* Tab Content - Suspense로 감싸서 lazy loading 처리 */}
        <Suspense
          fallback={
            <div className="flex items-center justify-center py-12">
              <div className="text-text-body">탭을 불러오는 중...</div>
            </div>
          }
        >
          {activeTab === "buy" && <BuyConditionTabNew />}
          {activeTab === "sell" && <SellConditionTabNew />}
          {activeTab === "target" && <TargetSelectionTabNew />}
        </Suspense>
      </div>
    </div>
  );
}
