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
  // 차트 데이터
  const successRateData = [
    { name: "매도실패(상승)", value: 55, color: "#ff4d6d" },
    { name: "매도성공(상승)", value: 45, color: "#3b82f6" },
  ];

  const universeData = [
    { name: "코스피대형", value: 37, color: "#3b82f6" },
    { name: "코스피중대형", value: 17, color: "#a855f7" },
    { name: "코스피중형", value: 46, color: "#ec4899" },
  ];

  const sellConditionData = [
    { name: "목표가", value: 47, color: "#10b981" },
    { name: "손절가", value: 23, color: "#f59e0b" },
    { name: "보유기간(최대)", value: 18, color: "#8b5cf6" },
    { name: "조건매도", value: 12, color: "#06b6d4" },
  ];

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      <h3 className="text-lg font-bold text-text-strong mb-6">매매 결과 통계</h3>

      {/* 통계 지표 그리드 */}
      <div className="grid grid-cols-3 gap-8 mb-12">
        {/* 왼쪽 섹션 */}
        <div className="space-y-6">
          <StatItem label="총 거래일" value="242일" />
          <StatItem
            label="수익률에 평균 수익률"
            value="2.87%"
            valueColor="text-accent-primary"
          />
          <StatItem label="일 표준편차" value="0.45" />
          <StatItem label="Sharpe Ratio" value={statistics.sharpeRatio.toFixed(2)} />
          <StatItem label="고점 대비 절반 비율" value="73%" />
        </div>

        {/* 중간 섹션 */}
        <div className="space-y-6">
          <StatItem label="평균 보유일" value="5.05일" />
          <StatItem
            label="손실률에 평균 수익률"
            value="-2.08%"
            valueColor="text-brand-primary"
          />
          <StatItem label="월 표준편차" value="1.97" />
          <StatItem label="월 평균 수익률" value="1.35%" />
          <StatItem label="KOSPI 상관성" value="0.55" />
        </div>

        {/* 오른쪽 섹션 */}
        <div className="space-y-6">
          <StatItem label="총 매매 횟수" value="809회" />
          <StatItem label="평균 손익비" value="1.38" />
          <StatItem label="CPC Index" value="1.34" />
          <StatItem label="익절 승률(상승/보합/하락)" value="57% / 0% / 43%" />
          <StatItem label="KOSDAQ 상관성" value="0.56" />
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