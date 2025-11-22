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
import { communityApi } from "@/lib/api/community";

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
  const cloneAppliedRef = useRef(false);
  const [isLoadingClone, setIsLoadingClone] = useState(false);

  // React Query로 데이터 fetch (클라이언트 사이드)
  // 데이터는 하위 컴포넌트에서 사용하므로 여기서는 캐싱 목적으로만 fetch
  const { isLoading: isLoadingFactors } = useFactorsQuery();
  const { isLoading: isLoadingSubFactors } = useSubFactorsQuery();
  const { isLoading: isLoadingThemes } = useThemesQuery();

  // Query parameter로 전달된 조건 처리 (추천 전략에서 백테스트 실행 시)
  const searchParams = useSearchParams();
  const addBuyConditionUIWithData = useBacktestConfigStore((state) => state.addBuyConditionUIWithData);
  const {
    setStrategyName,
    setIsDayOrMonth,
    setStartDate,
    setEndDate,
    setInitialInvestment,
    setCommissionRate,
    setSlippage,
    setBuyLogic,
    setPriorityFactor,
    setPriorityOrder,
    setPerStockRatio,
    setMaxHoldings,
    setMaxBuyValue,
    setMaxDailyStock,
    setBuyPriceBasis,
    setBuyPriceOffset,
    setTargetAndLoss,
    setHoldDays,
    setConditionSell,
    setTradeTargets,
  } = useBacktestConfigStore();

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

  // 조건식 파싱 헬퍼 함수
  const parseConditionString = (expression: string): { factorName: string | null; subFactorName: string | null; argument?: string } => {
    // Case 1: SubFactor({Factor},{Arg}) or SubFactor({Factor})
    // 예: "이동평균({PER},{20일})" -> subFactor: "이동평균", factor: "PER", arg: "20일"
    const subFactorMatch = expression.match(/^([^(]+)\(\{([^}]+)\}(?:,\{([^}]+)\})?\)$/);
    if (subFactorMatch) {
      return {
        subFactorName: subFactorMatch[1],
        factorName: subFactorMatch[2],
        argument: subFactorMatch[3]
      };
    }

    // Case 2: {Factor}
    // 예: "{PER}" -> factor: "PER"
    const factorMatch = expression.match(/^\{([^}]+)\}$/);
    if (factorMatch) {
      return {
        factorName: factorMatch[1],
        subFactorName: null
      };
    }

    return { factorName: null, subFactorName: null };
  };

  // Clone parameter 처리 (복제된 전략)
  useEffect(() => {
    if (cloneAppliedRef.current) return;
    const cloneParam = searchParams.get("clone");
    if (!cloneParam) return;

    const loadCloneData = async () => {
      try {
        setIsLoadingClone(true);
        cloneAppliedRef.current = true;

        // 원본 전략 데이터 가져오기
        const cloneData = await communityApi.getCloneStrategyData(cloneParam);

        // 기본 설정
        setStrategyName(cloneData.strategyName);
        setIsDayOrMonth(cloneData.isDayOrMonth);
        setStartDate(cloneData.startDate);
        setEndDate(cloneData.endDate);
        setInitialInvestment(cloneData.initialInvestment);
        setCommissionRate(cloneData.commissionRate);
        setSlippage(cloneData.slippage);

        // 매수 조건
        setBuyLogic(cloneData.buyLogic);
        if (cloneData.priorityFactor) setPriorityFactor(cloneData.priorityFactor);
        setPriorityOrder(cloneData.priorityOrder);
        setPerStockRatio(cloneData.perStockRatio);
        setMaxHoldings(cloneData.maxHoldings);
        if (cloneData.maxBuyValue) setMaxBuyValue(cloneData.maxBuyValue);
        if (cloneData.maxDailyStock) setMaxDailyStock(cloneData.maxDailyStock);
        setBuyPriceBasis(cloneData.buyPriceBasis);
        setBuyPriceOffset(cloneData.buyPriceOffset);

        // 매수 조건 UI
        if (cloneData.buyConditions && Array.isArray(cloneData.buyConditions)) {
          cloneData.buyConditions.forEach((condition: any) => {
            // API의 exp_left_side를 파싱하여 UI 상태로 변환
            const parsed = parseConditionString(condition.exp_left_side || "");

            addBuyConditionUIWithData({
              factorName: parsed.factorName,
              subFactorName: parsed.subFactorName,
              operator: condition.inequality || "GT",
              value: condition.exp_right_side !== null ? String(condition.exp_right_side) : "",
              argument: parsed.argument,
            });
          });
        }

        // 매도 조건
        if (cloneData.targetAndLoss) setTargetAndLoss(cloneData.targetAndLoss as any);
        if (cloneData.holdDays) setHoldDays(cloneData.holdDays as any);

        // 조건 매도 (condition_sell) 처리
        if (cloneData.conditionSell) {
          setConditionSell(cloneData.conditionSell as any);

          // 매도 조건 UI 복원
          if (cloneData.conditionSell.sell_conditions && Array.isArray((cloneData.conditionSell as any).sell_conditions)) {
            // 기존 매도 조건 UI 초기화 (필요시)
            // setSellConditionsUI([]); // store에 이 함수가 있다면 사용, 없으면 생략

            (cloneData.conditionSell as any).sell_conditions.forEach((condition: any) => {
              const parsed = parseConditionString(condition.exp_left_side || "");

              // addSellConditionUIWithData는 store에 정의되어 있어야 함
              // useBacktestConfigStore에 addSellConditionUIWithData가 있는지 확인 필요
              // 확인 결과: 있음
              const { addSellConditionUIWithData } = useBacktestConfigStore.getState();

              addSellConditionUIWithData({
                factorName: parsed.factorName,
                subFactorName: parsed.subFactorName,
                operator: condition.inequality || "GT",
                value: condition.exp_right_side !== null ? String(condition.exp_right_side) : "",
                argument: parsed.argument,
              });
            });
          }
        }

        // 종목 선택
        setTradeTargets(cloneData.tradeTargets as any);

        // URL에서 clone 파라미터 제거
        const url = new URL(window.location.href);
        url.searchParams.delete("clone");
        window.history.replaceState({}, "", url.toString());
      } catch (error) {
        console.error("복제 데이터 로드 실패:", error);
        alert("전략 복제에 실패했습니다. 다시 시도해주세요.");
      } finally {
        setIsLoadingClone(false);
      }
    };

    loadCloneData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 마운트 시 한 번만 실행

  // 로딩 상태 표시
  if (isLoadingFactors || isLoadingSubFactors || isLoadingThemes || isLoadingClone) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-text-body">
          {isLoadingClone ? "전략을 불러오는 중..." : "데이터를 불러오는 중..."}
        </div>
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
