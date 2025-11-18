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

  return (
    <div className="space-y-6 mb-6">
      {/* 통계 지표 섹션 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <div className="flex justify-between items-start">
          {/* 왼쪽: 통계 지표 */}
          <div className="flex-1">
            <h2 className="text-lg font-bold text-text-strong mb-4">통계</h2>

            {/* 상단 주요 지표 */}
            <div className="grid grid-cols-4 gap-8 mb-6">
              <StatMetric
                label="일 평균 수익률"
                value={`${dailyReturn.toFixed(3)}%`}
                color={dailyReturn >= 0 ? "text-red-500" : "text-blue-500"}
                tooltip="일별 평균 수익률 (연간 252 거래일 기준)"
              />
              <StatMetric
                label="누적 수익률"
                value={`${stats.totalReturn.toFixed(2)}%`}
                color={
                  stats.totalReturn >= 0 ? "text-red-500" : "text-blue-500"
                }
                tooltip="전체 기간 누적 수익률"
              />
              <StatMetric
                label="CAGR"
                value={`${stats.annualizedReturn.toFixed(2)}%`}
                color={
                  stats.annualizedReturn >= 0 ? "text-red-500" : "text-blue-500"
                }
                tooltip="연평균 복리 수익률"
              />
              <StatMetric
                label="MDD"
                value={`${Math.abs(stats.maxDrawdown).toFixed(2)}%`}
                color="text-text-strong"
                tooltip="최대 낙폭 (Maximum Drawdown)"
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
                value={`${Math.round(totalProfit).toLocaleString()}원`}
                color={totalProfit >= 0 ? "text-red-500" : "text-blue-500"}
                size="large"
                tooltip="총 수익금 (최종 자산 - 투자 원금)"
              />
              <StatMetric
                label="현재 총 자산"
                value={`${Math.round(finalAssets).toLocaleString()}원`}
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
    </div>
  );
}
