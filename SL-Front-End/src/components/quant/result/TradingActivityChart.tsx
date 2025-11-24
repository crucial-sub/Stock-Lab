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
  endDate?: string; // YYYY-MM-DD 형식
  className?: string;
}

export function TradingActivityChart({
  yieldPoints,
  startDate,
  endDate,
  className = "",
}: TradingActivityChartProps) {
  const chartDivRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<am5.Root | null>(null);
  const buySeriesRef = useRef<am5xy.ColumnSeries | null>(null);
  const sellSeriesRef = useRef<am5xy.ColumnSeries | null>(null);
  const returnSeriesRef = useRef<am5xy.LineSeries | null>(null);
  const lastDataLengthRef = useRef(0);

  // 차트 초기화 (한 번만 실행)
  useEffect(() => {
    if (!chartDivRef.current) return;

    // amCharts 초기화
    const root = am5.Root.new(chartDivRef.current);
    rootRef.current = root;

    root.setThemes([am5themes_Animated.new(root)]);

    // 워터마크 제거
    root._logo?.dispose();

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: false,
        wheelX: "panX",
        wheelY: "zoomX",
        layout: root.verticalLayout,
        paddingLeft: 0,
        paddingRight: 0,
      }),
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
        strictMinMax: !!(startDate && endDate),
        // 날짜 포맷 설정: YYYY.MM 형식
        dateFormats: {
          month: "yyyy.MM",
        },
        periodChangeDateFormats: {
          month: "yyyy.MM",
        },
        // 2개월마다 표시
        gridIntervals: [
          { timeUnit: "month", count: 2 },
        ],
      }),
    );

    // Y축 (수익률) - 왼쪽 (고정 범위로 기준선 안정화)
    const yAxisReturn = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: false,
        }),
        numberFormat: "#'%'",
        min: -50, // 고정 최소값: -50%
        max: 100, // 고정 최대값: +100%
        strictMinMax: true, // 범위 고정
      }),
    );

    // Y축 (거래 횟수) - 오른쪽 (레이블 숨김, 수익률 축과 0점 동기화)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: true,
          visible: false, // 오른쪽 y축 레이블 숨김
        }),
        // 수익률 축과 0점을 공유하도록 동기화
        syncWithAxis: yAxisReturn,
        strictMinMax: true, // 기준선 고정
      }),
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
      }),
    );

    buySeries.columns.template.setAll({
      width: am5.percent(40),
      fillOpacity: 0.7,
      strokeOpacity: 0,
    });

    buySeriesRef.current = buySeries;

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
      }),
    );

    sellSeries.columns.template.setAll({
      width: am5.percent(40),
      fillOpacity: 0.7,
      strokeOpacity: 0,
    });

    sellSeriesRef.current = sellSeries;

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
      }),
    );

    returnSeries.strokes.template.setAll({
      strokeWidth: 2,
    });

    returnSeries.fills.template.setAll({
      visible: true,
      fillOpacity: 0.1,
    });

    returnSeriesRef.current = returnSeries;

    // 범례 추가
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
      }),
    );

    legend.data.setAll(chart.series.values);

    // 커서 추가
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "zoomX",
      }),
    );

    // 클린업
    return () => {
      root.dispose();
      buySeriesRef.current = null;
      sellSeriesRef.current = null;
      returnSeriesRef.current = null;
      lastDataLengthRef.current = 0;
    };
  }, [startDate, endDate]); // yieldPoints 제거 - 차트 초기화는 날짜 범위 변경 시에만

  // 데이터 증분 업데이트 (yieldPoints가 변경될 때만)
  useEffect(() => {
    if (!buySeriesRef.current || !sellSeriesRef.current || !returnSeriesRef.current) {
      return;
    }

    const currentLength = yieldPoints.length;
    const lastLength = lastDataLengthRef.current;

    // 새로운 데이터 포인트만 추출
    const newPoints = yieldPoints.slice(lastLength);

    if (newPoints.length === 0) {
      return;
    }

    // 새 데이터만 차트에 추가 (전체 재생성 없이 증분 업데이트)
    newPoints.forEach((point) => {
      const dataPoint = {
        date: new Date(point.date).getTime(),
        buy: point.buyCount || 0,
        sell: -(point.sellCount || 0), // 매도는 음수 (아래로 표시)
        return: point.cumulativeReturn || 0,
      };

      buySeriesRef.current!.data.push(dataPoint);
      sellSeriesRef.current!.data.push(dataPoint);
      returnSeriesRef.current!.data.push(dataPoint);
    });

    lastDataLengthRef.current = currentLength;
  }, [yieldPoints]);

  return (
    <div className={className}>
      <div ref={chartDivRef} className="w-full h-[350px]" />
    </div>
  );
}
