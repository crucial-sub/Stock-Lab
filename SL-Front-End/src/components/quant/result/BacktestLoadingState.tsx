"use client";

/**
 * 백테스트 로딩 상태 컴포넌트
 * - 백테스트가 실행 중일 때 표시되는 UI
 * - 진행률, 통계 스켈레톤, amCharts 로딩 애니메이션 표시
 */

import { useEffect, useRef } from "react";
import * as am5 from "@amcharts/amcharts5";
import * as am5xy from "@amcharts/amcharts5/xy";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";

interface BacktestLoadingStateProps {
  backtestId: string;
  status: "pending" | "running";
  progress: number;
}

export function BacktestLoadingState({
  backtestId,
  status,
  progress,
}: BacktestLoadingStateProps) {
  const chartDiv = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartDiv.current) return;

    // amCharts 루트 생성
    const root = am5.Root.new(chartDiv.current);

    // 테마 적용
    root.setThemes([am5themes_Animated.new(root)]);

    // 차트 생성
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        paddingLeft: 0,
        paddingRight: 0,
      })
    );

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50,
        }),
        tooltip: am5.Tooltip.new(root, {}),
      })
    );

    // Y축 (수익률)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
      })
    );

    // 로딩 중 가짜 데이터 생성
    const generateLoadingData = () => {
      const data = [];
      const now = new Date().getTime();
      const dayMs = 24 * 60 * 60 * 1000;

      for (let i = 0; i < 100; i++) {
        const date = now - (100 - i) * dayMs;
        const value = Math.sin(i / 10) * 5 + Math.random() * 2;
        data.push({
          date: date,
          value: value,
        });
      }
      return data;
    };

    // 시리즈 생성 (누적 수익률)
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "누적수익률",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "value",
        valueXField: "date",
        stroke: am5.color(0x3b82f6), // 파란색
        fill: am5.color(0x3b82f6),
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY}%",
        }),
      })
    );

    // 데이터 설정
    series.data.setAll(generateLoadingData());

    // 애니메이션 효과
    series.appear(1000);
    chart.appear(1000, 100);

    // 로딩 인디케이터 표시
    const indicator = root.container.children.push(
      am5.Container.new(root, {
        width: am5.p100,
        height: am5.p100,
        layer: 1000,
      })
    );

    const indicatorLabel = indicator.children.push(
      am5.Label.new(root, {
        text: "백테스트 실행 중...",
        fontSize: 16,
        fontWeight: "500",
        textAlign: "center",
        x: am5.p50,
        y: am5.p50,
        centerX: am5.p50,
        centerY: am5.p50,
      })
    );

    // 정리
    return () => {
      root.dispose();
    };
  }, []);

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto space-y-6">
        {/* 헤더 영역 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-accent-error">
                {backtestId}
              </h1>
              <p className="text-sm text-text-body mt-1">
                {status === "pending"
                  ? "백테스트 대기 중..."
                  : "백테스트 실행 중..."}
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-accent-primary">
                {progress}%
              </div>
              <div className="text-sm text-text-body">진행률</div>
            </div>
          </div>

          {/* 진행률 바 */}
          <div className="mt-4">
            <div className="w-full bg-bg-app rounded-full h-2 overflow-hidden">
              <div
                className="bg-accent-primary h-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* 통계 스켈레톤 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "누적 수익률", loading: true },
              { label: "MDD", loading: true },
              { label: "전체시간", loading: true },
              { label: "예상시간", loading: true },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-sm text-text-body mb-1">{stat.label}</div>
                <div className="animate-pulse">
                  <div className="h-8 bg-bg-app rounded w-32 mx-auto" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 차트 영역 - amCharts */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="space-y-4">
            {/* 차트 타이틀 */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-strong">
                수익률 차트
              </h3>
              <div className="flex gap-2">
                <div className="px-3 py-1 bg-bg-app rounded text-sm text-text-body">
                  로딩 중...
                </div>
              </div>
            </div>

            {/* amCharts 차트 영역 */}
            <div
              ref={chartDiv}
              className="w-full h-[400px] relative"
              style={{ opacity: 0.5 }}
            />

            {/* 범례 */}
            <div className="flex items-center justify-center gap-6 pt-2 border-t border-border-subtle">
              <div className="flex items-center gap-2">
                <div className="w-4 h-1 bg-blue-500 rounded" />
                <span className="text-sm text-text-body">누적수익률</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-1 bg-red-500 rounded" />
                <span className="text-sm text-text-body">매수</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-1 bg-blue-300 rounded" />
                <span className="text-sm text-text-body">매도</span>
              </div>
            </div>
          </div>
        </div>

        {/* 하단 정보 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <div className="text-sm text-text-body mb-1">매수 횟수</div>
                <div className="animate-pulse">
                  <div className="h-6 bg-bg-app rounded w-20" />
                </div>
              </div>
              <div>
                <div className="text-sm text-text-body mb-1">매도 횟수</div>
                <div className="animate-pulse">
                  <div className="h-6 bg-bg-app rounded w-20" />
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-text-body mb-1">평균 수익률</div>
                <div className="animate-pulse">
                  <div className="h-6 bg-bg-app rounded w-24" />
                </div>
              </div>
              <div>
                <div className="text-sm text-text-body mb-1">승률</div>
                <div className="animate-pulse">
                  <div className="h-6 bg-bg-app rounded w-20" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
