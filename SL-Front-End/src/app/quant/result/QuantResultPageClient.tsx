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
import {
  AutoTradingSection,
  PageHeader,
  StatisticsSection,
  TabNavigation,
} from "@/components/quant/result/sections";
import { SettingsTab } from "@/components/quant/result/SettingsTab";
import { StatisticsTabWrapper } from "@/components/quant/result/StatisticsTabWrapper";
import { StockInfoTab } from "@/components/quant/result/StockInfoTab";
import { TradingHistoryTab } from "@/components/quant/result/TradingHistoryTab";
import {
  useBacktestResultQuery,
  useBacktestSettingsQuery,
  useBacktestStatusQuery,
  backtestQueryKey,
} from "@/hooks/useBacktestQuery";
import { mockBacktestResult } from "@/mocks/backtestResult";
import { strategyApi } from "@/lib/api/strategy";
import { communityApi } from "@/lib/api/community";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { PortfolioShareModal } from "@/components/modal/PortfolioShareModal";

interface QuantResultPageClientProps {
  backtestId: string;
  initialStrategyName?: string;
}

type TabType = "stockInfo" | "returns" | "statistics" | "history" | "settings";

export function QuantResultPageClient({
  backtestId,
  initialStrategyName,
}: QuantResultPageClientProps) {
  const [activeTab, setActiveTab] = useState<TabType>("stockInfo");
  const [editableStrategyName, setEditableStrategyName] = useState<
    string | undefined
  >(initialStrategyName);
  const [hasEditedName, setHasEditedName] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editInputValue, setEditInputValue] = useState("");
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const previousStatusRef = useRef<string | undefined>(undefined);
  const router = useRouter();

  // Mock 모드 체크
  const isMockMode = backtestId.startsWith("mock");

  // 백테스트 상태 폴링 (pending/running 상태일 때만)
  const { data: statusData } = useBacktestStatusQuery(
    backtestId,
    !isMockMode, // mock 모드가 아닐 때만 활성화
    2000, // 2초마다 폴링
  );

  // React Query로 백테스트 결과 조회 (completed 상태일 때만)
  const {
    data: result,
    isLoading,
    error,
  } = useBacktestResultQuery(
    backtestId,
    !isMockMode && statusData?.status === "completed",
  );

  // 백테스트 설정 조회
  const { data: settings, isLoading: isLoadingSettings } =
    useBacktestSettingsQuery(
      backtestId,
      !isMockMode && statusData?.status === "completed",
    );

  const { data: myStrategies } = useQuery({
    queryKey: ["myStrategies"],
    queryFn: strategyApi.getMyStrategies,
    staleTime: 1000 * 30,
    enabled: !isMockMode,
  });

  const currentStrategyMeta = myStrategies?.strategies.find(
    (item) => item.sessionId === backtestId,
  );
  const strategyId = currentStrategyMeta?.strategyId;
  const isOwner = currentStrategyMeta !== undefined;
  const isPublic = currentStrategyMeta?.isPublic || false;

  const resolvedStrategyName =
    currentStrategyMeta?.strategyName ||
    statusData?.strategyName ||
    settings?.strategyName ||
    initialStrategyName;

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

  // 외부 데이터로부터 전략명 동기화 (사용자가 직접 수정한 경우는 유지)
  useEffect(() => {
    if (!hasEditedName && resolvedStrategyName) {
      setEditableStrategyName(resolvedStrategyName);
    }
  }, [hasEditedName, resolvedStrategyName]);

  const updateNameMutation = useMutation({
    mutationFn: (name: string) => {
      if (!strategyId) {
        return Promise.reject(new Error("전략 ID를 찾을 수 없습니다."));
      }
      return strategyApi.updateStrategyName(strategyId, name);
    },
    onSuccess: (_, name) => {
      setEditableStrategyName(name);
      setHasEditedName(true);
      setIsEditingName(false);
      queryClient.invalidateQueries({ queryKey: ["myStrategies"] });
      queryClient.invalidateQueries({
        queryKey: backtestQueryKey.status(backtestId),
      });
      queryClient.invalidateQueries({
        queryKey: backtestQueryKey.settings(backtestId),
      });
      queryClient.invalidateQueries({
        queryKey: backtestQueryKey.detail(backtestId),
      });

      queryClient.setQueryData(
        backtestQueryKey.status(backtestId),
        (prev: any) => (prev ? { ...prev, strategyName: name } : prev),
      );
      queryClient.setQueryData(
        backtestQueryKey.settings(backtestId),
        (prev: any) => (prev ? { ...prev, strategyName: name } : prev),
      );
    },
    onError: (error: any) => {
      alert(
        error?.response?.data?.detail ||
        error?.message ||
        "백테스트 이름을 수정하지 못했습니다.",
      );
    },
  });

  const handleStartEdit = () => {
    const currentName =
      editableStrategyName ||
      resolvedStrategyName ||
      backtestId ||
      "백테스트 이름";
    setEditInputValue(currentName);
    setIsEditingName(true);
  };

  const handleCancelEdit = () => {
    setIsEditingName(false);
    setEditInputValue("");
  };

  const handleSaveEdit = () => {
    const nextName = editInputValue.trim();
    if (!nextName) return;

    if (!strategyId) {
      alert("전략 ID를 찾을 수 없습니다. 새로고침 후 다시 시도해주세요.");
      return;
    }

    updateNameMutation.mutate(nextName);
  };

  // 전략 복제 핸들러
  const handleClone = async () => {
    try {
      await communityApi.cloneStrategy(backtestId);
      alert("전략이 성공적으로 복제되었습니다.");
      router.push("/quant");
    } catch (error: any) {
      alert(
        error?.response?.data?.detail ||
        error?.message ||
        "전략 복제에 실패했습니다."
      );
    }
  };

  // 전략 공유 토글 핸들러
  const handleToggleShare = () => {
    if (isPublic) {
      // 공유 해제
      if (confirm("전략 공유를 해제하시겠습니까?")) {
        handleShareConfirm({ description: "", isAnonymous: false });
      }
    } else {
      // 공유 설정 모달 열기
      setIsShareModalOpen(true);
    }
  };

  // 공유 설정 확인 핸들러
  const handleShareConfirm = async (params: {
    description: string;
    isAnonymous: boolean;
  }) => {
    if (!strategyId) {
      alert("전략 ID를 찾을 수 없습니다.");
      return;
    }

    try {
      await strategyApi.updateSharingSettings(strategyId, {
        isPublic: !isPublic,
        isAnonymous: params.isAnonymous,
      });
      // description은 별도로 업데이트
      if (params.description) {
        await strategyApi.updateStrategy(strategyId, {
          description: params.description,
        });
      }
      alert(
        isPublic
          ? "전략 공유가 해제되었습니다."
          : "전략이 성공적으로 공유되었습니다."
      );
      setIsShareModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["myStrategies"] });
    } catch (error: any) {
      alert(
        error?.response?.data?.detail ||
        error?.message ||
        "전략 공유 설정에 실패했습니다."
      );
    }
  };

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
  if (
    !isMockMode &&
    statusData &&
    (statusData.status === "pending" || statusData.status === "running")
  ) {
    console.log(
      "📊 백테스트 진행 중 - yieldPoints:",
      statusData.yieldPoints ? statusData.yieldPoints.length : 0,
    );
    return (
      <BacktestLoadingState
        backtestId={backtestId}
        strategyName={statusData.strategyName || initialStrategyName}
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
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
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

  const displayStrategyName =
    editableStrategyName ||
    resolvedStrategyName ||
    finalResult.id ||
    backtestId;

  return (
    <div className="min-h-screen py-[5rem] px-[3.5rem]">
      <div className="mx-auto">
        {/* 페이지 헤더 */}
        <PageHeader
          strategyName={displayStrategyName}
          isEditingName={isEditingName}
          editValue={editInputValue}
          isSavingName={updateNameMutation.isPending}
          onStartEdit={handleStartEdit}
          onChangeEditValue={setEditInputValue}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          isOwner={isOwner}
          isPublic={isPublic}
          onClone={handleClone}
          onToggleShare={handleToggleShare}
        />

        {/* 통계 섹션 */}
        <StatisticsSection
          statistics={finalResult.statistics}
          initialCapital={initialCapital}
          periodReturns={periodReturns}
        />

        {/* 자동매매 섹션 */}
        <AutoTradingSection
          sessionId={backtestId}
          sessionStatus={statusData?.status || "completed"}
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
          <ReturnsTab
            yieldPoints={finalResult.yieldPoints}
            trades={finalResult.trades}
          />
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

      {/* 공유 설정 모달 */}
      <PortfolioShareModal
        isOpen={isShareModalOpen}
        portfolioName={displayStrategyName}
        initialDescription=""
        initialIsAnonymous={false}
        onClose={() => setIsShareModalOpen(false)}
        onConfirm={handleShareConfirm}
      />
    </div>
  );
}
