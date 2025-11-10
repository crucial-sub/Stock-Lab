"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { BacktestResult } from "@/types/api";

/**
 * 수익률 차트 컴포넌트
 * - Recharts를 사용한 누적 수익률 라인 차트
 * - 포트폴리오 vs KOSPI vs KOSDAQ 비교
 */
interface ReturnsChartProps {
  yieldPoints: BacktestResult["yieldPoints"];
  className?: string;
}

export function ReturnsChart({ yieldPoints, className = "" }: ReturnsChartProps) {
  // 데이터 변환
  const chartData = yieldPoints.map((point) => ({
    date: point.date,
    portfolioReturn: point.cumulativeReturn || 0,
    // 임시 데이터 (실제 API 응답에 따라 수정 필요)
    kospiReturn: (point.cumulativeReturn || 0) * 0.8,
    kosdaqReturn: (point.cumulativeReturn || 0) * 0.6,
  }));

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#9ca3af"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#ffffff",
              border: "1px solid #e5e7eb",
              borderRadius: "4px",
            }}
            formatter={(value: number) => `${value.toFixed(2)}%`}
            labelFormatter={(label) => {
              const date = new Date(label);
              return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: "14px" }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="portfolioReturn"
            name="수익률"
            stroke="#ff4d6d"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="kospiReturn"
            name="KOSPI"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="kosdaqReturn"
            name="KOSDAQ"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}