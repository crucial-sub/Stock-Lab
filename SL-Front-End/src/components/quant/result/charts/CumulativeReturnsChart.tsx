"use client";

import { useEffect, useRef } from "react";
import * as am5 from "@amcharts/amcharts5";
import * as am5xy from "@amcharts/amcharts5/xy";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import type { BacktestResult } from "@/types/api";

interface CumulativeReturnsChartProps {
  yieldPoints: BacktestResult["yieldPoints"];
}

export function CumulativeReturnsChart({ yieldPoints }: CumulativeReturnsChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !yieldPoints || yieldPoints.length === 0) return;

    // Root 생성
    const root = am5.Root.new(chartRef.current);
    root.setThemes([am5themes_Animated.new(root)]);

    // 차트 생성
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: true,
        wheelX: "panX",
        wheelY: "zoomX",
        pinchZoomX: true,
        layout: root.verticalLayout,
      })
    );

    // 데이터 변환
    const chartData = yieldPoints.map((point) => ({
      date: new Date(point.date).getTime(),
      cumulativeReturn: point.cumulativeReturn || 0,
      drawdown: point.dailyDrawdown || 0,
    }));

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

    // Y축 1 (수익률)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
        tooltip: am5.Tooltip.new(root, {}),
      })
    );

    // Y축 2 (낙폭)
    const yAxisDrawdown = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: true,
        }),
        min: 0,
        max: 100,
        strictMinMax: true,
      })
    );

    // 수익률 라인 시리즈
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "누적 수익률",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "cumulativeReturn",
        valueXField: "date",
        stroke: am5.color(0x3b82f6), // 파란색
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      })
    );
    series.strokes.template.setAll({ strokeWidth: 2 });
    series.data.setAll(chartData);

    // 낙폭 영역 시리즈 (빨간색)
    const drawdownSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "낙폭 (MDD)",
        xAxis: xAxis,
        yAxis: yAxisDrawdown,
        valueYField: "drawdown",
        valueXField: "date",
        stroke: am5.color(0xef4444), // 빨간색
        fill: am5.color(0xef4444),
        fillOpacity: 0.3,
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      })
    );
    drawdownSeries.fills.template.setAll({ visible: true, fillOpacity: 0.3 });
    drawdownSeries.data.setAll(chartData);

    // 커서
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "zoomX",
      })
    );

    // 스크롤바
    chart.set(
      "scrollbarX",
      am5.Scrollbar.new(root, {
        orientation: "horizontal",
      })
    );

    // 범례
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.p50,
        x: am5.p50,
      })
    );
    legend.data.setAll(chart.series.values);

    return () => {
      root.dispose();
    };
  }, [yieldPoints]);

  return <div ref={chartRef} className="w-full h-96" />;
}
