"use client";

import type { BacktestResult, UniverseStock } from "@/types/api";
import { useMemo, useState } from "react";

/**
 * 매매종목 정보 탭 컴포넌트
 * - 유니버스의 모든 종목을 그리드 형태로 표시
 * - 실제 거래된 종목은 매수/매도 포인트 표시
 * - 더보기/접기 기능 (초기 30개만 표시)
 */
interface StockInfoTabProps {
  trades: BacktestResult["trades"];
  universeStocks?: UniverseStock[];
}

interface StockInfo {
  stockCode: string;
  stockName: string;
  hasBuy: boolean;
  hasSell: boolean;
}

export function StockInfoTab({ trades, universeStocks = [] }: StockInfoTabProps) {
  const [showAll, setShowAll] = useState(false);
  const INITIAL_DISPLAY_COUNT = 30;

  // 종목별 매수/매도 여부 계산
  const stockList = useMemo(() => {
    const stockMap = new Map<string, StockInfo>();

    // 1. 유니버스의 모든 종목을 먼저 추가
    universeStocks.forEach((stock) => {
      stockMap.set(stock.stockCode, {
        stockCode: stock.stockCode,
        stockName: stock.stockName,
        hasBuy: false,
        hasSell: false,
      });
    });

    // 2. 거래된 종목에 매수/매도 마커 추가
    trades.forEach((trade) => {
      if (!stockMap.has(trade.stockCode)) {
        // 유니버스에 없는 종목도 추가 (직접 추가한 종목)
        stockMap.set(trade.stockCode, {
          stockCode: trade.stockCode,
          stockName: trade.stockName,
          hasBuy: false,
          hasSell: false,
        });
      }

      const stock = stockMap.get(trade.stockCode)!;
      stock.hasBuy = true;
      stock.hasSell = true;
    });

    return Array.from(stockMap.values()).sort((a, b) =>
      a.stockName.localeCompare(b.stockName, "ko")
    );
  }, [trades, universeStocks]);

  // 거래한 종목과 거래하지 않은 종목 구분
  const tradedStocksCount = stockList.filter((s) => s.hasBuy || s.hasSell).length;

  // 표시할 종목 리스트
  const displayedStocks = showAll ? stockList : stockList.slice(0, INITIAL_DISPLAY_COUNT);
  const hasMore = stockList.length > INITIAL_DISPLAY_COUNT;

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-text-strong">
          유니버스 종목 목록 ({stockList.length}개)
        </h3>
        <p className="text-sm text-text-muted mt-1">
          선택한 테마/유니버스의 전체 종목입니다. 실제 거래한 종목은 {tradedStocksCount}개입니다.
        </p>
      </div>

      {/* 범례 (상단으로 이동) */}
      <div className="mb-6 flex items-center justify-center gap-6 text-sm bg-bg-muted rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-text-muted">매수</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-text-muted">매도</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded border border-border-subtle bg-bg-surface opacity-50" />
          <span className="text-text-muted">거래 없음</span>
        </div>
      </div>

      {/* 그리드 레이아웃 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {stockList.length === 0 ? (
          <div className="col-span-full py-12 text-center text-text-muted">
            종목이 없습니다.
          </div>
        ) : (
          displayedStocks.map((stock, index) => {
            const hasTraded = stock.hasBuy || stock.hasSell;
            return (
              <div
                key={stock.stockCode}
                className={`relative p-4 rounded border transition-all ${
                  hasTraded
                    ? "bg-bg-muted border-border-subtle hover:border-accent-primary hover:bg-bg-surface"
                    : "bg-bg-surface border-border-subtle opacity-50 hover:opacity-75"
                }`}
              >
                {/* 순번 */}
                <div className="absolute top-2 left-2 text-xs font-medium text-text-muted">
                  {String(index + 1).padStart(2, "0")}
                </div>

                {/* 매수/매도 마커 */}
                {hasTraded && (
                  <div className="absolute top-2 right-2 flex gap-1">
                    {stock.hasBuy && (
                      <div
                        className="w-2 h-2 rounded-full bg-red-500"
                        title="매수"
                      />
                    )}
                    {stock.hasSell && (
                      <div
                        className="w-2 h-2 rounded-full bg-blue-500"
                        title="매도"
                      />
                    )}
                  </div>
                )}

                {/* 종목 정보 */}
                <div className="mt-6 space-y-1">
                  <div className="text-sm font-semibold text-text-strong truncate">
                    {stock.stockName}
                  </div>
                  <div className="text-xs text-text-muted">
                    {stock.stockCode}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* 더보기/접기 버튼 */}
      {hasMore && (
        <div className="mt-6 flex justify-center">
          <button
            type="button"
            onClick={() => setShowAll(!showAll)}
            className="px-6 py-2 text-sm font-medium text-accent-primary border border-accent-primary rounded-lg hover:bg-accent-primary hover:text-white transition-colors"
          >
            {showAll
              ? "접기"
              : "더보기"}
          </button>
        </div>
      )}
    </div>
  );
}
