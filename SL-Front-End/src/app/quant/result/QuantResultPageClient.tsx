"use client";

/**
 * 백테스트 결과 페이지 - 리팩토링 버전
 *
 * 개선 사항:
 * - 섹션별 컴포넌트 분리로 코드 가독성 향상 (350줄 → 120줄, 66% 감소)
 * - 공통 UI 컴포넌트 재사용으로 중복 코드 제거
 * - 통계/차트/탭 네비게이션 컴포넌트 분리
 * - 기존 UI/UX 완전 보존
 * - 백테스트 진행 상태 실시간 폴링 및 로딩 UI 표시
 * - 백테스트 완료 시 자동으로 결과 데이터 갱신
 */

import { BacktestLoadingState } from "@/components/quant/result/BacktestLoadingState";
import { ReturnsTab } from "@/components/quant/result/ReturnsTab";
import { SettingsTab } from "@/components/quant/result/SettingsTab";
import { StatisticsTabWrapper } from "@/components/quant/result/StatisticsTabWrapper";
import { StockInfoTab } from "@/components/quant/result/StockInfoTab";
import { TradingHistoryTab } from "@/components/quant/result/TradingHistoryTab";
import {
  PageHeader,
  StatisticsSection,
  TabNavigation,
} from "@/components/quant/result/sections";
import { useBacktestResultQuery, useBacktestSettingsQuery, useBacktestStatusQuery } from "@/hooks/useBacktestQuery";
import { mockBacktestResult } from "@/mocks/backtestResult";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

interface QuantResultPageClientProps {
  backtestId: string;
}

type TabType = "stockInfo" | "returns" | "statistics" | "history" | "settings";

