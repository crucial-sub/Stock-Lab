import { FieldPanel } from "@/components/quant/ui";
import { PeriodReturnsChart, StatMetric } from "../common";

/**
 * Result 페이지 통계 섹션
 * - 주요 통계 지표 및 기간별 수익률 차트
 */
interface StatisticsSectionProps {
  statistics: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    finalCapital?: number;
  };
  initialCapital: number;
  periodReturns: Array<{ label: string; value: number }>;
}

export function StatisticsSection({
  statistics,
  initialCapital,
  periodReturns,
}: StatisticsSectionProps) {
  const stats = statistics;

  // 실제 데이터 기반 계산
  const totalProfit = (stats.finalCapital || initialCapital) - initialCapital;
  const finalAssets = stats.finalCapital || initialCapital;

  // 일 평균 수익률 계산 (CAGR 기반, 연간 252 거래일 기준)
  // 공식: (1 + CAGR)^(1/252) - 1
  const dailyReturn =
    ((1 + stats.annualizedReturn / 100) ** (1 / 252) - 1) * 100;

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
    <div className="grid grid-cols-1 gap-5 mb-10 lg:grid-cols-1">
      <FieldPanel conditionType="none" className="h-full">
        <div className="flex flex-col gap-5">
          <span className="text-[1.125rem] font-semibold">통계</span>

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
              value={formatSignedPercent(stats.totalReturn)}
              tone={getTone(stats.totalReturn)}
              tooltip="전체 기간 누적 수익률"
            />
            <StatMetric
              label="CAGR"
              value={formatSignedPercent(stats.annualizedReturn)}
              tone={getTone(stats.annualizedReturn)}
              tooltip="연평균 복리 수익률"
            />
            <StatMetric
              label="MDD"
              value={`${Math.abs(stats.maxDrawdown).toFixed(2)}%`}
              tone="neutral"
              tooltip="최대 낙폭 (Maximum Drawdown)"
            />
          </div>

          {/* 하단 자산 정보 */}
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            <StatMetric label="투자 원금" value={formatCurrency(initialCapital)} />
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
      </FieldPanel>

      <FieldPanel conditionType="none" className="h-full">
        <PeriodReturnsChart periodReturns={periodReturns} />
      </FieldPanel>
    </div>
  );
}
