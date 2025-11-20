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

import { useEffect, useState, useRef } from "react";
import { getBacktestStatus, getBacktestResult } from "@/lib/api/backtest";
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

  // Ref로 폴링 인터벌 관리
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * 백테스트 상태 폴링
   */
  const pollBacktestStatus = async () => {
    try {
      const status = await getBacktestStatus(backtestId);

      // 진행률 업데이트
      if (status.progress !== undefined && status.progress !== null) {
        setProgress(status.progress);
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
      if (status.yieldPoints && status.yieldPoints.length > 0) {
        setYieldPoints(status.yieldPoints);
      }

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
      } else if (status.status === "failed") {
        // 폴링 중지
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
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
  };

  /**
   * 백테스트 시작 (마운트 시 자동 실행)
   */
  useEffect(() => {
    setPhase("loading");

    // 즉시 첫 폴링 실행
    pollBacktestStatus();

    // 1초마다 폴링
    pollingIntervalRef.current = setInterval(() => {
      pollBacktestStatus();
    }, 1000);

    // 언마운트 시 폴링 중지
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [backtestId]);

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

    // 폴링 재시작
    setTimeout(() => {
      setPhase("loading");
      pollBacktestStatus();
      pollingIntervalRef.current = setInterval(() => {
        pollBacktestStatus();
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
            elapsedTime: 0,
            estimatedRemainingTime: 0,
          },
        }}
      />
    );
  }

  /**
   * 완료 상태 렌더링
   */
  if (phase === "completed" && finalResult) {
    return (
      <BacktestResultView
        userName={userName}
        strategyName={strategyName}
        config={config}
        result={{
          backtestId: finalResult.id,
          statistics: finalResult.statistics,
          allYieldPoints: finalResult.yieldPoints || [],
          periodReturns: (finalResult.yieldPoints || []).map(p => ({ label: p.date, value: p.value })),
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
