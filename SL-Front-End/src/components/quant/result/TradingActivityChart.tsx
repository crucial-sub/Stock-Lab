"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useRef } from "react";

/**
 * 매수/매도 활동 차트 컴포넌트
 * - 완료된 백테스트 결과를 위한 차트
 * - 일별 매수/매도 횟수 (bar) + 누적 수익률 (line)
 */
interface TradingActivityChartProps {
  yieldPoints: Array<{
    date: string;
    buyCount?: number;
    sellCount?: number;
    cumulativeReturn?: number;
  }>;
  startDate?: string; // YYYY-MM-DD 형식
  endDate?: string;   // YYYY-MM-DD 형식
  className?: string;
}

export function TradingActivityChart({ yieldPoints, startDate, endDate, className = "" }: TradingActivityChartProps) {
  const chartDivRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<am5.Root | null>(null);

  useEffect(() => {
    if (!chartDivRef.current) return;

    // amCharts 초기화
    const root = am5.Root.new(chartDivRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: false,
        wheelX: "panX",
        wheelY: "zoomX",
        layout: root.verticalLayout,
        paddingLeft: 0,
        paddingRight: 0,
      })
    );

    // X축 범위 계산
    let minDate: number | undefined;
    let maxDate: number | undefined;

    if (startDate && endDate) {
      minDate = new Date(startDate).getTime();
      maxDate = new Date(endDate).getTime();
    }

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50,
        }),
        tooltip: am5.Tooltip.new(root, {}),
        // X축 범위 고정
        min: minDate,
        max: maxDate,
        strictMinMax: startDate && endDate ? true : false,
      })
    );

    // Y축 (수익률) - 왼쪽
    const yAxisReturn = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: false,
        }),
        numberFormat: "#'%'",
        strictMinMax: false,
      })
    );

    // Y축 (거래 횟수) - 오른쪽
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: true,
        }),
        min: -10,
        max: 10,
        strictMinMax: true,
      })
    );

    // 매수 시리즈 (빨간색 바, 위로)
    const buySeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "매수",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "buy",
        valueXField: "date",
        fill: am5.color(0xff6b6b),
        stroke: am5.color(0xff6b6b),
        clustered: false,
        tooltip: am5.Tooltip.new(root, {
          labelText: "매수: {valueY}회",
        }),
      })
    );

    buySeries.columns.template.setAll({
      width: am5.percent(40),
      fillOpacity: 0.7,
      strokeOpacity: 0,
    });

    // 매도 시리즈 (파란색 바, 아래로)
    const sellSeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "매도",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "sell",
        valueXField: "date",
        fill: am5.color(0x5470c6),
        stroke: am5.color(0x5470c6),
        clustered: false,
        tooltip: am5.Tooltip.new(root, {
          labelText: "매도: {valueY}회",
        }),
      })
    );

    sellSeries.columns.template.setAll({
      width: am5.percent(40),
      fillOpacity: 0.7,
      strokeOpacity: 0,
    });

    // 누적 수익률 시리즈 (회색 라인)
    const returnSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "누적 수익률",
        xAxis: xAxis,
        yAxis: yAxisReturn,
        valueYField: "return",
        valueXField: "date",
        stroke: am5.color(0x999999),
        fill: am5.color(0x999999),
        tooltip: am5.Tooltip.new(root, {
          labelText: "수익률: {valueY}%",
        }),
      })
    );

    returnSeries.strokes.template.setAll({
      strokeWidth: 2,
    });

    returnSeries.fills.template.setAll({
      visible: true,
      fillOpacity: 0.1,
    });

    // 차트 데이터 생성
    const chartData = yieldPoints.map(point => ({
      date: new Date(point.date).getTime(),
      buy: point.buyCount || 0,
      sell: -(point.sellCount || 0), // 매도는 음수 (아래로 표시)
      return: point.cumulativeReturn || 0,
    }));

    buySeries.data.setAll(chartData);
    sellSeries.data.setAll(chartData);
    returnSeries.data.setAll(chartData);

    // 범례 추가
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
      })
    );

    legend.data.setAll(chart.series.values);

    // 커서 추가
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "zoomX",
      })
    );

    // 클린업
    return () => {
      root.dispose();
    };
  }, [yieldPoints, startDate, endDate]);

  return (
    <div className={className}>
      <div ref={chartDivRef} className="w-full h-[500px]" />
    </div>
  );
}
