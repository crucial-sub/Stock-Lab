"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useRef } from "react";

// YieldPoint 타입 정의
interface YieldPoint {
  date: string;
  cumulativeReturn?: number;
  buyCount?: number;
  sellCount?: number;
}

/**
 * BacktestLoadingChart Props
 */
interface BacktestLoadingChartProps {
  /** 투자 시작일 (ISO 8601) */
  startDate: string;
  /** 투자 종료일 (ISO 8601) */
  endDate: string;
  /** 누적된 수익률 데이터 포인트 (실시간 업데이트) */
  accumulatedYieldPoints: YieldPoint[];
  /** 진행률 (0-100) */
  progress: number;
}

/**
 * 차트 데이터 포인트
 */
interface ChartDataPoint {
  /** 날짜 (타임스탬프) */
  date: number;
  /** 누적 수익률 (%) */
  cumulativeReturn: number;
  /** 매수 횟수 */
  buyCount: number;
  /** 매도 횟수 */
  sellCount: number;
  /** 매도 횟수 (음수, 막대 그래프용) */
  sellCountNegative: number;
}

const COLOR_RETURN = am5.color(0x7c5cfe);
const COLOR_RETURN_FILL = am5.color(0xded6ff);
const COLOR_BUY = am5.color(0xff6464); // price-up
const COLOR_SELL = am5.color(0x007dfc); // price-down

/**
 * 백테스트 로딩 차트 컴포넌트
 *
 * - amcharts5 기반 실시간 업데이트 차트
 * - 누적 수익률 라인 그래프 (브랜드 퍼플)
 * - 매수/매도 횟수 막대 그래프 (price-up / price-down)
 * - X축 범위 고정 (투자 시작일 ~ 종료일)
 * - 줌/패닝 비활성화
 */
