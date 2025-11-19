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

import { StatisticsSection } from "@/components/quant/result/sections/StatisticsSection";
import { ResultChartsSection } from "./ResultChartsSection";
import { SummaryMarkdown } from "./SummaryMarkdown";
import { SavePortfolioButton } from "./SavePortfolioButton";
import type { BacktestCompleteData } from "@/hooks/useBacktestStream";

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

  return (
    <div className="w-full max-w-[900px] mx-auto space-y-8 py-6">
      {/* 1. 헤더 - 사용자명 + 전략명 */}
      <div className="text-center border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {userName}_{strategyName}
        </h1>
        <p className="text-sm text-gray-600 mt-2">
          백테스트 기간: {config.startDate} ~ {config.endDate} | 투자 금액:{" "}
          {statistics.initialCapital.toLocaleString()}원
        </p>
      </div>

      {/* 2. 통계 섹션 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          📊 주요 통계
        </h2>
        <StatisticsSection
          statistics={{
            totalReturn: statistics.totalReturn,
            annualizedReturn: statistics.annualizedReturn,
            maxDrawdown: statistics.maxDrawdown,
          }}
          initialCapital={statistics.initialCapital}
          periodReturns={periodReturns}
        />
      </section>

      {/* 3. 차트 섹션 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          📈 상세 분석
        </h2>
        <ResultChartsSection result={result} />
      </section>

      {/* 4. 마크다운 요약 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          💡 AI 분석 요약
        </h2>
        <SummaryMarkdown summary={summary} />
      </section>

      {/* 5. 포트폴리오 저장 버튼 */}
      <section className="flex justify-center pt-4 border-t border-gray-200">
        <SavePortfolioButton backtestId={backtestId} />
      </section>
    </div>
  );
}
