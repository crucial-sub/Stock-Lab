"use client";

/**
 * Quant 페이지 - 클라이언트 컴포넌트
 * - 서버에서 prefetch된 팩터와 함수 데이터를 사용합니다
 * - 사용자 상호작용을 처리합니다
 */

import { BuyConditionTab } from "@/components/quant/BuyConditionTab";
import { SellConditionTab } from "@/components/quant/SellConditionTab";
import { TargetSelectionTab } from "@/components/quant/TargetSelectionTab";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useState } from "react";

type TabId = "buy" | "sell" | "target";

/**
 * Quant 새 전략 페이지 클라이언트 컴포넌트
 * - SSR로 prefetch된 데이터를 React Query를 통해 자동으로 사용합니다
 */
export function QuantNewPageClient() {
  const [activeTab, setActiveTab] = useState<TabId>("buy");

  // 서버에서 prefetch된 데이터를 자동으로 사용 (추가 요청 없음)
  const { data: factors, isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: functions, isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-text-secondary">데이터를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-app">
      <div className="quant-container py-8 space-y-6">
        {/* 데이터 로드 확인 (개발용) */}
        {process.env.NODE_ENV === "development" && (
          <div className="text-xs text-text-tertiary">
            Factors: {factors?.length ?? 0} | SubFactors:{" "}
            {functions?.length ?? 0}
          </div>
        )}

        {/* Tabs */}
        <div className="quant-tab-group">
          <button
            type="button"
            onClick={() => setActiveTab("buy")}
            className={`quant-tab ${activeTab === "buy" ? "is-active" : ""}`}
          >
            매수 조건
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("sell")}
            className={`quant-tab ${activeTab === "sell" ? "is-active" : ""}`}
          >
            매도 조건
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("target")}
            className={`quant-tab ${activeTab === "target" ? "is-active" : ""}`}
          >
            매매 대상 설정
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "buy" && <BuyConditionTab />}
        {activeTab === "sell" && <SellConditionTab />}
        {activeTab === "target" && <TargetSelectionTab />}
      </div>
    </div>
  );
}
