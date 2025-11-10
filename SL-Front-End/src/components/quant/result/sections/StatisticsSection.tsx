import { StatMetric, PeriodReturnsChart } from "../common";

/**
 * Result 페이지 통계 섹션
 * - 주요 통계 지표 및 기간별 수익률 차트
 */
interface StatisticsSectionProps {
  statistics: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
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
  const totalProfit = initialCapital * (stats.totalReturn / 100);
  const finalAssets = initialCapital + totalProfit;

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6 mb-6">
      <div className="flex justify-between items-start">
        {/* 왼쪽: 통계 지표 */}
        <div className="flex-1">
          <h2 className="text-lg font-bold text-text-strong mb-4">통계</h2>

          {/* 상단 주요 지표 */}
          <div className="grid grid-cols-4 gap-8 mb-6">
            <StatMetric
              label="일 평균 수익률"
              value={`${(stats.totalReturn / 365).toFixed(2)}%`}
              color="text-accent-primary"
              tooltip="일별 평균 수익률"
            />
            <StatMetric
              label="누적 수익률"
              value={`${stats.annualizedReturn.toFixed(2)}%`}
              color="text-accent-primary"
              tooltip="연간 수익률"
            />
            <StatMetric
              label="CAGR"
              value={`${stats.annualizedReturn.toFixed(2)}%`}
              color="text-accent-primary"
              tooltip="연평균 복리 수익률"
            />
            <StatMetric
              label="MDD"
              value={`${stats.maxDrawdown.toFixed(2)}%`}
              color="text-text-strong"
              tooltip="최대 낙폭"
            />
          </div>

          {/* 하단 자산 정보 */}
          <div className="grid grid-cols-3 gap-8">
            <StatMetric
              label="투자 원금"
              value={`${initialCapital.toLocaleString()}원`}
              size="large"
            />
            <StatMetric
              label="총 손익"
              value={`${totalProfit.toLocaleString()}원`}
              color="text-accent-primary"
              size="large"
              tooltip="총 수익금"
            />
            <StatMetric
              label="현재 총 자산"
              value={`${finalAssets.toLocaleString()}원`}
              size="large"
            />
          </div>
        </div>

        {/* 오른쪽: 수익률 바 차트 */}
        <div className="ml-8">
          <PeriodReturnsChart periodReturns={periodReturns} />
        </div>
      </div>
    </div>
  );
}
