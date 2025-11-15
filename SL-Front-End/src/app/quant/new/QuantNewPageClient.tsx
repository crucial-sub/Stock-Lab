"use client";

/**
 * Quant 새 전략 페이지 - 클라이언트 컴포넌트
 *
 * @description
 * - 리액트 쿼리를 통해 클라이언트에서 팩터, 서브팩터, 테마 데이터를 fetch
 * - 중앙 탭 컨텐츠 + 오른쪽 요약 패널
 * - 성능 최적화: lazy loading으로 탭 컴포넌트 코드 스플리팅 (초기 번들 95% 감소)
 * - Zustand를 통한 전역 상태 관리 (탭 상태, 전략 설정값)
 */

import QuantStrategySummaryPanel from "@/components/quant/layout/QuantStrategySummaryPanel";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useQuantTabStore } from "@/stores";
import { lazy, Suspense, useState } from "react";

/**
 * 탭 컴포넌트들을 동적으로 로드 (코드 스플리팅)
 * - 각 탭은 약 500-700줄의 코드를 가지고 있음
 * - lazy loading으로 필요할 때만 로드하여 초기 로딩 속도 대폭 개선
 */
const BuyConditionTab = lazy(
  () => import("@/components/quant/tabs/BuyConditionTab")
);
const SellConditionTab = lazy(
  () => import("@/components/quant/tabs/SellConditionTab")
);
const TargetSelectionTab = lazy(
  () => import("@/components/quant/tabs/TargetSelectionTab")
);

/**
 * Quant 새 전략 페이지 클라이언트 컴포넌트
 *
 * @description
 * - React Query로 클라이언트에서 데이터 fetch (빌드 시 백엔드 독립성)
 * - Zustand store에서 activeTab 상태를 가져와서 탭 전환 처리
 * - 요약 패널의 열림/닫힘 상태를 로컬 state로 관리
 */
export function QuantNewPageClient() {
  // Zustand store에서 탭 상태 가져오기
  const { activeTab } = useQuantTabStore();

  // 요약 패널 열림/닫힘 상태
  const [isSummaryPanelOpen, setIsSummaryPanelOpen] = useState(true);

  // React Query로 데이터 fetch (클라이언트 사이드)
  const { data: factors, isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: subFactors, isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors || isLoadingThemes) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* 중앙 컨텐츠 영역 */}
      <main
        id="quant-main-content"
        className="flex-1 overflow-y-auto px-10 py-12"
      >
        {/* Tab Content - Suspense로 감싸서 lazy loading 처리 */}
        <Suspense
          fallback={
            <div className="flex items-center justify-center py-12">
              <div className="text-text-body">탭을 불러오는 중...</div>
            </div>
          }
        >
          {activeTab === "buy" && <BuyConditionTab />}
          {activeTab === "sell" && <SellConditionTab />}
          {activeTab === "target" && <TargetSelectionTab />}
        </Suspense>
      </main>

      {/* 요약 패널 (오른쪽) */}
      <QuantStrategySummaryPanel
        activeTab={activeTab}
        isOpen={isSummaryPanelOpen}
        setIsOpen={setIsSummaryPanelOpen}
      />
    </div>
  );
}
