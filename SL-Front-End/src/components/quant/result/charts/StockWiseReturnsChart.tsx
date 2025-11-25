"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useMemo, useRef, useState } from "react";
import type { BacktestResult } from "@/types/api";

interface StockWiseReturnsChartProps {
  trades: BacktestResult["trades"];
  yieldPoints: BacktestResult["yieldPoints"];
}

interface TradePoint {
  date: string;
  dateTimestamp: number;
  stockName: string;
  stockCode: string;
  type: "buy" | "sell";
  profitRate: number;
  holdingDays: number;
  price: number;
  quantity: number;
  reason?: string;  // 매매 사유 추가
}

export function StockWiseReturnsChart({
  trades,
  yieldPoints,
}: StockWiseReturnsChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  // 모든 거래를 날짜별 포인트로 변환
  const allTradePoints = useMemo(() => {
    const points: TradePoint[] = [];

    trades.forEach((trade) => {
      const holdingDays = Math.floor(
        (new Date(trade.sellDate).getTime() -
          new Date(trade.buyDate).getTime()) /
          (1000 * 60 * 60 * 24),
      );

      // 매수 포인트
      points.push({
        date: trade.buyDate,
        dateTimestamp: new Date(trade.buyDate).getTime(),
        stockName: trade.stockName,
        stockCode: trade.stockCode,
        type: "buy",
        profitRate: 0,
        holdingDays: 0,
        price: trade.buyPrice,
        quantity: trade.quantity,
      });

      // 매도 포인트
      points.push({
        date: trade.sellDate,
        dateTimestamp: new Date(trade.sellDate).getTime(),
        stockName: trade.stockName,
        stockCode: trade.stockCode,
        type: "sell",
        profitRate: trade.profitRate,
        holdingDays: holdingDays,
        price: trade.sellPrice,
        quantity: trade.quantity,
        reason: trade.reason,  // 매매 사유 추가
      });
    });

    return points.sort((a, b) => a.dateTimestamp - b.dateTimestamp);
  }, [trades]);

  // 선택한 날짜의 거래 목록
  const selectedDateTrades = useMemo(() => {
    if (!selectedDate) return [];
    return allTradePoints.filter((point) => point.date === selectedDate);
  }, [allTradePoints, selectedDate]);

  useEffect(() => {
    if (!chartRef.current || allTradePoints.length === 0) return;

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

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50,
        }),
      }),
    );

    // Y축 (수익률 %)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
      }),
    );

    // 스캐터 시리즈 (모션 차트)
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "수익률",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "profitRate",
        valueXField: "dateTimestamp",
        tooltip: am5.Tooltip.new(root, {
          labelText: "",  // 빈 문자열로 설정 (커스텀 툴팁 사용)
        }),
        connect: false,
      }),
    );

    series.strokes.template.set("visible", false);
    series.data.setAll(allTradePoints);

    // 버블 마커 추가 (매수/매도 구분, 선택된 날짜 강조)
    series.bullets.push((root, _series, dataItem) => {
      const dataContext = dataItem.dataContext as TradePoint;
      const isBuy = dataContext.type === "buy";
      const isSelected = selectedDate === dataContext.date;

      // 색상 결정: 선택된 날짜만 색상 표시, 나머지는 회색
      let fillColor: am5.Color;
      let fillOpacity: number;

      if (isSelected) {
        // 선택된 날짜: 매수는 빨간색, 매도는 파란색
        if (isBuy) {
          fillColor = am5.color(0xef4444); // 빨간색 (매수)
        } else {
          fillColor = am5.color(0x3b82f6); // 파란색 (매도)
        }
        fillOpacity = 1.0; // 선택된 점은 불투명하게
      } else {
        // 선택되지 않은 날짜: 회색
        fillColor = am5.color(0x94a3b8); // 회색
        fillOpacity = 0.5; // 반투명
      }

      const circle = am5.Circle.new(root, {
        radius: isSelected ? 10 : 8, // 선택된 점은 더 크게
        fill: fillColor,
        fillOpacity: fillOpacity,
        stroke: am5.color(0xffffff),
        strokeWidth: isSelected ? 3 : 2, // 선택된 점은 테두리도 두껍게
        cursorOverStyle: "pointer",
        // 커스텀 툴팁 추가
        tooltipText: isBuy
          ? `${dataContext.stockName}\n매수`
          : `${dataContext.stockName}\n매도: ${dataContext.profitRate.toFixed(2)}%`,
      });

      // 애니메이션 효과
      circle.animate({
        key: "radius",
        from: 0,
        to: isSelected ? 10 : 8,
        duration: 600,
        easing: am5.ease.out(am5.ease.cubic),
      });

      // 클릭 이벤트
      circle.events.on("click", (_ev) => {
        if (selectedDate === dataContext.date) {
          // 같은 날짜 클릭 시 선택 해제
          setSelectedDate(null);
        } else {
          setSelectedDate(dataContext.date);
        }
      });

      // 호버 효과
      circle.states.create("hover", {
        scale: 1.3,
        fillOpacity: 1,
      });

      return am5.Bullet.new(root, {
        sprite: circle,
      });
    });

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

    return () => {
      root.dispose();
    };
  }, [allTradePoints, selectedDate]); // selectedDate 의존성 추가

  return (
    <div className="space-y-6">
      {/* 차트 */}
      <div ref={chartRef} className="w-full h-96" />

      {/* 선택한 날짜의 거래 내역 테이블 */}
      {selectedDate && (
        <div className="bg-bg-muted rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-base font-semibold text-text-strong">
              {selectedDate} 거래 내역
            </h4>
            <button
              onClick={() => setSelectedDate(null)}
              className="text-sm text-text-muted hover:text-text-strong"
            >
              닫기 ✕
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-subtle">
                  <th className="px-4 py-3 text-left font-medium text-text-muted">
                    날짜
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-text-muted">
                    종목명
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-text-muted">
                    유니버스
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-text-muted">
                    매매가격(원)
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-text-muted">
                    보유기간(일)
                  </th>
                  <th className="px-4 py-3 text-center font-medium text-text-muted">
                    사유
                  </th>
                  <th className="px-4 py-3 text-right font-medium text-text-muted">
                    수익률(%)
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedDateTrades.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-8 text-center text-text-muted"
                    >
                      거래 내역이 없습니다.
                    </td>
                  </tr>
                ) : (
                  selectedDateTrades.map((trade, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-border-subtle hover:bg-bg-surface transition-colors"
                    >
                      <td className="px-4 py-3 text-text-body">{trade.date}</td>
                      <td className="px-4 py-3 text-text-body font-medium">
                        {trade.stockName}
                      </td>
                      <td className="px-4 py-3 text-center text-text-body">
                        {/* 종목 코드로 시장 판단: 6자리이고 0으로 시작하면 코스피, 아니면 코스닥 */}
                        {trade.stockCode.length === 6 && trade.stockCode.startsWith('0') ? '코스피' : '코스닥'}
                      </td>
                      <td className="px-4 py-3 text-right text-text-body">
                        {trade.price.toLocaleString('ko-KR')}
                      </td>
                      <td className="px-4 py-3 text-right text-text-body">
                        {trade.holdingDays}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`font-medium ${
                            trade.type === "buy"
                              ? "text-red-500"
                              : "text-blue-500"
                          }`}
                        >
                          {trade.type === "buy" ? "팩터 기반 매수 (익일 시가)" : (trade.reason || "매도")}
                        </span>
                      </td>
                      <td
                        className={`px-4 py-3 text-right font-semibold ${
                          trade.type === "buy"
                            ? "text-text-body"
                            : trade.profitRate >= 0
                            ? "text-red-500"
                            : "text-blue-500"
                        }`}
                      >
                        {trade.type === "buy" ? "-" : trade.profitRate.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
