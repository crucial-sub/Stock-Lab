"use client";

/**
 * 백테스트 결과 페이지 - 클라이언트 컴포넌트
 * - 서버에서 prefetch된 백테스트 결과 데이터를 사용합니다
 * - 대용량 매매 데이터를 무한 스크롤로 처리합니다
 */

import { useMemo, useState, useEffect, useRef } from "react";
import { FilterGroup, Panel } from "@/components/common";
import { BACKTEST_RESULT_TABS } from "@/constants";
import {
  useBacktestResultQuery,
  useBacktestTradesInfiniteQuery,
  useBacktestStatusQuery,
} from "@/hooks/useBacktestQuery";

/**
 * 백테스트 결과 페이지 클라이언트 컴포넌트 Props
 */
interface QuantResultPageClientProps {
  backtestId: string;
}

/**
 * 백테스트 결과 페이지 클라이언트 컴포넌트
 * - SSR로 prefetch된 데이터를 React Query를 통해 자동으로 사용합니다
 * - 매매 내역은 무한 스크롤로 처리합니다
 */
export function QuantResultPageClient({
  backtestId,
}: QuantResultPageClientProps) {
  const [activeTab, setActiveTab] = useState("stocks");

  // 서버에서 prefetch된 백테스트 결과 데이터 사용
  const {
    data: backtestResult,
    isLoading: isLoadingResult,
  } = useBacktestResultQuery(backtestId);

  // 백테스트 상태 폴링 (실행 중인 경우에만)
  const { data: statusData } = useBacktestStatusQuery(
    backtestId,
    backtestResult?.status === "running" || backtestResult?.status === "pending",
  );

  // 매매 내역 무한 스크롤
  const {
    data: tradesData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useBacktestTradesInfiniteQuery(backtestId);

  // 무한 스크롤을 위한 Intersection Observer
  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // 모든 페이지의 매매 내역을 합침
  const allTrades = useMemo(() => {
    if (!tradesData) return [];
    return tradesData.pages.flatMap((page) => page.data);
  }, [tradesData]);

  // 통계 지표 (mock 데이터 대신 실제 데이터 사용)
  const statsMetrics = useMemo(() => {
    if (!backtestResult) return [];

    return [
      {
        label: "총 수익률",
        value: `${backtestResult.statistics.totalReturn.toFixed(2)}%`,
        tone: backtestResult.statistics.totalReturn >= 0 ? "positive" : "negative",
        group: "통계",
      },
      {
        label: "연환산 수익률",
        value: `${backtestResult.statistics.annualizedReturn.toFixed(2)}%`,
        tone: backtestResult.statistics.annualizedReturn >= 0 ? "positive" : "negative",
        group: "통계",
      },
      {
        label: "샤프 비율",
        value: backtestResult.statistics.sharpeRatio.toFixed(2),
        tone: backtestResult.statistics.sharpeRatio >= 1 ? "positive" : "neutral",
        group: "통계",
      },
      {
        label: "MDD",
        value: `${backtestResult.statistics.maxDrawdown.toFixed(2)}%`,
        tone: "negative",
        group: "통계",
      },
      {
        label: "승률",
        value: `${backtestResult.statistics.winRate.toFixed(2)}%`,
        tone: backtestResult.statistics.winRate >= 50 ? "positive" : "negative",
        group: "통계",
      },
      {
        label: "손익비",
        value: backtestResult.statistics.profitFactor.toFixed(2),
        tone: backtestResult.statistics.profitFactor >= 1 ? "positive" : "negative",
        group: "통계",
      },
      {
        label: "변동성",
        value: `${backtestResult.statistics.volatility.toFixed(2)}%`,
        tone: "neutral",
        group: "통계",
      },
    ];
  }, [backtestResult]);

  // 매매 결과 지표
  const tradeMetrics = useMemo(() => {
    if (!backtestResult) return [];

    const totalTrades = backtestResult.trades.length;
    const winningTrades = backtestResult.trades.filter((t) => t.profit > 0).length;
    const losingTrades = totalTrades - winningTrades;
    const avgProfit = backtestResult.trades.reduce((sum, t) => sum + t.profit, 0) / totalTrades;

    return [
      {
        label: "총 거래 수",
        value: totalTrades.toString(),
        tone: "neutral",
        group: "매매 결과",
      },
      {
        label: "수익 거래",
        value: winningTrades.toString(),
        tone: "positive",
        group: "매매 결과",
      },
      {
        label: "손실 거래",
        value: losingTrades.toString(),
        tone: "negative",
        group: "매매 결과",
      },
      {
        label: "평균 수익",
        value: `${avgProfit.toFixed(0)}원`,
        tone: avgProfit >= 0 ? "positive" : "negative",
        group: "매매 결과",
      },
    ];
  }, [backtestResult]);

  // 수익률 차트 데이터 (간이 차트용)
  const yieldChartData = useMemo(() => {
    if (!backtestResult) return [];

    // 최근 5개 데이터 포인트만 사용 (간이 차트)
    return backtestResult.yieldPoints.slice(-5).map((point) => ({
      label: new Date(point.date).toLocaleDateString("ko-KR", {
        month: "short",
        day: "numeric",
      }),
      value: point.value,
    }));
  }, [backtestResult]);

  // 수익률 최대 절대값
  const maxYield = useMemo(() => {
    return Math.max(
      ...yieldChartData.map((point) => Math.abs(point.value)),
      1,
    );
  }, [yieldChartData]);

  /** 지표 색상 클래스 반환 */
  const getMetricToneClass = (tone: string | undefined) => {
    if (tone === "positive") return "text-state-positive";
    if (tone === "negative") return "text-state-negative";
    return "text-text-primary";
  };

  /** 수익률 양/음수에 따른 색상 */
  const getYieldBarClass = (value: number) => {
    return value >= 0 ? "bg-state-positive" : "bg-state-negative";
  };

  /** 탭 전환 시 보여줄 본문 렌더 */
  const renderTabContent = () => {
    if (activeTab === "stocks") {
      return (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-text-secondary">
              <tr className="border-b border-border-subtle">
                <th className="py-3">매매 종목명</th>
                <th className="py-3">거래 단가(원)</th>
                <th className="py-3">수익(원)</th>
                <th className="py-3">수익률(%)</th>
                <th className="py-3">매수일자</th>
                <th className="py-3">매도일자</th>
                <th className="py-3">보유 비중(%)</th>
                <th className="py-3">평가 금액(원)</th>
              </tr>
            </thead>
            <tbody>
              {allTrades.map((trade, index) => (
                <tr
                  key={`${trade.stockCode}-${index}`}
                  className="border-b border-border-subtle/50 text-text-primary"
                >
                  <td className="py-3">{trade.stockName}</td>
                  <td className="py-3">{trade.buyPrice.toLocaleString()}</td>
                  <td className="py-3">{trade.profit.toLocaleString()}</td>
                  <td
                    className={`py-3 ${trade.profitRate >= 0 ? "text-state-positive" : "text-state-negative"}`}
                  >
                    {trade.profitRate.toFixed(2)}%
                  </td>
                  <td className="py-3">
                    {new Date(trade.buyDate).toLocaleDateString("ko-KR")}
                  </td>
                  <td className="py-3">
                    {new Date(trade.sellDate).toLocaleDateString("ko-KR")}
                  </td>
                  <td className="py-3">{trade.weight.toFixed(2)}%</td>
                  <td className="py-3">{trade.valuation.toLocaleString()}원</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* 무한 스크롤 트리거 */}
          {hasNextPage && (
            <div
              ref={loadMoreRef}
              className="py-4 text-center text-text-tertiary"
            >
              {isFetchingNextPage ? "로딩 중..." : "더 불러오기"}
            </div>
          )}
        </div>
      );
    }

    if (activeTab === "yield") {
      return (
        <div className="flex flex-col items-center justify-center py-8 text-sm text-text-tertiary">
          <p>수익률 상세 분석 기능은 추후 제공될 예정입니다.</p>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center py-8 text-sm text-text-tertiary">
        <p>설정 조건 확인 기능은 추후 제공될 예정입니다.</p>
      </div>
    );
  };

  // 로딩 상태
  if (isLoadingResult) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-text-secondary">데이터를 불러오는 중...</div>
      </div>
    );
  }

  // 백테스트 실행 중
  if (backtestResult?.status === "running" || backtestResult?.status === "pending") {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 실행 중...
          </h1>
          <p className="text-text-secondary">
            {statusData?.progress ? `진행률: ${statusData.progress}%` : "잠시만 기다려주세요"}
          </p>
        </div>
      </div>
    );
  }

  // 백테스트 실패
  if (backtestResult?.status === "failed") {
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

  return (
    <div className="min-h-screen bg-bg-app pb-16">
      <div className="quant-container space-y-6 py-8">
        {/* 페이지 타이틀 */}
        <div>
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 결과
          </h1>
        </div>

        {/* 통계 요약 패널 */}
        <Panel className="p-6">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[2fr_2fr]">
            {/* 지표 요약 */}
            <div>
              <div className="space-y-5">
                {/* 통계 지표 */}
                <section>
                  <h2 className="text-lg font-medium uppercase tracking-wide text-text-primary">
                    통계
                  </h2>
                  <div className="grid grid-cols-1 gap-3 rounded-lg py-2 sm:grid-cols-2 lg:grid-cols-4">
                    {statsMetrics.slice(0, 4).map((metric) => (
                      <div key={metric.label} className="space-y-1">
                        <div
                          className={`text-sm font-semibold ${getMetricToneClass(metric.tone)}`}
                        >
                          {metric.value}
                        </div>
                        <div className="text-xs text-text-tertiary">
                          {metric.label}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 gap-3 rounded-lg py-2 sm:grid-cols-2 lg:grid-cols-3">
                    {statsMetrics.slice(4).map((metric) => (
                      <div key={metric.label} className="space-y-1">
                        <div
                          className={`text-sm font-semibold ${getMetricToneClass(metric.tone)}`}
                        >
                          {metric.value}
                        </div>
                        <div className="text-xs text-text-tertiary">
                          {metric.label}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                {/* 매매 결과 */}
                <section>
                  <h2 className="text-lg font-medium uppercase tracking-wide text-text-primary">
                    매매 결과
                  </h2>
                  <div className="grid grid-cols-1 gap-3 rounded-lg py-2 sm:grid-cols-2 lg:grid-cols-4">
                    {tradeMetrics.map((metric) => (
                      <div key={metric.label} className="space-y-1">
                        <div
                          className={`text-sm font-semibold ${getMetricToneClass(metric.tone)}`}
                        >
                          {metric.value}
                        </div>
                        <div className="text-xs text-text-tertiary">
                          {metric.label}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </div>

            {/* 수익률 간이 차트 */}
            <div className="flex flex-col">
              <h2 className="text-lg font-medium uppercase tracking-wide text-text-primary pb-2">
                수익률
              </h2>
              <div className="flex flex-1 items-end justify-between gap-3 rounded-lg bg-white/5 p-3">
                {yieldChartData.map((point) => {
                  const barHeight = Math.round((Math.abs(point.value) / maxYield) * 100);
                  return (
                    <div
                      key={point.label}
                      className="flex flex-1 flex-col items-center gap-2 text-xs text-text-secondary"
                    >
                      <div className="flex h-48 w-full items-end justify-center">
                        <div
                          className={`${getYieldBarClass(point.value)} w-10 rounded-md transition-all`}
                          style={{ height: `${barHeight}%` }}
                        />
                      </div>
                      <div className="text-[11px] text-text-tertiary">
                        {point.label}
                      </div>
                      <div
                        className={`text-xs font-semibold ${point.value >= 0 ? "text-state-positive" : "text-state-negative"}`}
                      >
                        {point.value.toFixed(2)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </Panel>

        {/* 탭과 테이블 */}
        <Panel className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            {/* 탭 그룹 */}
            <FilterGroup
              items={BACKTEST_RESULT_TABS}
              activeId={activeTab}
              onChange={setActiveTab}
            />
          </div>

          {/* 탭 컨텐츠 */}
          {renderTabContent()}
        </Panel>
      </div>
    </div>
  );
}