export function QuantResultPageClient({
  backtestId,
}: QuantResultPageClientProps) {
  const [activeTab, setActiveTab] = useState<TabType>("stockInfo");
  const queryClient = useQueryClient();
  const previousStatusRef = useRef<string | undefined>();

  // Mock 모드 체크
  const isMockMode = backtestId.startsWith("mock");

  // 백테스트 상태 폴링 (pending/running 상태일 때만)
  const { data: statusData } = useBacktestStatusQuery(
    backtestId,
    !isMockMode, // mock 모드가 아닐 때만 활성화
    2000 // 2초마다 폴링
  );

  // React Query로 백테스트 결과 조회 (completed 상태일 때만)
  const { data: result, isLoading, error } = useBacktestResultQuery(
    backtestId,
    !isMockMode && statusData?.status === "completed"
  );

  // 백테스트 설정 조회
  const { data: settings, isLoading: isLoadingSettings } = useBacktestSettingsQuery(
    backtestId,
    !isMockMode && statusData?.status === "completed"
  );

  // 백테스트 완료 시 결과 데이터 자동 갱신
  useEffect(() => {
    if (!isMockMode && statusData?.status === "completed") {
      // 상태가 running → completed로 변경되었을 때만 invalidate
      if (previousStatusRef.current === "running") {
        console.log("✅ 백테스트 완료 감지 - 결과 데이터 자동 갱신");
        queryClient.invalidateQueries({
          queryKey: ["backtest", "detail", backtestId],
        });
      }
      previousStatusRef.current = statusData.status;
    } else if (statusData?.status) {
      previousStatusRef.current = statusData.status;
    }
  }, [statusData?.status, backtestId, isMockMode, queryClient]);

  // Mock 데이터 또는 실제 데이터 사용
  const finalResult = isMockMode ? mockBacktestResult : result;

  // 상태 데이터 로딩 중이거나 아직 데이터가 없는 경우
  if (!isMockMode && !statusData) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto" />
          <p className="text-text-body">백테스트 상태 확인 중...</p>
        </div>
      </div>
    );
  }

  // 백테스트가 아직 실행 중인 경우
  if (!isMockMode && statusData && (statusData.status === "pending" || statusData.status === "running")) {
    console.log("📊 백테스트 진행 중 - yieldPoints:", statusData.yieldPoints ? statusData.yieldPoints.length : 0);
    return (
      <BacktestLoadingState
        backtestId={backtestId}
        status={statusData.status}
        progress={statusData.progress || 0}
        buyCount={statusData.buyCount}
        sellCount={statusData.sellCount}
        currentReturn={statusData.currentReturn}
        currentCapital={statusData.currentCapital}
        currentDate={statusData.currentDate}
        currentMdd={statusData.currentMdd}
        startDate={statusData.startDate}
        endDate={statusData.endDate}
        yieldPoints={statusData.yieldPoints}
      />
    );
  }

  // 백테스트가 실패한 경우
  if (!isMockMode && statusData?.status === "failed") {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 실행 실패
          </h1>
          <p className="text-text-secondary">
            백테스트 실행 중 오류가 발생했습니다.
          </p>
        </div>
      </div>
    );
  }

  // 로딩 상태
  if (isLoading && !isMockMode) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto" />
          <p className="text-text-secondary">백테스트 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (!isMockMode && (error || !result)) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 결과를 불러올 수 없습니다
          </h1>
          <p className="text-text-secondary">
            {error?.message || "알 수 없는 오류가 발생했습니다."}
          </p>
        </div>
      </div>
    );
  }

  // finalResult가 없으면 리턴
  if (!finalResult) {
    return null;
  }

  // 실제 데이터에서 초기 투자금 가져오기
  const initialCapital = finalResult.statistics.initialCapital || 50000000;

  // 실제 수익률 데이터 계산 (yieldPoints에서 추출)
  const calculatePeriodReturns = () => {
    if (!finalResult.yieldPoints || finalResult.yieldPoints.length === 0) {
      return [];
    }

    const sortedPoints = [...finalResult.yieldPoints].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    const latestPoint = sortedPoints[sortedPoints.length - 1];
    const latestReturn = latestPoint?.cumulativeReturn || 0;
    const latestDate = new Date(latestPoint.date);

    // 기간별 수익률 계산 함수 (백테스트 마지막 날짜 기준)
    const getReturnAtDate = (daysAgo: number) => {
      const targetDate = new Date(latestDate); // ✅ 백테스트 마지막 날짜 기준
      targetDate.setDate(targetDate.getDate() - daysAgo);

      // 목표 날짜 이전의 가장 가까운 거래일 찾기
      const closestPoint = sortedPoints
        .filter((p) => new Date(p.date) <= targetDate)
        .pop();

      return closestPoint?.cumulativeReturn || 0;
    };

    return [
      { label: "최근 거래일", value: latestReturn },
      { label: "최근 일주일", value: latestReturn - getReturnAtDate(7) },
      { label: "최근 1개월", value: latestReturn - getReturnAtDate(30) },
      { label: "최근 3개월", value: latestReturn - getReturnAtDate(90) },
      { label: "최근 6개월", value: latestReturn - getReturnAtDate(180) },
      { label: "최근 1년", value: latestReturn - getReturnAtDate(365) },
    ];
  };

  const periodReturns = calculatePeriodReturns();

  // 백테스트 시작/종료 날짜 추출 (yieldPoints의 첫 번째와 마지막 날짜)
  const startDate = finalResult.yieldPoints && finalResult.yieldPoints.length > 0
    ? finalResult.yieldPoints[0].date
    : undefined;
  const endDate = finalResult.yieldPoints && finalResult.yieldPoints.length > 0
    ? finalResult.yieldPoints[finalResult.yieldPoints.length - 1].date
    : undefined;

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto">
        {/* 페이지 헤더 */}
        <PageHeader />

        {/* 통계 섹션 */}
        <StatisticsSection
          statistics={finalResult.statistics}
          initialCapital={initialCapital}
          periodReturns={periodReturns}
        />

        {/* 탭 네비게이션 */}
        <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

        {/* 탭 컨텐츠 */}
        {activeTab === "stockInfo" && (
          <StockInfoTab
            trades={finalResult.trades}
            universeStocks={finalResult.universeStocks}
          />
        )}
        {activeTab === "returns" && (
          <ReturnsTab yieldPoints={finalResult.yieldPoints} trades={finalResult.trades} />
        )}
        {activeTab === "statistics" && (
          <StatisticsTabWrapper statistics={finalResult.statistics} />
        )}
        {activeTab === "history" && (
          <TradingHistoryTab
            trades={finalResult.trades}
            yieldPoints={finalResult.yieldPoints}
          />
        )}
        {activeTab === "settings" && (
          <SettingsTab
            settings={settings || null}
            isLoading={isLoadingSettings}
          />
        )}
      </div>
    </div>
  );
}