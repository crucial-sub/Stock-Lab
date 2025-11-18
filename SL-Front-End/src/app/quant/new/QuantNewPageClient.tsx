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

import { lazy, Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import QuantStrategySummaryPanel from "@/components/quant/layout/QuantStrategySummaryPanel";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useQuantTabStore } from "@/stores";
import { useBacktestConfigStore } from "@/stores/backtestConfigStore";
import { useRef } from "react";

/**
 * 탭 컴포넌트들을 동적으로 로드 (코드 스플리팅)
 * - 각 탭은 약 500-700줄의 코드를 가지고 있음
 * - lazy loading으로 필요할 때만 로드하여 초기 로딩 속도 대폭 개선
 */
const BuyConditionTab = lazy(
  () => import("@/components/quant/tabs/BuyConditionTab"),
);
const SellConditionTab = lazy(
  () => import("@/components/quant/tabs/SellConditionTab"),
);
const TargetSelectionTab = lazy(
  () => import("@/components/quant/tabs/TargetSelectionTab"),
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
  const conditionsAppliedRef = useRef(false);

  // React Query로 데이터 fetch (클라이언트 사이드)
  // 데이터는 하위 컴포넌트에서 사용하므로 여기서는 캐싱 목적으로만 fetch
  const { isLoading: isLoadingFactors } = useFactorsQuery();
  const { isLoading: isLoadingSubFactors } = useSubFactorsQuery();
  const { isLoading: isLoadingThemes } = useThemesQuery();

  // Query parameter로 전달된 조건 처리 (추천 전략에서 백테스트 실행 시)
  const searchParams = useSearchParams();
  const addBuyConditionUIWithData = useBacktestConfigStore((state) => state.addBuyConditionUIWithData);

  useEffect(() => {
    if (conditionsAppliedRef.current) return;
    const conditionsParam = searchParams.get("conditions");
    if (!conditionsParam) return;

    try {
      const conditions = JSON.parse(conditionsParam);
      conditionsAppliedRef.current = true;

      // 조건을 데이터와 함께 한 번에 추가
      conditions.forEach((dslCondition: any) => {
        const { factor, params, operator, value } = dslCondition;

        if (params && params.length > 0) {
          addBuyConditionUIWithData({
            factorName: factor,
            subFactorName: null,
            operator: operator,
            value: value !== null ? String(value) : "",
            argument: String(params[0]),
          });
        } else {
          addBuyConditionUIWithData({
            factorName: factor,
            subFactorName: null,
            operator: operator,
            value: value !== null ? String(value) : "",
          });
        }
      });

      // URL에서 조건 파라미터 제거 (한 번만 적용)
      const url = new URL(window.location.href);
      url.searchParams.delete("conditions");
      url.searchParams.delete("strategy_id");
      window.history.replaceState({}, "", url.toString());
    } catch (error) {
      console.error("조건 파싱 실패:", error);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 마운트 시 한 번만 실행

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
        className="flex-1 overflow-y-auto px-10 py-12 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
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
