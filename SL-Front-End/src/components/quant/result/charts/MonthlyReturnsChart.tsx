"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useMemo, useRef, useState } from "react";
import type { BacktestResult } from "@/types/api";

interface MonthlyReturnsChartProps {
  yieldPoints: BacktestResult["yieldPoints"];
}

interface MonthlyData {
  yearMonth: string;
  portfolioReturn: number;
  kospiReturn: number;
  kosdaqReturn: number;
}

export function MonthlyReturnsChart({ yieldPoints }: MonthlyReturnsChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  // 사용 가능한 연도 목록 추출
  const availableYears = useMemo(() => {
    if (!yieldPoints || yieldPoints.length === 0) return [];

    const years = new Set<number>();
    yieldPoints.forEach((point) => {
      const year = new Date(point.date).getFullYear();
      years.add(year);
    });

    return Array.from(years).sort((a, b) => b - a); // 최신 연도부터
  }, [yieldPoints]);

  // 기본값: 가장 최신 연도
  const [selectedYear, setSelectedYear] = useState<number | null>(null);

  // selectedYear 초기화
  useEffect(() => {
    if (availableYears.length > 0 && selectedYear === null) {
      setSelectedYear(availableYears[0]);
    }
  }, [availableYears, selectedYear]);

  // 월별 데이터 계산
  const monthlyData = useMemo(() => {
    if (!yieldPoints || yieldPoints.length === 0 || selectedYear === null)
      return [];

    const monthMap = new Map<number, any[]>();

    // 선택한 연도의 데이터만 필터링하고 월별로 그룹화
    yieldPoints
      .filter((point) => new Date(point.date).getFullYear() === selectedYear)
      .forEach((point) => {
        const month = new Date(point.date).getMonth() + 1;
        if (!monthMap.has(month)) {
          monthMap.set(month, []);
        }
        monthMap.get(month)?.push(point);
      });

    // 각 월의 수익률 계산
    const result: MonthlyData[] = [];
    for (let month = 1; month <= 12; month++) {
      const points = monthMap.get(month);
      if (points && points.length > 0) {
        const sortedPoints = points.sort(
          (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
        );
        const startReturn = sortedPoints[0].cumulativeReturn || 0;
        const endReturn =
          sortedPoints[sortedPoints.length - 1].cumulativeReturn || 0;
        const returnRate = endReturn - startReturn;

        result.push({
          yearMonth: `${selectedYear}.${String(month).padStart(2, "0")}`,
          portfolioReturn: returnRate,
          kospiReturn: 0, // TODO: KOSPI 데이터 연동 필요
          kosdaqReturn: 0, // TODO: KOSDAQ 데이터 연동 필요
        });
      }
    }

    return result;
  }, [yieldPoints, selectedYear]);

  useEffect(() => {
    if (!chartRef.current || monthlyData.length === 0) return;

    const root = am5.Root.new(chartRef.current);
    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
      }),
    );

    // X축 (연월)
    const xAxis = chart.xAxes.push(
      am5xy.CategoryAxis.new(root, {
        categoryField: "yearMonth",
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 30,
        }),
      }),
    );
    xAxis.data.setAll(monthlyData);

    // Y축 (수익률 %)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
      }),
    );

    // 포트폴리오 수익률 시리즈
    const portfolioSeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "포트폴리오",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "portfolioReturn",
        categoryXField: "yearMonth",
        clustered: true,
        tooltip: am5.Tooltip.new(root, {
          labelText: "{name}: {valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    portfolioSeries.columns.template.setAll({
      width: am5.percent(80),
      strokeOpacity: 0,
    });
    portfolioSeries.data.setAll(monthlyData);

    // 색상: 양수는 주황색, 음수는 파란색
    portfolioSeries.columns.template.adapters.add("fill", (fill, target) => {
      const dataItem = target.dataItem;
      if (dataItem) {
        const value = dataItem.get("valueY") as number;
        if (value >= 0) {
          return am5.color(0xf97316); // 주황색
        }
        return am5.color(0x3b82f6); // 파란색
      }
      return fill;
    });

    // KOSPI 수익률 시리즈
    const kospiSeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "KOSPI",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "kospiReturn",
        categoryXField: "yearMonth",
        clustered: true,
        tooltip: am5.Tooltip.new(root, {
          labelText: "{name}: {valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    kospiSeries.columns.template.setAll({
      width: am5.percent(80),
      strokeOpacity: 0,
      fill: am5.color(0xef4444), // 빨간색
    });
    kospiSeries.data.setAll(monthlyData);

    // KOSDAQ 수익률 시리즈
    const kosdaqSeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "KOSDAQ",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "kosdaqReturn",
        categoryXField: "yearMonth",
        clustered: true,
        tooltip: am5.Tooltip.new(root, {
          labelText: "{name}: {valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    kosdaqSeries.columns.template.setAll({
      width: am5.percent(80),
      strokeOpacity: 0,
      fill: am5.color(0x06b6d4), // 청록색
    });
    kosdaqSeries.data.setAll(monthlyData);

    // 범례
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.p50,
        x: am5.p50,
      }),
    );
    legend.data.setAll(chart.series.values);

    return () => {
      root.dispose();
    };
  }, [monthlyData]);

  if (availableYears.length === 0) {
    return (
      <div className="w-full h-96 flex items-center justify-center text-text-muted">
        데이터가 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 연도 선택 버튼 */}
      <div className="flex justify-end gap-2">
        {availableYears.map((year) => (
          <button
            key={year}
            onClick={() => setSelectedYear(year)}
            className={`px-4 py-2 text-sm font-medium rounded transition-colors ${
              selectedYear === year
                ? "bg-accent-primary text-white"
                : "text-text-body hover:text-text-strong border border-border-default hover:bg-bg-muted"
            }`}
          >
            {year}
          </button>
        ))}
      </div>

      {/* 차트 */}
      <div ref={chartRef} className="w-full h-96" />
    </div>
  );
}
