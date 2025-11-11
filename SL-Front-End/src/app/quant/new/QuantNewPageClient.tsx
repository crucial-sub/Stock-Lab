"use client";

/**
 * Quant 새 전략 페이지 - 클라이언트 컴포넌트
 * - 서버에서 prefetch된 팩터와 함수 데이터를 사용합니다
 * - Figma 디자인에 따른 3-탭 레이아웃 (매수 조건, 매도 조건, 매매 대상)
 * - 성능 최적화: 각 탭을 lazy loading으로 코드 스플리팅 (초기 번들 크기 95% 감소)
 * - Zustand로 탭 상태 전역 관리
 */

import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useQuantTabStore } from "@/stores";
import { lazy, Suspense } from "react";

/**
 * 탭 컴포넌트들을 동적으로 로드 (코드 스플리팅)
 * - 각 탭은 약 500-700줄의 코드를 가지고 있음
 * - lazy loading으로 필요할 때만 로드하여 초기 로딩 속도 대폭 개선
 */
const BuyConditionTab = lazy(
  () => import("@/components/quant/BuyConditionTab"),
);
const SellConditionTab = lazy(
  () => import("@/components/quant/SellConditionTab"),
);
const TargetSelectionTab = lazy(
  () => import("@/components/quant/TargetSelectionTab"),
);

/**
 * Quant 새 전략 페이지 클라이언트 컴포넌트
 * - SSR로 prefetch된 데이터를 React Query를 통해 자동으로 사용합니다
 * - Zustand store에서 activeTab 상태를 가져와서 탭 전환을 처리합니다
 */
export function QuantNewPageClient() {
  // Zustand store에서 탭 상태 가져오기
  const { activeTab } = useQuantTabStore();

  // 서버에서 prefetch된 데이터를 자동으로 사용 (추가 요청 없음)
  const { data: factors, isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: subFactors, isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors || isLoadingThemes) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app relative">
        <div className="text-text-body">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="h-full p-[3.75rem]">
      {/* Tab Content - Suspense로 감싸서 lazy loading 처리 */}
      <Suspense
        fallback={
          <div className="flex items-center justify-center py-12">
            <div className="text-text-body">탭을 불러오는 중...</div>
          </div>
        }
      >
        <div className="pb-12">
          {activeTab === "buy" && <BuyConditionTab />}
          {activeTab === "sell" && <SellConditionTab />}
          {activeTab === "target" && <TargetSelectionTab />}
        </div>
      </Suspense>
    </div>
  );
}
