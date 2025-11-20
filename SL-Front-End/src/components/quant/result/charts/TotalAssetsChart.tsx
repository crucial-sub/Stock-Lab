"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useRef } from "react";
import type { BacktestResult } from "@/types/api";

interface TotalAssetsChartProps {
  yieldPoints: BacktestResult["yieldPoints"];
}

export function TotalAssetsChart({ yieldPoints }: TotalAssetsChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !yieldPoints || yieldPoints.length === 0) return;

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

    // 데이터 변환
    const chartData = yieldPoints.map((point) => ({
      date: new Date(point.date).getTime(),
      portfolioValue: point.portfolioValue || 0,
      cash: point.cash || 0,
      positionValue: point.positionValue || 0,
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

    // Y축 (자산 금액)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
        tooltip: am5.Tooltip.new(root, {}),
      }),
    );

    // 포트폴리오 총 가치 라인 시리즈
    const portfolioSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "총 자산",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "portfolioValue",
        valueXField: "date",
        stroke: am5.color(0x3b82f6),
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#,###')}원",
        }),
      }),
    );
    portfolioSeries.strokes.template.setAll({ strokeWidth: 2 });
    portfolioSeries.data.setAll(chartData);

    // 현금 라인 시리즈
    const cashSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "현금",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "cash",
        valueXField: "date",
        stroke: am5.color(0x10b981),
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#,###')}원",
        }),
      }),
    );
    cashSeries.strokes.template.setAll({
      strokeWidth: 2,
      strokeDasharray: [5, 5],
    });
    cashSeries.data.setAll(chartData);

    // 포지션 가치 라인 시리즈
    const positionSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "보유 포지션",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "positionValue",
        valueXField: "date",
        stroke: am5.color(0xf59e0b),
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#,###')}원",
        }),
      }),
    );
    positionSeries.strokes.template.setAll({
      strokeWidth: 2,
      strokeDasharray: [5, 5],
    });
    positionSeries.data.setAll(chartData);

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
  }, [yieldPoints]);

  return <div ref={chartRef} className="w-full h-96" />;
}
