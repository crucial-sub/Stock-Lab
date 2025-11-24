/**
 * 백테스트 실행 및 결과 렌더링 메인 컴포넌트
 *
 * AI 어시스턴트 채팅에서 백테스트 실행을 담당하는 최상위 컴포넌트입니다.
 * - 폴링을 통한 실시간 진행 상황 확인
 * - 로딩 UI → 결과 UI 자동 전환
 * - 상태 관리 및 에러 처리
 * - 마운트 시 자동 시작
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  getBacktestStatus,
  getBacktestResult,
  getBacktestYieldPoints,
} from "@/lib/api/backtest";
import { BacktestLoadingView } from "./BacktestLoadingView";
import { BacktestResultView } from "./BacktestResultView";
import type { BacktestResult } from "@/types/api";

/**
 * BacktestExecutionRenderer Props
 */
interface BacktestExecutionRendererProps {
  /** 백테스트 ID (백엔드에서 생성) */
  backtestId: string;
  /** 전략 ID */
  strategyId: string;
  /** 전략명 */
  strategyName: string;
  /** 사용자명 */
  userName: string;
  /** 백테스트 설정 */
  config: {
    /** 투자 금액 (원) */
    initialCapital: number;
    /** 시작일 (ISO 8601: YYYY-MM-DD) */
    startDate: string;
    /** 종료일 (ISO 8601: YYYY-MM-DD) */
    endDate: string;
  };
}

/**
 * 백테스트 실행 상태
 */
type BacktestPhase = "idle" | "loading" | "completed" | "error";

/**
 * 백테스트 실행 및 결과 렌더링 메인 컴포넌트
 *
 * - 컴포넌트 마운트 시 자동으로 백테스트 시작
 * - 폴링을 통한 실시간 진행 상황 확인 및 UI 업데이트
 * - 상태에 따른 조건부 렌더링:
 *   - idle: 준비 중 메시지
 *   - loading: 진행 중 UI (BacktestLoadingView)
 *   - completed: 완료 UI (BacktestResultView)
 *   - error: 에러 UI + 재시도 버튼
 */
