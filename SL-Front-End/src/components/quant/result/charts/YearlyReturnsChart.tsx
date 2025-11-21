"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useMemo, useRef, useState } from "react";
import type { BacktestResult } from "@/types/api";

interface YearlyReturnsChartProps {
  yieldPoints: BacktestResult["yieldPoints"];
}

export function YearlyReturnsChart({ yieldPoints }: YearlyReturnsChartProps) {
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

  // 선택한 연도의 데이터만 필터링
  const filteredData = useMemo(() => {
    if (!yieldPoints || yieldPoints.length === 0 || selectedYear === null)
      return [];

    return yieldPoints.filter((point) => {
      const year = new Date(point.date).getFullYear();
      return year === selectedYear;
    });
  }, [yieldPoints, selectedYear]);

  useEffect(() => {
    if (!chartRef.current || filteredData.length === 0) return;

    const root = am5.Root.new(chartRef.current);
    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: true,
        wheelX: "panX",
        wheelY: "zoomX",
        pinchZoomX: true,
      }),
    );

    // 데이터 변환 (누적 수익률 기준으로 정규화)
    const startReturn = filteredData[0]?.cumulativeReturn || 0;
    const chartData = filteredData.map((point) => ({
      date: new Date(point.date).getTime(),
      portfolioReturn: (point.cumulativeReturn || 0) - startReturn,
      kospiReturn: 0, // TODO: KOSPI 데이터 연동 필요
      kosdaqReturn: 0, // TODO: KOSDAQ 데이터 연동 필요
    }));

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50,
        }),
        tooltip: am5.Tooltip.new(root, {}),
        // 날짜 형식: YYYY.MM 또는 YYYY.MM.DD
        dateFormats: {
          day: "yyyy.MM.dd",
          week: "yyyy.MM.dd",
          month: "yyyy.MM",
          year: "yyyy",
        },
        periodChangeDateFormats: {
          day: "yyyy.MM.dd",
          week: "yyyy.MM.dd",
          month: "yyyy.MM",
          year: "yyyy",
        },
      }),
    );

    // Y축 (수익률 %)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
        tooltip: am5.Tooltip.new(root, {}),
      }),
    );

    // 수익률 라인 (빨간색)
    const portfolioSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "수익률",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "portfolioReturn",
        valueXField: "date",
        stroke: am5.color(0xef4444), // 빨간색
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    portfolioSeries.strokes.template.setAll({ strokeWidth: 2 });
    portfolioSeries.data.setAll(chartData);

    // 포인트에 원형 마커 추가
    portfolioSeries.bullets.push(() => {
      return am5.Bullet.new(root, {
        sprite: am5.Circle.new(root, {
          radius: 4,
          fill: portfolioSeries.get("fill"),
          stroke: root.interfaceColors.get("background"),
          strokeWidth: 2,
        }),
      });
    });

    // KOSPI 라인 (주황색)
    const kospiSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "KOSPI",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "kospiReturn",
        valueXField: "date",
        stroke: am5.color(0xf97316), // 주황색
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    kospiSeries.strokes.template.setAll({ strokeWidth: 2 });
    kospiSeries.data.setAll(chartData);

    // KOSDAQ 라인 (파란색)
    const kosdaqSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "KOSDAQ",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "kosdaqReturn",
        valueXField: "date",
        stroke: am5.color(0x3b82f6), // 파란색
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      }),
    );
    kosdaqSeries.strokes.template.setAll({ strokeWidth: 2 });
    kosdaqSeries.data.setAll(chartData);

    // 커서
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "zoomX",
      }),
    );

    // 스크롤바
    chart.set(
      "scrollbarX",
      am5.Scrollbar.new(root, {
        orientation: "horizontal",
      }),
    );

    // 범례 (차트 상단에 배치하여 스크롤바와 겹치지 않도록)
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.p50,
        x: am5.p50,
        y: 0,
        layout: root.horizontalLayout,
      }),
    );
    legend.data.setAll(chart.series.values);

    // 차트에 상단 여백 추가 (범례 공간 확보)
    chart.set("paddingTop", 30);

    return () => {
      root.dispose();
    };
  }, [filteredData]);

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
