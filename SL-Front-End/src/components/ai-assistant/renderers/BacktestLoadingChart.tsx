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
const INITIAL_RETURN = 0;

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
  const lastDataLengthRef = useRef(0);
  const lastReturnRef = useRef<number | undefined>(undefined);
  const lastTimestampRef = useRef<number | undefined>(undefined);

  /**
   * 1️⃣ 차트 초기화 (마운트 시 한 번만)
   */
  useEffect(() => {
    if (!chartRef.current) return;

    // Root 생성 - 워터마크 제거를 위해 설정 추가
    const root = am5.Root.new(chartRef.current);

    // 워터마크 제거 (amCharts 로고)
    root._logo?.dispose();
    root.dateFormatter.set("dateFormat", "yyyy.MM.dd");
    root.dateFormatter.set("intlLocales", "ko-KR");

    // 애니메이션 테마 적용 (성능 최적화를 위해 duration 조정)
    const animatedTheme = am5themes_Animated.new(root);
    root.setThemes([animatedTheme]);

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
    chart.set("paddingBottom", 30);

    // X축 (날짜) - 범위 고정
    const xAxisRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 50,
      strokeOpacity: 0.1,
      minorGridEnabled: true,
    });

    // X축 레이블 스타일 조정 (크기 축소)
    xAxisRenderer.labels.template.setAll({
      fontSize: 12,
      fontWeight: "600",
      fill: am5.color(0x4a4a4a),
    });

    // X축 툴팁 (젠포트 스타일: 검은 배경, 흰 텍스트, YYYY.MM.DD)
    const xAxisTooltip = am5.Tooltip.new(root, {
      pointerOrientation: "horizontal",
      keepTargetHover: true,
      animationDuration: 0,
    });
    xAxisTooltip.get("background")?.setAll({
      fill: am5.color(0x000000),
      stroke: am5.color(0x000000),
      fillOpacity: 1,
    });
    xAxisTooltip.label.setAll({
      text: "{valueX.formatDate('yyyy.MM.dd')}",
      fill: am5.color(0xffffff),
      fontSize: 12,
      fontWeight: "600",
      paddingTop: 6,
      paddingBottom: 6,
      paddingLeft: 10,
      paddingRight: 10,
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
    xAxis.set("tooltip", xAxisTooltip);
    xAxisTooltip.label.setAll({ text: "{value.formatDate('yyyy.MM.dd')}" });
    xAxis.get("tooltip")?.label.setAll({ text: "{valueX.formatDate('yyyy.MM.dd')}" });
    xAxis.set("tooltipDateFormat", "yyyy.MM.dd");
    xAxisRenderer.grid.template.setAll({ strokeOpacity: 0.05 });

    // X축 레이블 포맷 (YYYY.MM 형식으로 표시)
    xAxis.get("dateFormats")!["day"] = "yyyy.MM";
    xAxis.get("dateFormats")!["month"] = "yyyy.MM";
    xAxis.get("periodChangeDateFormats")!["day"] = "yyyy.MM";
    xAxis.get("periodChangeDateFormats")!["month"] = "yyyy.MM";

    // Y축 1 (수익률) - 왼쪽
    const yAxisReturnRenderer = am5xy.AxisRendererY.new(root, {});
    const yAxisReturn = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: yAxisReturnRenderer,
      })
    );
    yAxisReturnRenderer.grid.template.setAll({ strokeOpacity: 0.05 });

    // Y축 2 (매매 횟수) - 완전 숨김
    const yAxisTradeRenderer = am5xy.AxisRendererY.new(root, {
      opposite: true,
      visible: false,
      inside: true,
    });
    yAxisTradeRenderer.labels.template.setAll({
      visible: false,
      forceHidden: true
    });
    yAxisTradeRenderer.grid.template.setAll({
      visible: false,
      strokeOpacity: 0
    });

    const yAxisTrade = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: yAxisTradeRenderer,
        // 매수/매도 막대 높이를 줄이기 위해 스케일 조정
        min: -10, // 최소값 설정
        max: 10, // 최대값 설정
        strictMinMax: true,
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
          labelText: "누적수익률: {cumulativeReturn}%",
          animationDuration: 0,
        }),
      })
    );
    returnSeries.strokes.template.setAll({ strokeWidth: 2 });
    returnSeries.fills.template.setAll({
      fill: COLOR_RETURN_FILL,
      fillOpacity: 0.3,
    });
    returnSeries.setAll({
      sequencedInterpolation: false,
      interpolationDuration: 0,
    });
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
          animationDuration: 0,
        }),
      })
    );
    buySeries.columns.template.setAll({
      width: am5.percent(50), // 막대 너비를 50%로 조정
      strokeOpacity: 0,
      fillOpacity: 0.7, // 투명도 추가
    });
    buySeries.setAll({
      sequencedInterpolation: false,
      interpolationDuration: 0,
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
          animationDuration: 0,
        }),
      })
    );
    sellSeries.columns.template.setAll({
      width: am5.percent(50), // 막대 너비를 50%로 조정
      strokeOpacity: 0,
      fillOpacity: 0.7, // 투명도 추가
    });
    sellSeries.setAll({
      sequencedInterpolation: false,
      interpolationDuration: 0,
    });
    sellSeries.data.setAll([]);

    // 커서 - 그래프 호버 시 세로선 표시
    const cursor = am5xy.XYCursor.new(root, {
      behavior: "none",
      xAxis: xAxis,
      yAxis: yAxisReturn,
    });

    // 커서 스타일 설정 - 세로선만 표시
    cursor.lineX.setAll({
      strokeOpacity: 0.5,
      stroke: am5.color(0x000000),
      strokeDasharray: [2, 2],
    });
    cursor.lineY.setAll({
      strokeOpacity: 0,
    });

    chart.set("cursor", cursor);
    chart.plotContainer.set("mask", undefined);

    // 범례 제거 - 오른쪽 y축처럼 보이는 범례 삭제

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

    // 데이터 길이 리셋 (새 차트 생성 시)
  useEffect(() => {
    lastDataLengthRef.current = 0;
    lastReturnRef.current = undefined;
    lastTimestampRef.current = undefined;
  }, [startDate, endDate]);

  /**
   * 2️⃣ 데이터 업데이트 (accumulatedYieldPoints 변경 시)
   * 실시간 업데이트로 즉시 반영
   */
  useEffect(() => {
    if (!chartInstanceRef.current || !accumulatedYieldPoints) return;

    const { returnSeries, buySeries, sellSeries } = chartInstanceRef.current;

    // 데이터 변환 - 새로 들어온 구간만 추가로 반영 (정렬 + 중복 제거)
    const sortedPoints = [...accumulatedYieldPoints]
      .map((p) => ({
        ...p,
        _ts: new Date(p.date).getTime(),
      }))
      .sort((a, b) => a._ts - b._ts);

    const currentLength = sortedPoints.length;
    const previousLength = lastDataLengthRef.current;

    if (currentLength === 0) {
      returnSeries.data.setAll([]);
      buySeries.data.setAll([]);
      sellSeries.data.setAll([]);
      lastDataLengthRef.current = 0;
      lastReturnRef.current = undefined;
      lastTimestampRef.current = undefined;
      return;
    }

    // 진행 중 백테스트가 재시작되거나 데이터가 초기화된 경우를 대비해 길이가 줄어들면 전체 리셋
    const shouldResetAll = currentLength < previousLength;
    if (shouldResetAll) {
      lastReturnRef.current = undefined;
      lastTimestampRef.current = undefined;
    }
    const lastTimestamp = lastTimestampRef.current;
    const slice = shouldResetAll
      ? sortedPoints
      : sortedPoints.filter((p) => p._ts > (lastTimestamp ?? -Infinity));
    const hasExistingData = !shouldResetAll && !!lastTimestamp;

    const incrementalData: ChartDataPoint[] = slice.map((point) => {
      const value =
        point.cumulativeReturn !== undefined && point.cumulativeReturn !== null
          ? point.cumulativeReturn
          : lastReturnRef.current ?? INITIAL_RETURN;

      lastReturnRef.current = value;

      const dataPoint = {
        date: new Date(point.date).getTime(),
        cumulativeReturn: value,
        buyCount: point.buyCount || 0,
        sellCount: point.sellCount || 0,
        sellCountNegative: -(point.sellCount || 0),
      };
      lastTimestampRef.current = point._ts ?? dataPoint.date;
      return dataPoint;
    });

    if (!hasExistingData || shouldResetAll) {
      returnSeries.data.setAll(incrementalData);
      buySeries.data.setAll(incrementalData);
      sellSeries.data.setAll(incrementalData);
    } else if (incrementalData.length > 0) {
      returnSeries.data.pushAll(incrementalData);
      buySeries.data.pushAll(incrementalData);
      sellSeries.data.pushAll(incrementalData);
    }

    lastDataLengthRef.current = currentLength;
    if (incrementalData.length > 0) {
      lastTimestampRef.current =
        incrementalData[incrementalData.length - 1].date;
    }
  }, [accumulatedYieldPoints]);

  return (
    <div
      ref={chartRef}
      className="w-full h-96"
      aria-label="백테스트 진행 상황 차트"
    />
  );
}