export function BacktestExecutionRenderer({
  backtestId,
  strategyName,
  userName,
  config,
}: BacktestExecutionRendererProps) {
  // 상태 관리
  const [phase, setPhase] = useState<BacktestPhase>("idle");
  const [progress, setProgress] = useState(0);
  const [currentReturn, setCurrentReturn] = useState(0);
  const [yieldPoints, setYieldPoints] = useState<any[]>([]);
  const [finalResult, setFinalResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  // 시간 추적을 위한 상태 추가
  const startTimeRef = useRef<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [estimatedTotalTime, setEstimatedTotalTime] = useState(0);
  const lastProgressRef = useRef(0);
  const lastYieldTimestampRef = useRef<number | null>(null);

  // Ref로 폴링 인터벌 관리
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const tickingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const yieldPollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isFetchingYieldRef = useRef(false);

  /**
   * 상태/추가 API에서 받은 yieldPoints를 병합하여 누락 없이 순서대로 추가
   */
  const appendYieldPoints = useCallback((points?: any[]) => {
    if (!points || points.length === 0) return;

    const sorted = [...points]
      .map((p) => ({ ...p, _ts: new Date(p.date).getTime() }))
      .sort((a, b) => a._ts - b._ts);

    const slice = sorted.filter(
      (p) => p._ts > (lastYieldTimestampRef.current ?? -Infinity),
    );
    if (slice.length === 0) return;

    setYieldPoints((prev) => [...prev, ...slice.map(({ _ts, ...rest }) => rest)]);
    lastYieldTimestampRef.current = slice[slice.length - 1]._ts;
  }, []);

  /**
   * 백테스트 상태 폴링
   */
  const pollBacktestStatus = useCallback(async () => {
    try {
      const status = await getBacktestStatus(backtestId);

      // 진행률 값 보정 및 저장
      const progressValue =
        status.progress !== undefined && status.progress !== null
          ? Math.min(100, Math.max(0, status.progress))
          : lastProgressRef.current;

      let hasProgressChanged = false;
      if (status.progress !== undefined && status.progress !== null) {
        hasProgressChanged = progressValue !== lastProgressRef.current;
        setProgress(progressValue);
        lastProgressRef.current = progressValue;
      }

      // 시작 시간 설정 (최초 한 번만)
      if (!startTimeRef.current && status.status !== "failed") {
        startTimeRef.current = Date.now();
      }

      // 시간 계산 (progress가 정체돼 있어도 시간은 계속 증가)
      if (startTimeRef.current) {
        const currentTime = Date.now();
        const elapsed = currentTime - startTimeRef.current;
        setElapsedTime(elapsed);

        // 예상 남은 시간 계산
        if (progressValue > 0 && progressValue < 100 && hasProgressChanged) {
          const totalEstimatedTime = elapsed / (progressValue / 100);
          setEstimatedTotalTime(Math.max(elapsed, totalEstimatedTime));
        } else if (progressValue >= 100) {
          setEstimatedTotalTime(elapsed);
        }
      }

      // 현재 수익률 업데이트
      if (status.currentReturn != null) {  // null과 undefined 체크
        setCurrentReturn(status.currentReturn);
      } else if (status.yieldPoints && status.yieldPoints.length > 0) {
        // 완료 상태에서 currentReturn이 null일 때는 마지막 yieldPoint 사용
        const lastPoint = status.yieldPoints[status.yieldPoints.length - 1];
        if (lastPoint.cumulativeReturn != null) {
          setCurrentReturn(lastPoint.cumulativeReturn);
        }
      }

      // yieldPoints 업데이트
      appendYieldPoints(status.yieldPoints);

      // 상태에 따른 처리
      if (status.status === "completed") {
        // 폴링 중지
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }

        // 최종 결과 조회
        const result = await getBacktestResult(backtestId);

        setFinalResult(result);
        setPhase("completed");
        setProgress(100);
        lastProgressRef.current = 100;
        if (tickingIntervalRef.current) {
          clearInterval(tickingIntervalRef.current);
          tickingIntervalRef.current = null;
        }
        if (startTimeRef.current) {
          const doneElapsed = Date.now() - startTimeRef.current;
          setElapsedTime(doneElapsed);
          setEstimatedTotalTime(doneElapsed);
        }
      } else if (status.status === "failed") {
        // 폴링 중지
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        if (tickingIntervalRef.current) {
          clearInterval(tickingIntervalRef.current);
          tickingIntervalRef.current = null;
        }

        setError(new Error("백테스트 실행 중 오류가 발생했습니다."));
        setPhase("error");
      } else {
        // running, pending 상태는 계속 폴링
        setPhase("loading");
      }
    } catch (err) {
      // 폴링 중지
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }

      setError(err instanceof Error ? err : new Error("알 수 없는 오류가 발생했습니다."));
      setPhase("error");
    }
  }, [backtestId]);

  /**
   * 진행 중일 때 수익률 포인트를 전용 API로 주기적으로 받아와 차트와 싱크를 맞춘다.
   * 상태 응답(status) 외에 별도로 데이터를 당겨서 초기 지연을 줄임.
   */
  useEffect(() => {
    const shouldPollYield =
      phase === "loading" && lastProgressRef.current > 0 && backtestId;

    const fetchYieldPoints = async () => {
      if (!shouldPollYield || isFetchingYieldRef.current) return;
      isFetchingYieldRef.current = true;
      try {
        const res = await getBacktestYieldPoints(backtestId, {
          page: 1,
          limit: 500,
        });
        appendYieldPoints(res.data);
      } catch (err) {
        // 폴링 실패는 무시하고 다음 주기에서 재시도
        console.warn("yieldPoints polling 실패", err);
      } finally {
        isFetchingYieldRef.current = false;
      }
    };

    // 즉시 한 번 실행
    fetchYieldPoints();

    if (shouldPollYield) {
      yieldPollingIntervalRef.current = setInterval(fetchYieldPoints, 2000);
    }

    return () => {
      if (yieldPollingIntervalRef.current) {
        clearInterval(yieldPollingIntervalRef.current);
        yieldPollingIntervalRef.current = null;
      }
    };
  }, [appendYieldPoints, backtestId, phase]);

  /**
   * 백테스트 시작 (마운트 시 자동 실행)
   */
  useEffect(() => {
    setPhase("loading");
    startTimeRef.current = Date.now();
    lastProgressRef.current = 0;
    setEstimatedTotalTime(0);
    lastYieldTimestampRef.current = null;
    setYieldPoints([]);

    // 즉시 첫 폴링 실행
    pollBacktestStatus();

    // 1초마다 폴링
    pollingIntervalRef.current = setInterval(() => {
      pollBacktestStatus();
    }, 1000);

    // 초 단위 부드러운 시간 갱신용 로컬 타이머
    tickingIntervalRef.current = setInterval(() => {
      if (!startTimeRef.current) return;
      const now = Date.now();
      const elapsed = now - startTimeRef.current;
      setElapsedTime(elapsed);

      // 진행률이 아주 낮아도 전체 예상 시간은 최소 경과 시간 이상 유지
      // 예상 시간은 진행률 업데이트 시에만 갱신 (여기서는 미변경)
    }, 1000);

    // 언마운트 시 폴링 및 타이머 중지
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      if (tickingIntervalRef.current) {
        clearInterval(tickingIntervalRef.current);
        tickingIntervalRef.current = null;
      }
    };
  }, [backtestId, pollBacktestStatus]);

  /**
   * 재시도 함수
   */
  const handleRetry = () => {
    setError(null);
    setPhase("idle");
    setProgress(0);
    setCurrentReturn(0);
    setYieldPoints([]);
    setFinalResult(null);
    startTimeRef.current = null;
    setElapsedTime(0);
    setEstimatedTotalTime(0);
    lastProgressRef.current = 0;
    lastYieldTimestampRef.current = null;

    // 폴링 재시작
    setTimeout(() => {
      setPhase("loading");
      startTimeRef.current = Date.now();
      pollBacktestStatus();
      pollingIntervalRef.current = setInterval(() => {
        pollBacktestStatus();
      }, 1000);
      if (tickingIntervalRef.current) {
        clearInterval(tickingIntervalRef.current);
      }
      tickingIntervalRef.current = setInterval(() => {
        if (!startTimeRef.current) return;
        const now = Date.now();
        const elapsed = now - startTimeRef.current;
        setElapsedTime(elapsed);

        // 예상 시간은 진행률 업데이트 시에만 갱신 (여기서는 미변경)
      }, 1000);
    }, 100);
  };

  /**
   * 에러 상태 렌더링
   */
  if (phase === "error") {
    return (
      <div className="w-full max-w-[900px] mx-auto my-6">
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6 space-y-4">
          {/* 에러 헤더 */}
          <div className="flex items-center gap-2">
            <svg
              className="h-6 w-6 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="text-lg font-bold text-red-700">
              백테스트 실행 오류
            </h3>
          </div>

          {/* 에러 메시지 */}
          <p className="text-red-600 text-sm leading-relaxed">
            {error?.message ||
              "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
          </p>

          {/* 재시도 버튼 */}
          <button
            onClick={handleRetry}
            className="w-full sm:w-auto px-6 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 active:scale-95 transition-all duration-200"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  /**
   * 로딩 상태 렌더링
   */
  if (phase === "loading") {
    return (
      <BacktestLoadingView
        userName={userName}
        strategyName={strategyName}
        config={config}
        progress={progress}
        accumulatedData={{
          yieldPoints,
          statistics: {
            currentReturn,
            elapsedTime,
            estimatedTotalTime,
          },
        }}
      />
    );
  }

  /**
   * 완료 상태 렌더링
   */
  if (phase === "completed" && finalResult) {
    // 기간별 수익률 계산
    const calculatePeriodReturns = () => {
      if (!finalResult.yieldPoints || finalResult.yieldPoints.length === 0) {
        return [];
      }

      const sortedPoints = [...finalResult.yieldPoints].sort(
        (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
      );

      const latestPoint = sortedPoints[sortedPoints.length - 1];
      const firstPoint = sortedPoints[0];
      const latestReturn = latestPoint?.cumulativeReturn || 0;
      const latestDate = new Date(latestPoint.date);
      const firstDate = new Date(firstPoint.date);

      // 백테스트 전체 기간 (일 단위)
      const totalDays = Math.floor(
        (latestDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      // 디버깅: 기간 정보 출력
      console.log("백테스트 기간 정보:", {
        firstDate: firstPoint.date,
        latestDate: latestPoint.date,
        totalDays: totalDays,
        "1년 이상?": totalDays >= 365,
        "데이터 포인트 수": sortedPoints.length
      });

      // 기간별 수익률 계산 함수 (백테스트 마지막 날짜 기준)
      const getReturnAtDate = (daysAgo: number) => {
        const targetDate = new Date(latestDate);
        targetDate.setDate(targetDate.getDate() - daysAgo);

        // 목표 날짜 이전의 가장 가까운 거래일 찾기
        const closestPoint = sortedPoints
          .filter((p) => new Date(p.date) <= targetDate)
          .pop();

        return closestPoint?.cumulativeReturn || 0;
      };

      const periods = [];

      // 최근 거래일은 항상 표시
      periods.push({ label: "최근 거래일", value: latestReturn });

      // 백테스트 기간에 따라 동적으로 표시할 기간 결정
      if (totalDays >= 7) {
        periods.push({ label: "최근 일주일", value: latestReturn - getReturnAtDate(7) });
      }
      if (totalDays >= 30) {
        periods.push({ label: "최근 1개월", value: latestReturn - getReturnAtDate(30) });
      }
      if (totalDays >= 90) {
        periods.push({ label: "최근 3개월", value: latestReturn - getReturnAtDate(90) });
      }
      if (totalDays >= 180) {
        periods.push({ label: "최근 6개월", value: latestReturn - getReturnAtDate(180) });
      }
      if (totalDays >= 365) {
        periods.push({ label: "최근 1년", value: latestReturn - getReturnAtDate(365) });
      }
      if (totalDays >= 730) {
        periods.push({ label: "최근 2년", value: latestReturn - getReturnAtDate(730) });
      }
      if (totalDays >= 1095) {
        periods.push({ label: "최근 3년", value: latestReturn - getReturnAtDate(1095) });
      }

      return periods;
    };

    return (
      <BacktestResultView
        userName={userName}
        strategyName={strategyName}
        config={config}
        result={{
          backtestId: finalResult.id,
          statistics: finalResult.statistics,
          allYieldPoints: finalResult.yieldPoints || [],
          periodReturns: calculatePeriodReturns(),
          yearlyReturns: [],
          monthlyReturns: [],
          stockWiseReturns: [],
          totalAssetsData: [],
          summary: finalResult.summary || "",
        }}
      />
    );
  }

  /**
   * idle 상태 렌더링
   */
  return (
    <div className="w-full max-w-[900px] mx-auto my-6">
      <div className="text-center py-12">
        {/* 로딩 스피너 */}
        <svg
          className="animate-spin h-10 w-10 text-brand-purple mx-auto mb-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>

        <p className="text-gray-600 font-medium">백테스트 준비 중...</p>
      </div>
    </div>
  );
}
