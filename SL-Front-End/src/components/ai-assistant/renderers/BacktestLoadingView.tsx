"use client";

import { BacktestLoadingChart } from "./BacktestLoadingChart";
import { formatDuration } from "@/lib/date-utils";
import type { AccumulatedData } from "@/hooks/useBacktestStream";

/**
 * BacktestLoadingView Props
 */
interface BacktestLoadingViewProps {
  /** 사용자명 */
  userName: string;
  /** 전략명 */
  strategyName: string;
  /** 백테스트 설정 */
  config: {
    initialCapital: number;
    startDate: string;
    endDate: string;
  };
  /** 진행률 (0-100) */
  progress: number;
  /** 누적 데이터 */
  accumulatedData: AccumulatedData;
}

/**
 * 백테스트 로딩 뷰 컴포넌트
 *
 * - 진행률 헤더 (사용자명 + 전략명)
 * - 진행률 통계 (누적 수익률, 진행 시간, 예상 시간)
 * - 진행률 바 (bg-brand-purple)
 * - 실시간 차트 (BacktestLoadingChart)
 */
export function BacktestLoadingView({
  userName,
  strategyName,
  config,
  progress,
  accumulatedData,
}: BacktestLoadingViewProps) {
  const { statistics, yieldPoints } = accumulatedData;
  const { currentReturn, elapsedTime, estimatedRemainingTime } = statistics;

  // 수익률 색상 결정 (양수: 빨간색, 음수: 파란색)
  const returnColor =
    currentReturn >= 0 ? "text-red-500" : "text-blue-500";
  const returnPrefix = currentReturn >= 0 ? "+" : "";

  return (
    <div className="w-full max-w-[900px] mx-auto space-y-6 p-6 bg-white rounded-lg shadow-card">
      {/* 1. 헤더 - 사용자명 + 전략명 */}
      <div className="text-center">
        <h2 className="text-xl font-bold text-gray-900">
          {userName}_{strategyName}
        </h2>
      </div>

      {/* 2. 서브 정보 - 누적 수익률, 진행시간, 예상시간 */}
      <div className="flex justify-around items-center text-sm border-b border-gray-200 pb-4">
        {/* 누적 수익률 */}
        <div className="flex flex-col items-center">
          <span className="text-gray-500 mb-1">누적 수익률</span>
          <span className={`text-lg font-bold ${returnColor}`}>
            {returnPrefix}
            {currentReturn.toFixed(2)}%
          </span>
        </div>

        {/* 진행 시간 */}
        <div className="flex flex-col items-center">
          <span className="text-gray-500 mb-1">진행 시간</span>
          <span className="text-lg font-semibold text-gray-900">
            {formatDuration(elapsedTime)}
          </span>
        </div>

        {/* 예상 시간 */}
        <div className="flex flex-col items-center">
          <span className="text-gray-500 mb-1">예상 시간</span>
          <span className="text-lg font-semibold text-gray-900">
            {formatDuration(estimatedRemainingTime)}
          </span>
        </div>
      </div>

      {/* 3. 진행률 바 */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-700 font-medium">백테스트 진행 중</span>
          <span className="text-brand-purple font-bold">{progress}%</span>
        </div>

        <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-purple transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            role="progressbar"
          />
        </div>
      </div>

      {/* 4. 실시간 차트 */}
      <div className="border border-gray-200 rounded-lg p-4">
        <BacktestLoadingChart
          startDate={config.startDate}
          endDate={config.endDate}
          accumulatedYieldPoints={yieldPoints}
          progress={progress}
        />
      </div>

      {/* 5. 진행 상태 메시지 */}
      <div className="text-center text-sm text-gray-500">
        <p>
          백테스트 결과를 실시간으로 계산하고 있습니다.
          <br />
          잠시만 기다려 주세요.
        </p>
      </div>
    </div>
  );
}
