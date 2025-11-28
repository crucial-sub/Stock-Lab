"use client";

import * as am5 from "@amcharts/amcharts5";
import am5themes_Animated from "@amcharts/amcharts5/themes/Animated";
import * as am5xy from "@amcharts/amcharts5/xy";
import { useEffect, useRef, useState } from "react";
import type { BacktestResult } from "@/types/api";
import { StockDetailModal } from "@/components/modal/StockDetailModal";

/**
 * 매매 내역 탭 컴포넌트
 * - 누적 수익률 차트
 * - 날짜별 필터링
 * - 거래 내역 테이블 표시
 * - 페이지네이션 지원
 */
interface TradingHistoryTabProps {
  trades: BacktestResult["trades"];
  yieldPoints?: BacktestResult["yieldPoints"];
}

export function TradingHistoryTab({
  trades,
  yieldPoints = [],
}: TradingHistoryTabProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState<"all" | "byDate">("all");
  const [selectedMonth, setSelectedMonth] = useState<string>("");
  const [selectedStock, setSelectedStock] = useState<{
    name: string;
    code: string;
  } | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const itemsPerPage = 10;

  // 월별로 거래 필터링
  const filteredTrades =
    viewMode === "all"
      ? trades
      : trades.filter((trade) => {
          if (!selectedMonth) return true;
          // 매수일의 연-월이 선택된 월과 같은 거래만 표시
          const tradeMonth = trade.buyDate.substring(0, 7); // "2024-01-15" -> "2024-01"
          return tradeMonth === selectedMonth;
        });

  // 페이지네이션 계산
  const totalPages = Math.ceil(filteredTrades.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentTrades = filteredTrades.slice(startIndex, endIndex);

  // 보유일수 계산
  const calculateHoldingDays = (buyDate: string, sellDate: string) => {
    const buy = new Date(buyDate);
    // sellDate가 없으면 현재 날짜 기준으로 계산
    const sell = sellDate ? new Date(sellDate) : new Date();
    return Math.floor((sell.getTime() - buy.getTime()) / (1000 * 60 * 60 * 24));
  };

  // 거래가 발생한 월 목록 추출 (YYYY-MM 형식)
  const tradeMonths = Array.from(
    new Set(trades.map((t) => t.buyDate.substring(0, 7))),
  )
    .sort()
    .reverse(); // 최신 월이 먼저 오도록 역순 정렬

  // viewMode 변경 시 페이지 초기화
  useEffect(() => {
    setCurrentPage(1);
  }, []);

  // 누적 수익률 차트 렌더링
  useEffect(() => {
    if (!chartRef.current || yieldPoints.length === 0) return;

    const root = am5.Root.new(chartRef.current);
    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: false,
        wheelX: "panX",
        wheelY: "zoomX",
        pinchZoomX: true,
      }),
    );

    // 데이터 준비
    const chartData = yieldPoints.map((point) => ({
      date: new Date(point.date).getTime(),
      value: point.cumulativeReturn || 0,
    }));

    // X축 (날짜)
    const xAxis = chart.xAxes.push(
      am5xy.DateAxis.new(root, {
        baseInterval: { timeUnit: "day", count: 1 },
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50,
        }),
        tooltip: am5.Tooltip.new(root, {}),
      }),
    );

    xAxis.get("renderer").labels.template.setAll({
      fontSize: 11,
      fill: am5.color(0x94a3b8),
    });

    // Y축 (수익률)
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {}),
      }),
    );

    yAxis.get("renderer").labels.template.setAll({
      fontSize: 11,
      fill: am5.color(0x94a3b8),
    });

    // 라인 시리즈
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: "누적 수익률",
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: "value",
        valueXField: "date",
        stroke: am5.color(0x3b82f6),
        fill: am5.color(0x3b82f6),
        tooltip: am5.Tooltip.new(root, {
          labelText: "{valueY.formatNumber('#.##')}%",
        }),
      }),
    );

    series.strokes.template.setAll({
      strokeWidth: 2,
    });

    series.fills.template.setAll({
      fillOpacity: 0.1,
      visible: true,
    });

    series.data.setAll(chartData);

    // 커서 추가
    chart.set(
      "cursor",
      am5xy.XYCursor.new(root, {
        behavior: "zoomX",
        xAxis: xAxis,
      }),
    );

    // 애니메이션
    series.appear(1000);
    chart.appear(1000, 100);

    return () => {
      root.dispose();
    };
  }, [yieldPoints]);

  return (
    <div className="space-y-6">
      {/* 누적 수익률 차트 */}
      {yieldPoints.length > 0 && (
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <h3 className="text-lg font-bold text-text-strong mb-4">
            누적 수익률
          </h3>
          <div ref={chartRef} style={{ width: "100%", height: "300px" }} />
        </div>
      )}

      {/* 필터 컨트롤 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-text-strong">거래 내역</h3>

          <div className="flex items-center gap-4">
            {/* 보기 모드 토글 */}
            <div className="flex items-center gap-2 bg-bg-muted rounded-lg p-1">
              <button
                type="button"
                onClick={() => setViewMode("byDate")}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === "byDate"
                    ? "bg-accent-primary text-white"
                    : "text-text-muted hover:text-text-body"
                }`}
              >
                날짜별 보기
              </button>
              <button
                type="button"
                onClick={() => setViewMode("all")}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  viewMode === "all"
                    ? "bg-accent-primary text-white"
                    : "text-text-muted hover:text-text-body"
                }`}
              >
                전체 보기
              </button>
            </div>

            {/* 월 선택 (날짜별 보기 모드일 때만) */}
            {viewMode === "byDate" && (
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="px-4 py-2 text-sm bg-bg-muted border border-border-subtle rounded-lg text-text-body focus:outline-none focus:ring-2 focus:ring-accent-primary"
              >
                <option value="">전체 월</option>
                {tradeMonths.map((month) => (
                  <option key={month} value={month}>
                    {month}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {/* 거래 통계 */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-bg-muted rounded-lg p-4">
            <div className="text-sm text-text-muted mb-1">총 거래 횟수</div>
            <div className="text-2xl font-bold text-text-strong">
              {filteredTrades.length}
            </div>
          </div>
          <div className="bg-bg-muted rounded-lg p-4">
            <div className="text-sm text-text-muted mb-1">수익 거래</div>
            <div className="text-2xl font-bold text-red-500">
              {filteredTrades.filter((t) => t.profitRate >= 0).length}
            </div>
          </div>
          <div className="bg-bg-muted rounded-lg p-4">
            <div className="text-sm text-text-muted mb-1">손실 거래</div>
            <div className="text-2xl font-bold text-blue-500">
              {filteredTrades.filter((t) => t.profitRate < 0).length}
            </div>
          </div>
        </div>

        {/* 테이블 헤더 */}
        <div className="grid grid-cols-[1fr_120px_120px_100px_100px_90px_100px] gap-4 px-6 py-4 bg-bg-muted border-b border-border-subtle">
          <div className="text-sm font-medium text-text-muted">종목명</div>
          <div className="text-sm font-medium text-text-muted text-right">
            진입
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            청산
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            진입가(원)
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            청산가(원)
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            보유일수
          </div>
          <div className="text-sm font-medium text-text-muted text-right">
            수익률 (%)
          </div>
        </div>

        {/* 테이블 바디 */}
        <div>
          {currentTrades.length === 0 ? (
            <div className="py-12 text-center text-text-muted">
              {viewMode === "byDate" && selectedMonth
                ? `${selectedMonth}에 거래 내역이 없습니다.`
                : "거래 내역이 없습니다."}
            </div>
          ) : (
            currentTrades.map((trade, idx) => (
              <div
                key={`${trade.stockCode}-${idx}`}
                className="grid grid-cols-[1fr_120px_120px_100px_100px_90px_100px] gap-4 px-6 py-4 border-b border-border-subtle hover:bg-bg-muted transition-colors"
              >
                <button
                  type="button"
                  onClick={() =>
                    setSelectedStock({
                      name: trade.stockName,
                      code: trade.stockCode,
                    })
                  }
                  className="text-text-body font-medium text-left hover:text-accent-primary hover:underline transition-colors"
                >
                  {trade.stockName}
                </button>
                <div className="text-text-body text-right">{trade.buyDate}</div>
                <div className="text-text-body text-right">
                  {trade.sellDate || "-"}
                </div>
                <div className="text-text-body text-right">
                  {trade.buyPrice.toLocaleString('ko-KR')}
                </div>
                <div className="text-text-body text-right">
                  {trade.sellPrice.toLocaleString('ko-KR')}
                </div>
                <div className="text-text-body text-right">
                  {calculateHoldingDays(trade.buyDate, trade.sellDate)}일
                </div>
                <div
                  className={`text-right font-semibold ${
                    trade.profitRate >= 0 ? "text-red-500" : "text-blue-500"
                  }`}
                >
                  {trade.profitRate.toFixed(2)}
                </div>
              </div>
            ))
          )}
        </div>

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 py-6">
            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-body disabled:opacity-30 disabled:cursor-not-allowed"
            >
              &lt;
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((page) => {
                return (
                  page === 1 ||
                  page === totalPages ||
                  Math.abs(page - currentPage) <= 2
                );
              })
              .map((page, idx, arr) => {
                const prevPage = arr[idx - 1];
                const showEllipsis = prevPage && page - prevPage > 1;

                return (
                  <div key={page} className="flex items-center gap-2">
                    {showEllipsis && (
                      <span className="text-text-muted">...</span>
                    )}
                    <button
                      type="button"
                      onClick={() => setCurrentPage(page)}
                      className={`w-8 h-8 flex items-center justify-center rounded font-medium transition-colors ${
                        currentPage === page
                          ? "bg-accent-primary text-white"
                          : "text-text-muted hover:text-text-body hover:bg-bg-muted"
                      }`}
                    >
                      {page}
                    </button>
                  </div>
                );
              })}

            <button
              type="button"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-body disabled:opacity-30 disabled:cursor-not-allowed"
            >
              &gt;
            </button>
          </div>
        )}
      </div>

      {/* 종목 상세 모달 */}
      <StockDetailModal
        isOpen={!!selectedStock}
        onClose={() => setSelectedStock(null)}
        stockName={selectedStock?.name || ""}
        stockCode={selectedStock?.code || ""}
      />
    </div>
  );
}
