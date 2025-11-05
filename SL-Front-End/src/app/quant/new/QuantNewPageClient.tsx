"use client";

import { FilterGroup } from "@/components/common";
/**
 * Quant 페이지 - 클라이언트 컴포넌트
 * - 서버에서 prefetch된 팩터와 함수 데이터를 사용합니다
 * - 사용자 상호작용을 처리합니다
 */

import { BuyConditionTab } from "@/components/quant/BuyConditionTab";
import { SellConditionTab } from "@/components/quant/SellConditionTab";
import { TargetSelectionTab } from "@/components/quant/TargetSelectionTab";
import { STRATEGY_EDITOR_TABS } from "@/constants";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useState } from "react";

/**
 * Quant 새 전략 페이지 클라이언트 컴포넌트
 * - SSR로 prefetch된 데이터를 React Query를 통해 자동으로 사용합니다
 */
export function QuantNewPageClient() {
  const [activeTab, setActiveTab] = useState("buy");

  // 서버에서 prefetch된 데이터를 자동으로 사용 (추가 요청 없음)
  const { data: factors, isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: subFactors, isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors || isLoadingThemes) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-text-secondary">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="quant-container py-8 space-y-6">
        {/* 데이터 로드 확인 (개발용) */}
        {process.env.NODE_ENV === "development" && (
          <div className="text-xs text-text-tertiary">
            Factors: {factors?.length ?? 0} | SubFactors:{" "}
            {subFactors?.length ?? 0} | Themes: {themes?.length ?? 0}
          </div>
        )}

        {/* Tabs */}
        <FilterGroup
          items={STRATEGY_EDITOR_TABS}
          activeId={activeTab}
          onChange={setActiveTab}
        />

        {/* Tab Content */}
        {activeTab === "buy" && <BuyConditionTab />}
        {activeTab === "sell" && <SellConditionTab />}
        {activeTab === "target" && <TargetSelectionTab />}
      </div>
    </div>
  );
}
