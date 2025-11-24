/**
 * 백테스트 상태 통합 훅
 *
 * WebSocket 기반 실시간 백테스트 상태 관리 훅
 * - AI Assistant와 전략 포트폴리오 페이지에서 재사용
 * - WebSocket 데이터를 React Query로 캐싱
 * - 일관된 상태 관리 인터페이스 제공
 */

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useBacktestWebSocket } from "./useBacktestWebSocket";
import { backtestQueryKey } from "./useBacktestQuery";
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

  // 백테스트 상태 계산
  const status: BacktestStatusType = wsError
    ? "error"
    : wsIsCompleted
    ? "completed"
    : wsProgress > 0
    ? "running"
    : "pending";

  // WebSocket 데이터에서 현재 값들 계산
  const latestData = chartData.length > 0 ? chartData[chartData.length - 1] : null;

  const currentReturn = latestData?.cumulativeReturn;
  const currentCapital = latestData?.portfolioValue;
  const currentDate = latestData?.date;
  const currentMdd = latestData?.currentMdd;
  const buyCount = latestData?.buyCount;
  const sellCount = latestData?.sellCount;

  // WebSocket 데이터를 React Query 캐시에 동기화
  // 다른 컴포넌트에서 캐시된 데이터를 활용할 수 있도록
  useEffect(() => {
    if (!backtestId || !isConnected) return;

    // 상태 데이터를 캐시에 저장
    queryClient.setQueryData(
      backtestQueryKey.status(backtestId),
      {
        status,
        progress: wsProgress,
        chartData,
        currentReturn,
        currentCapital,
        currentDate,
        currentMdd,
        buyCount,
        sellCount,
        isCompleted: wsIsCompleted,
        error: wsError,
      }
    );
  }, [
    backtestId,
    isConnected,
    status,
    wsProgress,
    chartData,
    currentReturn,
    currentCapital,
    currentDate,
    currentMdd,
    buyCount,
    sellCount,
    wsIsCompleted,
    wsError,
    queryClient,
  ]);

  return {
    status,
    progress: wsProgress,
    chartData,
    isConnected,
    isCompleted: wsIsCompleted,
    error: wsError,
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
