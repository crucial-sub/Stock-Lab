"use client";

import { BacktestLoadingChart } from "./BacktestLoadingChart";
import { formatDuration } from "@/lib/date-utils";

/**
 * 백테스트 누적 데이터 타입
 */
interface AccumulatedData {
  /** 수익률 포인트 배열 */
  yieldPoints: Array<{
    date: string;
    buyCount?: number;
    sellCount?: number;
    cumulativeReturn?: number;
  }>;
  /** 통계 정보 */
  statistics: {
    /** 현재 누적 수익률 */
    currentReturn: number;
    /** 경과 시간 (초) */
    elapsedTime: number;
    /** 예상 남은 시간 (초) */
    estimatedRemainingTime: number;
  };
}

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
    currentReturn >= 0 ? "text-price-up" : "text-price-down";
  const returnPrefix = currentReturn >= 0 ? "+" : "";

  return (
    <div className="w-full max-w-[1000px] mx-auto space-y-10 p-5 bg-[#1822340D] rounded-[12px] border-[0.5px] border-[#18223433]">
      {/* 1. 헤더 - 사용자명 + 전략명 */}
      <div className="text-center">
        <h2 className="text-[1.25rem] font-semibold text-black">
          {userName}_{strategyName}
        </h2>
      </div>

      {/* 2. 서브 정보 - 누적 수익률, 진행시간, 예상시간 */}
      <div className="flex justify-around items-center text-[0.875rem] font-normal border-b border-muted pb-5">
        {/* 누적 수익률 */}
        <div className="flex flex-col items-center">
          <span className="text-muted">누적 수익률</span>
          <span className={`text-[1.125rem] font-semibold ${returnColor}`}>
            {returnPrefix}
            {(currentReturn || 0).toFixed(2)}%
          </span>
        </div>

        {/* 진행 시간 */}
        <div className="flex flex-col items-center">
          <span className="text-muted">진행 시간</span>
          <span className="text-[1.125rem] font-semibold text-black">
            {formatDuration(elapsedTime)}
          </span>
        </div>

        {/* 예상 시간 */}
        <div className="flex flex-col items-center">
          <span className="text-muted">예상 시간</span>
          <span className="text-[1.125rem] font-semibold text-black">
            {formatDuration(estimatedRemainingTime)}
          </span>
        </div>
      </div>

      {/* 3. 진행률 바 */}
      <div className="space-y-2">
        <div className="flex justify-between items-center text-[0.875rem]">
          <span className="text-muted font-normal">백테스트 진행 중</span>
          <span className="text-brand-purple font-semibold">{progress}%</span>
        </div>

        <div className="relative h-2 bg-white/40 rounded-full overflow-hidden">
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
      <BacktestLoadingChart
        startDate={config.startDate}
        endDate={config.endDate}
        accumulatedYieldPoints={yieldPoints}
        progress={progress}
      />

      {/* 5. 진행 상태 메시지 */}
      <div className="text-center text-[0.875rem] text-muted font-normal">
        <p>
          백테스트 결과를 실시간으로 계산하고 있습니다.
          <br />
          잠시만 기다려 주세요.
        </p>
      </div>
    </div>
  );
}
