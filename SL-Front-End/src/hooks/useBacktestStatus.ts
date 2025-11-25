/**
 * 백테스트 상태 통합 훅
 *
 * WebSocket 기반 실시간 백테스트 상태 관리 훅
 * - AI Assistant와 전략 포트폴리오 페이지에서 재사용
 * - WebSocket 데이터를 React Query로 캐싱
 * - 일관된 상태 관리 인터페이스 제공
 */

import { useEffect, useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useBacktestWebSocket } from "./useBacktestWebSocket";
import {
  backtestQueryKey,
  useBacktestStatusQuery,
} from "./useBacktestQuery";
import type { ChartDataPoint } from "./useBacktestWebSocket";

/**
 * 백테스트 상태 타입
 */
export type BacktestStatusType = "pending" | "running" | "completed" | "failed" | "error";

/**
 * 백테스트 상태 훅 반환 타입
 */
export interface UseBacktestStatusReturn {
  /** 백테스트 상태 */
  status: BacktestStatusType;
  /** 진행률 (0-100) */
  progress: number;
  /** 차트 데이터 */
  chartData: ChartDataPoint[];
  /** WebSocket 연결 상태 */
  isConnected: boolean;
  /** 완료 여부 */
  isCompleted: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 최종 통계 */
  statistics: any | null;
  /** AI 요약 (마크다운) */
  summary: string | null;
  /** 현재 수익률 (%) */
  currentReturn: number | undefined;
  /** 현재 포트폴리오 가치 */
  currentCapital: number | undefined;
  /** 현재 처리 중인 날짜 */
  currentDate: string | undefined;
  /** 현재 MDD (%) */
  currentMdd: number | undefined;
  /** 당일 매수 횟수 */
  buyCount: number | undefined;
  /** 당일 매도 횟수 */
  sellCount: number | undefined;
}

/**
 * 백테스트 상태 통합 훅
 *
 * WebSocket을 통해 실시간으로 백테스트 상태를 추적하고
 * React Query 캐시와 동기화합니다.
 *
 * @param backtestId - 백테스트 ID
 * @param enabled - 훅 활성화 여부 (기본: true)
 * @returns 백테스트 상태 및 데이터
 *
 * @example
 * ```tsx
 * const { status, progress, chartData, isCompleted } = useBacktestStatus(backtestId);
 *
 * if (status === "running") {
 *   return <BacktestLoadingState progress={progress} chartData={chartData} />;
 * }
 *
 * if (status === "completed") {
 *   return <BacktestResultView />;
 * }
 * ```
 */
export function useBacktestStatus(
  backtestId: string | null,
  enabled = true
): UseBacktestStatusReturn {
  const queryClient = useQueryClient();

  // API 상태 단발 조회 (WebSocket 연결 실패/완료된 세션 접속 시 폴백)
  const { data: apiStatus } = useBacktestStatusQuery(
    backtestId ?? "",
    enabled && !!backtestId,
    false, // WebSocket 사용 시 폴링 비활성화
  );

  // WebSocket 연결 및 실시간 데이터 수신
  const {
    isConnected,
    chartData,
    progress: wsProgress,
    isCompleted: wsIsCompleted,
    error: wsError,
    statistics,
    summary,
  } = useBacktestWebSocket(backtestId, enabled);

  // API에서 받은 차트/진행률 폴백 데이터
  const fallbackChartData: ChartDataPoint[] = useMemo(() => {
    if (!apiStatus?.yieldPoints) return [];
    return apiStatus.yieldPoints.map((point) => ({
      date: point.date,
      portfolioValue: point.portfolioValue ?? point.value ?? 0,
      cumulativeReturn: point.cumulativeReturn ?? point.value ?? 0,
      dailyReturn: point.dailyReturn ?? 0,
      currentMdd: point.currentMdd ?? 0,
      buyCount: point.buyCount ?? 0,
      sellCount: point.sellCount ?? 0,
    }));
  }, [apiStatus?.yieldPoints]);

  const mergedChartData = chartData.length > 0 ? chartData : fallbackChartData;

  const apiCompleted = apiStatus?.status === "completed";
  const apiFailed = apiStatus?.status === "failed";

  // 진행률 계산 (WebSocket > API > 기본값)
  const mergedProgress =
    wsProgress > 0 ? wsProgress : apiStatus?.progress ?? 0;

  // 백테스트 상태 계산
  const status: BacktestStatusType = apiFailed
    ? "failed"
    : wsError && !apiCompleted
    ? "error"
    : wsIsCompleted || apiCompleted
    ? "completed"
    : mergedProgress > 0 || apiStatus?.status === "running"
    ? "running"
    : "pending";

  const mergedError =
    status === "failed"
      ? apiStatus?.errorMessage || "백테스트 실행에 실패했습니다."
      : status === "error"
      ? wsError
      : null;

  const mergedIsCompleted = wsIsCompleted || apiCompleted;

  // WebSocket 데이터에서 현재 값들 계산
  const latestData = mergedChartData.length > 0 ? mergedChartData[mergedChartData.length - 1] : null;

  const currentReturn = latestData?.cumulativeReturn ?? apiStatus?.currentReturn;
  const currentCapital = latestData?.portfolioValue ?? apiStatus?.currentCapital;
  const currentDate = latestData?.date ?? apiStatus?.currentDate;
  const currentMdd = latestData?.currentMdd ?? apiStatus?.currentMdd;
  const buyCount = latestData?.buyCount ?? apiStatus?.buyCount;
  const sellCount = latestData?.sellCount ?? apiStatus?.sellCount;

  // WebSocket 데이터를 React Query 캐시에 동기화
  // 다른 컴포넌트에서 캐시된 데이터를 활용할 수 있도록
  useEffect(() => {
    if (!backtestId || (!isConnected && !apiStatus)) return;

    // 상태 데이터를 캐시에 저장
    queryClient.setQueryData(
      backtestQueryKey.status(backtestId),
      {
        status,
        progress: mergedProgress,
        chartData: mergedChartData,
        currentReturn,
        currentCapital,
        currentDate,
        currentMdd,
        buyCount,
        sellCount,
        isCompleted: mergedIsCompleted,
        error: mergedError,
      }
    );
  }, [
    backtestId,
    isConnected,
    status,
    mergedProgress,
    mergedChartData,
    currentReturn,
    currentCapital,
    currentDate,
    currentMdd,
    buyCount,
    sellCount,
    mergedIsCompleted,
    mergedError,
    apiStatus,
    queryClient,
  ]);

  return {
    status,
    progress: mergedProgress,
    chartData: mergedChartData,
    isConnected,
    isCompleted: mergedIsCompleted,
    error: mergedError,
    statistics,
    summary,
    currentReturn,
    currentCapital,
    currentDate,
    currentMdd,
    buyCount,
    sellCount,
  };
}