export function BacktestLoadingChart({
  startDate,
  endDate,
  accumulatedYieldPoints,
  progress,
}: BacktestLoadingChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<{
    root: am5.Root;
    chart: am5xy.XYChart;
    returnSeries: am5xy.LineSeries;
    buySeries: am5xy.ColumnSeries;
    sellSeries: am5xy.ColumnSeries;
  } | null>(null);

  /**
   * 1️⃣ 차트 초기화 (마운트 시 한 번만)
   */
  useEffect(() => {
    if (!chartRef.current) return;

    // Root 생성
    const root = am5.Root.new(chartRef.current);
    root.setThemes([am5themes_Animated.new(root)]);

    // 차트 생성
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        pinchZoomX: false,
      })
    );
    chart.get("colors")!.set("step", 1);
    chart.set("paddingTop", 20);
    chart.set("paddingBottom", 10);
    chart.chartContainer.setAll({
      background: am5.Rectangle.new(root, {
        fill: am5.color(0xF2F6FF),
        fillOpacity: 1,
        cornerRadius: 20,
      }),
    });

    // X축 (날짜) - 범위 고정
    const xAxisRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 50,
      strokeOpacity: 0.1,
      minorGridEnabled: true,
    });
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        min: new Date(startDate).getTime(),
        max: new Date(endDate).getTime(),
        strictMinMax: true,
        renderer: xAxisRenderer,
      })
    );
    xAxisRenderer.grid.template.setAll({ strokeOpacity: 0.05 });

    // X축 레이블 포맷 (YYYY.MM.DD)
    xAxis.get("dateFormats")!["day"] = "yyyy.MM.dd";
    xAxis.get("periodChangeDateFormats")!["day"] = "yyyy.MM.dd";

    // Y축 1 (수익률) - 왼쪽
    const yAxisReturnRenderer = am5xy.AxisRendererY.new(root, {});
    const yAxisReturn = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: yAxisReturnRenderer,
      })
    );
    yAxisReturnRenderer.grid.template.setAll({ strokeOpacity: 0.05 });

    // Y축 2 (매매 횟수) - 오른쪽, 0 기준 양방향
    const yAxisTrade = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {
          opposite: true,
          gridTemplate: { strokeOpacity: 0 },
        }),
      })
    );

    // 시리즈 1: 누적 수익률 라인
    const returnSeries = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "누적 수익률",
        xAxis: xAxis,
        yAxis: yAxisReturn,
        valueYField: "cumulativeReturn",
        valueXField: "date",
        stroke: COLOR_RETURN,
        tooltip: am5.Tooltip.new(root, {
          labelText: `[bold]{valueX.formatDate('yyyy.MM.dd')}[/]
누적수익률: {cumulativeReturn}%
매수: {buyCount}회
매도: {sellCount}회`,
        }),
      })
    );
    returnSeries.strokes.template.setAll({ strokeWidth: 2 });
    returnSeries.fills.template.setAll({
      fill: COLOR_RETURN_FILL,
      fillOpacity: 0.3,
    });
    returnSeries.set("fillGradient", am5.LinearGradient.new(root, {
      stops: [{ color: COLOR_RETURN_FILL }, { color: am5.color(0xffffff), opacity: 0 }],
    }));
    returnSeries.data.setAll([]); // 빈 배열로 시작

    // 시리즈 2: 매수 횟수 막대 (위로)
    const buySeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "매수",
        xAxis: xAxis,
        yAxis: yAxisTrade,
        valueYField: "buyCount",
        valueXField: "date",
        fill: COLOR_BUY,
        stroke: COLOR_BUY,
        clustered: false, // 겹치기 허용
        tooltip: am5.Tooltip.new(root, {
          labelText: "매수: {buyCount}회",
        }),
      })
    );
    buySeries.columns.template.setAll({
      width: am5.percent(80),
      strokeOpacity: 0,
    });
    buySeries.data.setAll([]);

    // 시리즈 3: 매도 횟수 막대 (아래로, 음수)
    const sellSeries = chart.series.push(
      am5xy.ColumnSeries.new(root, {
        name: "매도",
        xAxis: xAxis,
        yAxis: yAxisTrade,
        valueYField: "sellCountNegative", // 음수 값
        valueXField: "date",
        fill: COLOR_SELL,
        stroke: COLOR_SELL,
        clustered: false,
        tooltip: am5.Tooltip.new(root, {
          labelText: "매도: {sellCount}회",
        }),
      })
    );
    sellSeries.columns.template.setAll({
      width: am5.percent(80),
      strokeOpacity: 0,
    });
    sellSeries.data.setAll([]);

    // 커서
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "none",
      })
    );

    // 범례 추가 (선택사항)
    const legend = chart.children.push(
      am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
      })
    );
    legend.data.setAll(chart.series.values);

    // 인스턴스 저장
    chartInstanceRef.current = {
      root,
      chart,
      returnSeries,
      buySeries,
      sellSeries,
    };

    // 정리 함수
    return () => {
      root.dispose();
      chartInstanceRef.current = null;
    };
  }, [startDate, endDate]); // 날짜가 바뀔 때만 재생성

  /**
   * 2️⃣ 데이터 업데이트 (accumulatedYieldPoints 변경 시)
   */
  useEffect(() => {
    if (!chartInstanceRef.current || !accumulatedYieldPoints) return;

    const { returnSeries, buySeries, sellSeries } = chartInstanceRef.current;

    // 데이터 변환
    const chartData: ChartDataPoint[] = accumulatedYieldPoints.map(
      (point) => ({
        date: new Date(point.date).getTime(),
        cumulativeReturn: point.cumulativeReturn || 0,
        buyCount: point.buyCount || 0,
        sellCount: point.sellCount || 0,
        sellCountNegative: -(point.sellCount || 0), // 음수 변환
      })
    );

    // ⭐ 데이터 업데이트 (애니메이션 자동 적용)
    returnSeries.data.setAll(chartData);
    buySeries.data.setAll(chartData);
    sellSeries.data.setAll(chartData);
  }, [accumulatedYieldPoints, progress]);

  return (
    <div
      ref={chartRef}
      className="w-full h-96"
      aria-label="백테스트 진행 상황 차트"
    />
  );
}
