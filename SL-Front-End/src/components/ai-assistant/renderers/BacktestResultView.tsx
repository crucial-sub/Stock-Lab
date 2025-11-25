/**
 * 백테스트 결과 뷰 컴포넌트
 *
 * 백테스트 완료 후 최종 결과를 표시하는 메인 컴포넌트입니다.
 * - 전략명 헤더
 * - 통계 섹션 (주요 지표)
 * - 차트 섹션 (5가지 차트 탭)
 * - 마크다운 요약
 * - 포트폴리오 저장 버튼
 *
 * 참조: 2025-01-19-ai-assistant-backtest-execution-plan.md 섹션 8.5
 */

"use client";

import { StatMetric } from "@/components/quant/result/common";
import type { BacktestResult } from "@/types/api";
import { PeriodReturnsBar } from "./PeriodReturnsBar";
import { SavePortfolioButton } from "./SavePortfolioButton";
import { SummaryMarkdown } from "./SummaryMarkdown";

/**
 * 백테스트 완료 데이터 타입
 */
export interface BacktestCompleteData {
  /** 백테스트 ID */
  backtestId: string;
  /** 통계 정보 */
  statistics: BacktestResult["statistics"];
  /** 전체 수익률 포인트 */
  allYieldPoints: BacktestResult["yieldPoints"];
  /** 기간별 수익률 */
  periodReturns: Array<{ label: string; value: number }>;
  /** 연도별 수익률 */
  yearlyReturns?: Array<{ year: string; return: number }>;
  /** 월별 수익률 */
  monthlyReturns?: Array<{ month: string; return: number }>;
  /** 종목별 수익률 */
  stockWiseReturns?: Array<{ stockName: string; return: number }>;
  /** 총 자산 데이터 */
  totalAssetsData?: Array<{ date: string; totalAssets: number }>;
  /** AI 요약 */
  summary: string;
}

/**
 * BacktestResultView Props
 */
interface BacktestResultViewProps {
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
  /** 백테스트 완료 데이터 */
  result: BacktestCompleteData;
}

/**
 * 백테스트 결과 뷰 컴포넌트
 *
 * 백테스트가 완료되면 표시되는 최종 결과 화면입니다.
 * - 헤더: 사용자명_전략명
 * - 통계 섹션: 주요 지표 (총 수익률, 연환산 수익률, MDD 등)
 * - 차트 섹션: 5가지 차트를 탭으로 전환하며 표시
 * - 마크다운 요약: AI가 생성한 백테스트 분석 요약
 * - 저장 버튼: 포트폴리오로 저장
 *
 * @example
 * ```tsx
 * function BacktestExecution() {
 *   const { state } = useBacktestStream(config);
 *
 *   if (state.phase === 'completed' && state.finalResult) {
 *     return (
 *       <BacktestResultView
 *         userName="홍길동"
 *         strategyName="성장주 전략"
 *         config={config}
 *         result={state.finalResult}
 *       />
 *     );
 *   }
 * }
 * ```
 */
export function BacktestResultView({
  userName,
  strategyName,
  config,
  result,
}: BacktestResultViewProps) {
  const { statistics, periodReturns, backtestId, summary } = result;

  // 실제 데이터 기반 계산
  const totalProfit = (statistics.finalCapital || statistics.initialCapital) - statistics.initialCapital;
  const finalAssets = statistics.finalCapital || statistics.initialCapital;

  // 일 평균 수익률 계산 (CAGR 기반, 연간 252 거래일 기준)
  // 공식: (1 + CAGR)^(1/252) - 1
  const dailyReturn =
    ((1 + statistics.annualizedReturn / 100) ** (1 / 252) - 1) * 100;

  const formatSignedPercent = (value: number, fractionDigits = 2) => {
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(fractionDigits)}%`;
  };

  const formatCurrency = (value: number) =>
    `${Math.round(value).toLocaleString()}원`;

  const formatSignedCurrency = (value: number) => {
    const rounded = Math.round(value);
    const sign = rounded > 0 ? "+" : rounded < 0 ? "" : "";
    return `${sign}${rounded.toLocaleString()}원`;
  };

  const getTone = (
    value: number,
  ): "positive" | "negative" | "neutral" => {
    if (value > 0) return "positive";
    if (value < 0) return "negative";
    return "neutral";
  };

  return (
    <>
      <div>
        <span className="text-[1.5rem] font-semibold text-black">
          🎯 백테스트 결과
        </span>
        <p className="text-[1rem] text-muted mt-1">
          백테스트가 완료되었어요.
        </p>
        <p className="text-[1rem] text-muted mt-1">
          AI가 요약한 결과를 확인해보시고, 내 포트폴리오로 저장해보세요!
        </p>

      </div>

      <div className="w-full max-w-[1000px] mx-auto space-y-5 pt-10 px-5 bg-[#1822340D] border-[0.5px] border-[#18223433] rounded-[12px] shadow-elev-card-soft">
        {/* 1. 헤더 - 사용자명 + 전략명 */}
        <div className="text-center border-b border-[#18223433] pb-10">
          <span className="text-[1.5rem] font-semibold text-black">
            {userName}_{strategyName}
          </span>
          <p className="text-[0.875rem] text-muted mt-1">
            백테스트 기간: {config.startDate} ~ {config.endDate} | 투자 금액: {statistics.initialCapital.toLocaleString()}원
          </p>
        </div>

        {/* 2. 통계 섹션 */}
        <section>

          <div className="mt-3" />
          <div className="flex flex-col gap-5">
            <span className="text-[1.25rem] font-semibold">
              🗂️ 주요 통계
            </span>

            {/* 상단 주요 지표 */}
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <StatMetric
                label="일 평균 수익률"
                value={formatSignedPercent(dailyReturn, 3)}
                tone={getTone(dailyReturn)}
                tooltip="일별 평균 수익률 (연간 252 거래일 기준)"
              />
              <StatMetric
                label="누적 수익률"
                value={formatSignedPercent(statistics.totalReturn)}
                tone={getTone(statistics.totalReturn)}
                tooltip="전체 기간 누적 수익률"
              />
              <StatMetric
                label="CAGR"
                value={formatSignedPercent(statistics.annualizedReturn)}
                tone={getTone(statistics.annualizedReturn)}
                tooltip="연평균 복리 수익률"
              />
              <StatMetric
                label="MDD"
                value={`${Math.abs(statistics.maxDrawdown).toFixed(2)}%`}
                tone="neutral"
                tooltip="최대 낙폭 (Maximum Drawdown)"
              />
            </div>

            {/* 하단 자산 정보 */}
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <StatMetric label="투자 원금" value={formatCurrency(statistics.initialCapital)} />
              <StatMetric
                label="총 손익"
                value={formatSignedCurrency(totalProfit)}
                tone={getTone(totalProfit)}
                tooltip="총 수익금 (최종 자산 - 투자 원금)"
              />
              <StatMetric
                label="현재 총 자산"
                value={formatCurrency(finalAssets)}
              />
            </div>
          </div>
        </section>

        {/* 3. 기간별 수익률 막대 차트 */}
        <section>
          <PeriodReturnsBar periodReturns={periodReturns} />
        </section>

        {/* 4. 마크다운 요약 */}
        <section>
          <SummaryMarkdown summary={summary} />
        </section>

        {/* 5. 포트폴리오 저장 버튼 */}
        <section className="flex justify-center pt-4 border-t border-gray-200">
          <SavePortfolioButton backtestId={backtestId} strategyName={strategyName} />
        </section>
      </div>
    </>
  );
}
