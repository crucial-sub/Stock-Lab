"use client";

/**
 * 백테스트 로딩 상태 컴포넌트
 * - 백테스트가 실행 중일 때 표시되는 UI
 * - 진행률, 통계, 차트 표시
 * - TradingActivityChart 재사용
 */

import { TradingActivityChart } from "./TradingActivityChart";

interface BacktestLoadingStateProps {
  backtestId: string;
  status: "pending" | "running";
  progress: number;
  buyCount?: number;
  sellCount?: number;
  currentReturn?: number;
  currentCapital?: number;
  currentDate?: string;
  currentMdd?: number;
  startDate?: string;  // YYYY-MM-DD
  endDate?: string;    // YYYY-MM-DD
  yieldPoints?: Array<{
    date: string;
    buyCount?: number;
    sellCount?: number;
    cumulativeReturn?: number;
  }>;
}

export function BacktestLoadingState({
  backtestId,
  status,
  progress,
  buyCount,
  sellCount,
  currentReturn,
  currentCapital,
  currentDate,
  currentMdd,
  startDate,
  endDate,
  yieldPoints,
}: BacktestLoadingStateProps) {
  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto space-y-6">
        {/* 헤더 영역 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-accent-error">
                {backtestId}
              </h1>
              <p className="text-sm text-text-body mt-1">
                {status === "pending"
                  ? "백테스트 대기 중..."
                  : "백테스트 실행 중..."}
              </p>
              {currentDate && (
                <p className="text-xs text-text-muted mt-1">
                  현재 처리 중: {currentDate}
                </p>
              )}
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-accent-primary">
                {progress}%
              </div>
              <div className="text-sm text-text-body">진행률</div>
            </div>
          </div>

          {/* 진행률 바 */}
          <div className="mt-4">
            <div className="w-full bg-bg-app rounded-full h-2 overflow-hidden">
              <div
                className="bg-accent-primary h-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* 실시간 통계 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="grid grid-cols-5 gap-4">
            {/* 누적 수익률 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">누적 수익률</div>
              {currentReturn !== undefined && currentReturn !== null ? (
                <div
                  className={`text-2xl font-bold ${currentReturn >= 0 ? "text-red-500" : "text-blue-500"
                    }`}
                >
                  {currentReturn > 0 ? "+" : ""}
                  {currentReturn.toFixed(2)}%
                </div>
              ) : (
                <div className="animate-pulse">
                  <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
                </div>
              )}
            </div>

            {/* MDD */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">MDD</div>
              {currentMdd !== undefined && currentMdd !== null ? (
                <div className={`text-2xl font-bold ${currentMdd >= 0 ? "text-accent-error" : "text-blue-500"
                  }`}>
                  {currentMdd.toFixed(2)}%
                </div>
              ) : (
                <div className="animate-pulse">
                  <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
                </div>
              )}
            </div>

            {/* 현재 자본금 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">현재 자본</div>
              {currentCapital !== undefined ? (
                <div className="text-2xl font-bold text-text-heading">
                  {Math.round(currentCapital).toLocaleString()}원
                </div>
              ) : (
                <div className="animate-pulse">
                  <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
                </div>
              )}
            </div>

            {/* 전체시간 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">전체시간</div>
              {currentDate ? (
                <div className="text-2xl font-bold text-text-heading">
                  {currentDate}
                </div>
              ) : (
                <div className="animate-pulse">
                  <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
                </div>
              )}
            </div>

            {/* 예상시간 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">예상시간</div>
              <div className="animate-pulse">
                <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
              </div>
            </div>
          </div>
        </div>

        {/* 차트 영역 */}
        {yieldPoints && yieldPoints.length > 0 && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6">
            <h2 className="text-lg font-bold text-text-strong mb-4">매수/매도 활동</h2>
            <TradingActivityChart
              yieldPoints={yieldPoints}
              startDate={startDate}
              endDate={endDate}
            />
          </div>
        )}
      </div>
    </div>
  );
}