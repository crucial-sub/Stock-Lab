/**
 * 백테스트 실행 및 결과 렌더링 메인 컴포넌트
 *
 * AI 어시스턴트 채팅에서 백테스트 실행을 담당하는 최상위 컴포넌트입니다.
 * - WebSocket을 통한 실시간 진행 상황 확인
 * - 로딩 UI → 결과 UI 자동 전환
 * - 상태 관리 및 에러 처리
 * - 마운트 시 자동 시작
 */

"use client";

import { useEffect, useState, useRef } from "react";
import { useBacktestStatus } from "@/hooks/useBacktestStatus";
import { BacktestLoadingState } from "@/components/quant/result/BacktestLoadingState";
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
 *   - loading: 진행 중 UI (BacktestLoadingState)
 *   - completed: 완료 UI (BacktestResultView)
 *   - error: 에러 UI + 재시도 버튼
 */
export function BacktestExecutionRenderer({
  backtestId,
  strategyName,
  userName,
  config,
}: BacktestExecutionRendererProps) {
  // 🚀 통합 백테스트 상태 훅 사용
  const {
    status: backtestStatus,
    progress,
    chartData,
    isCompleted,
    error: wsError,
    statistics: wsStatistics,
    summary: wsSummary,
    currentReturn,
    currentCapital,
    currentDate,
    currentMdd,
    buyCount,
    sellCount,
  } = useBacktestStatus(backtestId, true);

  // UI 상태 관리
  const [phase, setPhase] = useState<BacktestPhase>("idle");
  const [finalResult, setFinalResult] = useState<BacktestResult | null>(null);

  // 시간 추적을 위한 상태 추가
  const startTimeRef = useRef<number | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const tickingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // yieldPoints 형식 변환 (차트 컴포넌트용)
  const yieldPoints = chartData.map(point => ({
    date: point.date,
    cumulativeReturn: point.cumulativeReturn,
    buyCount: point.buyCount,
    sellCount: point.sellCount,
  }));

  // 🚀 백테스트 상태에 따른 UI 업데이트
  useEffect(() => {
    console.log("📡 [BacktestExecutionRenderer] 백테스트 상태:", {
      status: backtestStatus,
      progress,
      chartDataLength: chartData.length,
      isCompleted,
    });

    // 실패 또는 에러 상태 처리
    if (backtestStatus === "failed" || backtestStatus === "error") {
      setPhase("error");
      return;
    }

    // 시간 추적 시작 (위에서 failed/error는 이미 return 처리됨)
    if (!startTimeRef.current) {
      startTimeRef.current = Date.now();
    }

    // 상태에 따른 phase 업데이트
    if (wsError) {
      setPhase("error");
    } else if (progress > 0 && progress < 100) {
      setPhase("loading");
    } else if (progress === 0) {
      setPhase("loading");
    }
  }, [backtestStatus, progress, chartData.length, isCompleted, wsError]);

  // 초 단위 부드러운 시간 갱신용 로컬 타이머
  useEffect(() => {
    if (phase === "loading") {
      tickingIntervalRef.current = setInterval(() => {
        if (!startTimeRef.current) return;
        const now = Date.now();
        const elapsed = now - startTimeRef.current;
        setElapsedTime(elapsed);
      }, 1000);
    }

    return () => {
      if (tickingIntervalRef.current) {
        clearInterval(tickingIntervalRef.current);
        tickingIntervalRef.current = null;
      }
    };
  }, [phase]);

  // 🚀 백테스트 완료 처리 (WebSocket 데이터만 사용)
  useEffect(() => {
    if (!isCompleted) {
      console.log("⏳ [BacktestExecutionRenderer] 아직 완료되지 않음:", { isCompleted, wsStatistics, chartDataLength: chartData.length });
      return;
    }

    if (!wsStatistics) {
      console.error("⚠️ [BacktestExecutionRenderer] wsStatistics가 없음! chartData로 대체 시도");
      console.log("📊 chartData:", chartData.length, "포인트");
    }

    console.log("✅ 백테스트 완료 감지, WebSocket 데이터 사용");
    console.log("📊 [BacktestExecutionRenderer] WebSocket statistics:", wsStatistics);
    console.log("📊 [BacktestExecutionRenderer] WebSocket summary:", wsSummary?.length || 0, "글자");
    console.log("📊 [BacktestExecutionRenderer] chartData:", chartData.length, "포인트");

    // ✅ chartData에서 statistics 계산 (fallback)
    const lastDataPoint = chartData.length > 0 ? chartData[chartData.length - 1] : null;

    // 기간 계산
    const startDateObj = new Date(config.startDate);
    const endDateObj = new Date(config.endDate);
    const totalDays = Math.floor((endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60 * 24));
    const years = totalDays / 365.0;

    const finalValue = lastDataPoint?.portfolioValue || config.initialCapital;
    const totalReturn = lastDataPoint?.cumulativeReturn || 0;

    // CAGR 계산: (최종값/초기값)^(1/년수) - 1
    const cagr = years > 0 ? (Math.pow(finalValue / config.initialCapital, 1 / years) - 1) * 100 : 0;

    const calculatedStats = {
      total_return: totalReturn,
      final_value: finalValue,
      annualized_return: cagr,
      max_drawdown: Math.min(...chartData.map(d => d.currentMdd || 0)),
      total_trades: chartData.reduce((sum, d) => sum + (d.buyCount || 0) + (d.sellCount || 0), 0),
    };

    // wsStatistics가 있으면 사용, 없으면 계산된 값 사용
    const finalStats = wsStatistics || calculatedStats;

    console.log("📊 [BacktestExecutionRenderer] 최종 사용 statistics:", finalStats);

    // ✅ WebSocket 데이터를 BacktestResult 형식으로 변환
    const convertedResult: BacktestResult = {
      id: backtestId,
      status: "completed",
      statistics: {
        totalReturn: finalStats.total_return,
        annualizedReturn: finalStats.annualized_return || 0,
        sharpeRatio: 0,
        maxDrawdown: finalStats.max_drawdown,
        winRate: 0,
        profitFactor: 0,
        volatility: 0,
        totalTrades: finalStats.total_trades,
        winningTrades: 0,
        losingTrades: 0,
        initialCapital: config.initialCapital,
        finalCapital: finalStats.final_value,
      },
      trades: [],
      yieldPoints: chartData.map(point => ({
        date: point.date,
        value: point.portfolioValue,
        portfolioValue: point.portfolioValue,
        cumulativeReturn: point.cumulativeReturn,
        dailyReturn: point.dailyReturn,
        buyCount: point.buyCount,
        sellCount: point.sellCount,
      })),
      summary: wsSummary || undefined,
      createdAt: new Date().toISOString(),
    };

    console.log("✅ [BacktestExecutionRenderer] 변환된 결과:", convertedResult);
    setFinalResult(convertedResult);
    setPhase("completed");
  }, [isCompleted, wsStatistics, wsSummary, chartData, backtestId, config.initialCapital]);

  /**
   * 백테스트 시작 (마운트 시 초기 상태 설정)
   */
  useEffect(() => {
    setPhase("loading");
  }, [backtestId]);

  /**
   * 재시도 함수 - 페이지 새로고침으로 재시작
   */
  const handleRetry = () => {
    window.location.reload();
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
            {wsError ||
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
    const loadingStatus = progress > 0 ? "running" : "pending";

    return (
      <BacktestLoadingState
        backtestId={backtestId}
        strategyName={strategyName}
        status={loadingStatus}
        progress={progress}
        buyCount={buyCount}
        sellCount={sellCount}
        currentReturn={currentReturn}
        currentCapital={currentCapital}
        currentDate={currentDate}
        currentMdd={currentMdd}
        initialCapital={config.initialCapital}
        startDate={config.startDate}
        endDate={config.endDate}
        elapsedTime={elapsedTime}
        yieldPoints={yieldPoints}
        webSocketEnabled={true}
      />
    );
  }

  /**
   * 완료 상태 렌더링
   */
  if (phase === "completed" && finalResult) {
    // 기간별 수익률 계산
    const calculatePeriodReturns = () => {
      // ✅ API 응답에 yieldPoints가 없으면 WebSocket chartData 사용
      const dataPoints = finalResult.yieldPoints && finalResult.yieldPoints.length > 0
        ? finalResult.yieldPoints
        : yieldPoints;

      console.log("📊 [calculatePeriodReturns] 데이터 소스:", {
        apiYieldPoints: finalResult.yieldPoints?.length || 0,
        chartDataYieldPoints: yieldPoints.length,
        using: dataPoints === finalResult.yieldPoints ? "API" : "WebSocket chartData"
      });

      if (!dataPoints || dataPoints.length === 0) {
        console.warn("⚠️ [calculatePeriodReturns] 데이터가 없습니다!");
        return [];
      }

      const sortedPoints = [...dataPoints].sort(
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
      console.log("📊 [calculatePeriodReturns] 백테스트 기간 정보:", {
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
      if (totalDays >= 350) {
        // 350일 이상이면 "최근 1년" 표시 (거래일 기준으로 약간의 여유 허용)
        periods.push({ label: "최근 1년", value: latestReturn - getReturnAtDate(365) });
      }
      if (totalDays >= 700) {
        periods.push({ label: "최근 2년", value: latestReturn - getReturnAtDate(730) });
      }
      if (totalDays >= 1050) {
        periods.push({ label: "최근 3년", value: latestReturn - getReturnAtDate(1095) });
      }

      console.log("📊 [calculatePeriodReturns] 계산된 기간별 수익률:", periods);
      return periods;
    };

    // ✅ summary는 반드시 API에서 받아야 함
    const summaryText = finalResult.summary || "";

    console.log("📝 [BacktestExecutionRenderer] Summary:", {
      length: summaryText.length,
      content: summaryText,
    });

    return (
      <BacktestResultView
        userName={userName}
        strategyName={strategyName}
        config={config}
        result={{
          backtestId: finalResult.id,
          statistics: finalResult.statistics,
          allYieldPoints: finalResult.yieldPoints || yieldPoints,
          periodReturns: calculatePeriodReturns(),
          yearlyReturns: [],
          monthlyReturns: [],
          stockWiseReturns: [],
          totalAssetsData: [],
          summary: summaryText,
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
