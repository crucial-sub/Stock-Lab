"use client";

import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieLabelRenderProps,
} from "recharts";
import { Title } from "@/components/common/Title";
import type { BacktestResult } from "@/types/api";

/**
 * 매매 결과 통계 탭 컴포넌트
 * - 주요 통계 지표 표시
 * - 매매 성공률, 유니버스별 비중, 매도 조건별 비중 차트
 */
interface StatisticsTabProps {
  statistics: BacktestResult["statistics"];
}

export function StatisticsTab({ statistics }: StatisticsTabProps) {
  // 초기 자본 (기본값: 5억원 = 500,000,000원, API 명세 확정 후 수정 예정)
  const initialCapital = 50000000;

  // 실제 통계 데이터 기반 계산
  const winRate = (statistics.winRate || 0);
  const loseRate = 100 - winRate;

  // 차트 데이터 - 실제 데이터 기반
  const successRateData = [
    { name: "수익 거래", value: winRate, color: "#3b82f6" },
    { name: "손실 거래", value: loseRate, color: "#ff4d6d" },
  ];

  // TODO: 실제 유니버스별 비중 데이터가 있으면 대체
  const universeData = [
    { name: "코스피", value: 60, color: "#3b82f6" },
    { name: "코스닥", value: 40, color: "#a855f7" },
  ];

  // TODO: 실제 매도 조건별 비중 데이터가 있으면 대체
  const sellConditionData = [
    { name: "목표가", value: 40, color: "#10b981" },
    { name: "손절가", value: 30, color: "#f59e0b" },
    { name: "보유기간", value: 20, color: "#8b5cf6" },
    { name: "기타", value: 10, color: "#06b6d4" },
  ];

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      <div className="mb-6">
        <Title>매매 결과 통계</Title>
      </div>

      {/* 통계 지표 그리드 - 실제 데이터 */}
      <div className="grid grid-cols-3 gap-8 mb-12">
        {/* 왼쪽 섹션 */}
        <div className="space-y-6">
          <StatItem label="총 거래 횟수" value={`${(statistics as any).totalTrades || 0}회`} />
          <StatItem
            label="승리 거래"
            value={`${(statistics as any).winningTrades || 0}회`}
            valueColor="text-accent-primary"
          />
          <StatItem
            label="패배 거래"
            value={`${(statistics as any).losingTrades || 0}회`}
            valueColor="text-accent-error"
          />
          <StatItem
            label="Sharpe Ratio"
            value={statistics.sharpeRatio.toFixed(2)}
          />
          <StatItem
            label="변동성"
            value={`${(statistics.volatility * 100).toFixed(2)}%`}
          />
        </div>

        {/* 중간 섹션 */}
        <div className="space-y-6">
          <StatItem
            label="승률"
            value={`${statistics.winRate.toFixed(2)}%`}
            valueColor="text-accent-primary"
          />
          <StatItem
            label="손익비 (Profit Factor)"
            value={statistics.profitFactor.toFixed(2)}
          />
          <StatItem
            label="최대 낙폭 (MDD)"
            value={`${Math.abs(statistics.maxDrawdown).toFixed(2)}%`}
            valueColor="text-accent-error"
          />
          <StatItem
            label="연 환산 수익률"
            value={`${statistics.annualizedReturn.toFixed(2)}%`}
            valueColor={statistics.annualizedReturn >= 0 ? "text-accent-primary" : "text-accent-error"}
          />
          <StatItem
            label="총 수익률"
            value={`${statistics.totalReturn.toFixed(2)}%`}
            valueColor={statistics.totalReturn >= 0 ? "text-accent-primary" : "text-accent-error"}
          />
        </div>

        {/* 오른쪽 섹션 */}
        <div className="space-y-6">
          <StatItem
            label="초기 자본"
            value={`${initialCapital.toLocaleString()}원`}
          />
          <StatItem
            label="최종 자본"
            value={`${((statistics as any).finalCapital || initialCapital).toLocaleString()}원`}
            valueColor={(statistics as any).finalCapital >= initialCapital ? "text-accent-primary" : "text-accent-error"}
          />
          <StatItem
            label="순손익"
            value={`${(((statistics as any).finalCapital || initialCapital) - initialCapital).toLocaleString()}원`}
            valueColor={(statistics as any).finalCapital >= initialCapital ? "text-accent-primary" : "text-accent-error"}
          />
          <StatItem
            label="평균 거래당 수익"
            value={(statistics as any).totalTrades > 0
              ? `${((((statistics as any).finalCapital || initialCapital) - initialCapital) / (statistics as any).totalTrades).toLocaleString()}원`
              : "0원"
            }
          />
          <StatItem
            label="수익률 / MDD"
            value={statistics.maxDrawdown !== 0
              ? (statistics.totalReturn / Math.abs(statistics.maxDrawdown)).toFixed(2)
              : "N/A"
            }
          />
        </div>
      </div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-3 gap-6">
        {/* 매매 성공률 차트 */}
        <div>
          <h4 className="text-base font-semibold text-text-strong mb-4">
            매매 성공률
          </h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={successRateData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value">
                {successRateData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 유니버스별 매수 비중 */}
        <div>
          <h4 className="text-base font-semibold text-text-strong mb-4">
            유니버스별 매수 비중
          </h4>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={universeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: PieLabelRenderProps) => {
                  const percent = Number(props.percent ?? 0);
                  return `${props.name} ${(percent * 100).toFixed(0)}%`;
                }}
                outerRadius={60}
                fill="#8884d8"
                dataKey="value"
              >
                {universeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 매도 조건별 비중 */}
        <div>
          <h4 className="text-base font-semibold text-text-strong mb-4">
            매도 조건별 비중
          </h4>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sellConditionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: PieLabelRenderProps) => {
                  const percent = Number(props.percent ?? 0);
                  return `${props.name} ${(percent * 100).toFixed(0)}%`;
                }}
                outerRadius={60}
                fill="#8884d8"
                dataKey="value"
              >
                {sellConditionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

/**
 * 통계 지표 아이템 컴포넌트
 */
function StatItem({
  label,
  value,
  valueColor = "text-text-strong",
}: {
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <div>
      <div className={`text-2xl font-bold ${valueColor} mb-1`}>{value}</div>
      <div className="text-sm text-text-body">{label}</div>
    </div>
  );
}