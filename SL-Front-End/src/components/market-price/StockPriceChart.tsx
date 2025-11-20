"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useRef } from "react";
import type { PriceHistoryPoint } from "@/lib/api/company";

interface StockPriceChartProps {
  /**
   * 주가 데이터 배열
   */
  data: PriceHistoryPoint[];
  /**
   * 선택된 기간 (일 단위)
   */
  period: number;
  /**
   * 상승/하락 여부 (빨강/파랑 색상 결정)
   */
  isRising?: boolean;
}

/**
 * amCharts 5 기반 주가 라인 차트 컴포넌트
 * - 일봉 데이터 시각화
 * - 기간별 필터링 지원
 * - 반응형 디자인
 */
export function StockPriceChart({
  data,
  period,
  isRising = true,
}: StockPriceChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // 데이터가 없으면 차트를 그리지 않음
    if (!data || data.length === 0) {
      return;
    }

    // 데이터 정렬 및 변환 (모든 유효한 데이터)
    const allValidData = data
      .filter((point) => {
        // closePrice 또는 다른 가능한 필드명 확인
        const price =
          (point as any).closePrice ||
          (point as any).close_price ||
          (point as any).price ||
          (point as any).close;
        return price != null && price !== undefined;
      })
      .map((point) => {
        const price =
          (point as any).closePrice ||
          (point as any).close_price ||
          (point as any).price ||
          (point as any).close;
        return {
          date: new Date(point.date).getTime(),
          value: Number(price),
          originalDate: point.date,
        };
      })
      .sort((a, b) => a.date - b.date);

    // 기간(일수) 기준으로 최근 데이터 필터링 (주말/공휴일 포함)
    const lastTimestamp = allValidData[allValidData.length - 1]?.date ?? 0;
    const cutoffTimestamp = lastTimestamp - period * 24 * 60 * 60 * 1000;
    let filteredData = allValidData.filter((point) => point.date >= cutoffTimestamp);

    if (filteredData.length === 0) {
      filteredData = allValidData.slice(-Math.min(period, allValidData.length));
    }

    // 데이터가 없으면 차트를 그리지 않음
    if (filteredData.length === 0) {
      return;
    }

    // 최고가, 최저가, 마지막 값 찾기
    const prices = filteredData.map((d) => d.value);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const _maxPoint = filteredData.find((d) => d.value === maxPrice)!;
    const _minPoint = filteredData.find((d) => d.value === minPrice)!;
    const lastPoint = filteredData[filteredData.length - 1];

    // 색상 결정 (상승: 빨강, 하락: 파랑)
    const chartColor = isRising ? 0xff6464 : 0x007dfc;

    // Root 생성
    const root = am5.Root.new(chartRef.current);

    // 워터마크 제거
    root._logo?.dispose();

    // 테마 적용
    root.setThemes([am5themes_Animated.new(root)]);

    // XY 차트 생성 (미니멀 디자인)
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: false,
        panY: false,
        wheelX: "none",
        wheelY: "none",
        paddingLeft: 0,
        paddingRight: 0,
        paddingTop: 25,
        paddingBottom: 25,
      }),
    );

    // X축 (날짜) - 라벨과 그리드 완전히 숨김
    const xRenderer = am5xy.AxisRendererX.new(root, {
      minGridDistance: 50,
    });
    xRenderer.labels.template.setAll({
      visible: true,
      fontSize: 8,
      fill: am5.color(0x97a3ba),
      centerY: am5.p50,
      paddingTop: 4,
    });
    xRenderer.grid.template.setAll({
      stroke: am5.color(0xe9eef7),
      strokeOpacity: 0.4,
    });

    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        grindIntervals: [{ timeUnit: "week", count: 1 }],
        renderer: xRenderer,
      }),
    );

    // Y축 (가격) - 라벨과 그리드 완전히 숨김
    const yRenderer = am5xy.AxisRendererY.new(root, {});
    yRenderer.labels.template.setAll({
      visible: true,
      fontSize: 8,
      fill: am5.color(0x97a3ba),
      centerY: am5.p50,
    });
    yRenderer.grid.template.setAll({
      stroke: am5.color(0xe9eef7),
      strokeOpacity: 0.6,
      strokeDasharray: [2, 4],
    });

    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: yRenderer,
      }),
    );

    // 라인 시리즈 생성 (깔끔한 단일 라인)
    const areaGradient = am5.LinearGradient.new(root, {
      stops: [
        { color: am5.color(chartColor), opacity: 0.25 },
        { color: am5.color(chartColor), opacity: 0 },
      ],
      rotation: 90,
    });

    const strokeGradient = am5.LinearGradient.new(root, {
      stops: [
        { color: am5.color(chartColor), opacity: 0.9 },
        { color: am5.color(chartColor), opacity: 0.5 },
      ],
      rotation: 0,
    });

    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "주가",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "value",
        valueXField: "date",
        stroke: am5.color(chartColor),
        fill: am5.color(chartColor),
        tooltip: am5.Tooltip.new(root, {
          pointerOrientation: "vertical",
          getFillFromSprite: false,
          autoTextColor: false,
          labelHTML: `
            <div style="text-align: center; padding: 8px 12px; background: #F5F5F5; border-radius: 4px;">
              <div style="font-weight: 600; font-size: 14px; color: #000000; margin-bottom: 4px;">
                {valueY}원
              </div>
              <div style="font-size: 12px; color: #000000;">
                {valueX.formatDate('yyyy년 MM월 dd일')}
              </div>
            </div>
          `,
        }),
      }),
    );

    // 라인 스타일 설정 (부드럽고 연속적인 라인)
    series.strokes.template.setAll({
<<<<<<< HEAD
      strokeWidth: 2.5,
      tension: 0.5, // 곡선 부드럽게
=======
      strokeWidth: 2,
      strokeGradient,
    });
    series.fills.template.setAll({
      visible: true,
      fillGradient: areaGradient,
>>>>>>> f5f9a26 (Refactor: 세부 종목 창 디자인 수정)
    });

    // 데이터 포인트 숨김 (깔끔한 라인만)
    series.bullets.clear();

    // 데이터 설정
    series.data.setAll(filteredData);

    // 최고가 라벨 추가 (차트 상단)
    const maxBullet = am5.Label.new(root, {
      text: `최고 ${maxPrice.toLocaleString()}원`,
      fill: am5.color(chartColor),
      fontSize: 12,
      fontWeight: "600",
      centerX: am5.p50,
      centerY: 0,
      paddingTop: 8,
    });

    series.bullets.push(() => {
      return am5.Bullet.new(root, {
        locationX: undefined,
        sprite: maxBullet,
      });
    });

    maxBullet.adapters.add("visible", (_visible, target) => {
      const dataItem = target.dataItem as any;
      if (!dataItem) return false;
      return dataItem.get("valueY") === maxPrice;
    });

    // 최저가 라벨 추가 (차트 하단)
    const minBullet = am5.Label.new(root, {
      text: `최저 ${minPrice.toLocaleString()}원`,
      fill: am5.color(chartColor),
      fontSize: 12,
      fontWeight: "600",
      centerX: am5.p50,
      centerY: am5.p100,
      paddingBottom: 8,
    });

    series.bullets.push(() => {
      return am5.Bullet.new(root, {
        locationX: undefined,
        sprite: minBullet,
      });
    });

    minBullet.adapters.add("visible", (_visible, target) => {
      const dataItem = target.dataItem as any;
      if (!dataItem) return false;
      return dataItem.get("valueY") === minPrice;
    });

    // 현재가 기준선
    const lastRange = yAxis.createAxisRange(
      yAxis.makeDataItem({
        value: lastPoint.value,
      }),
    );
    lastRange.get("grid").setAll({
      stroke: am5.color(chartColor),
      strokeOpacity: 0.6,
      strokeDasharray: [6, 6],
    });
    lastRange.get("label").setAll({
      text: `${lastPoint.value.toLocaleString()}원`,
      fontSize: 10,
      fontWeight: "400",
      fill: am5.color(chartColor),
      background: am5.RoundedRectangle.new(root, {
        fill: am5.color(0xffffff),
        fillOpacity: 0.9,
        cornerRadiusTL: 4,
        cornerRadiusBL: 4,
        cornerRadiusTR: 4,
        cornerRadiusBR: 4,
        stroke: am5.color(chartColor),
        strokeOpacity: 0.3,
      }),
      paddingLeft: 4,
      paddingRight: 4,
      paddingTop: 2,
      paddingBottom: 2,
      centerY: am5.p50,
    });

    // 커서 추가 (마우스 오버 시 수직선만)
    const cursor = chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "none",
        xAxis: xAxis,
      }),
    );
    cursor.lineY.set("visible", false);
    cursor.lineX.setAll({
      stroke: am5.color(0xcccccc),
      strokeWidth: 1,
      strokeDasharray: [4, 4],
    });

    // 애니메이션
    series.appear(1000);
    chart.appear(1000, 100);

    // Cleanup: 컴포넌트 unmount 시 차트 dispose
    return () => {
      root.dispose();
    };
  }, [data, period, isRising]);

  // 데이터가 없거나 로딩 중일 때 placeholder 표시
  if (!data || data.length === 0) {
    return (
      <div className="h-32 w-full flex items-center justify-center bg-gray-50 rounded">
        <p className="text-sm text-gray-500">차트 데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div
      ref={chartRef}
      className="h-32 w-full bg-white"
      role="img"
      aria-label="주가 추세 그래프"
      style={{ minHeight: "128px" }}
    />
  );
}
