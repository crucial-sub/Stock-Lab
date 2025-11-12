"use client";

import { useState } from "react";
import type { BacktestResult } from "@/types/api";

/**
 * 매매 내역 탭 컴포넌트
 * - 거래 내역 테이블 표시
 * - 페이지네이션 지원
 */
interface TradingHistoryTabProps {
  trades: BacktestResult["trades"];
}

export function TradingHistoryTab({ trades }: TradingHistoryTabProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 페이지네이션 계산
  const totalPages = Math.ceil(trades.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentTrades = trades.slice(startIndex, endIndex);

  return (
    <div className="bg-bg-surface rounded-lg shadow-card overflow-hidden">
      {/* 테이블 헤더 */}
      <div className="grid grid-cols-[1fr_120px_100px_100px_120px_120px_100px_120px] gap-4 px-6 py-4 bg-bg-muted border-b border-border-subtle">
        <div className="text-sm font-medium text-text-muted">매매 종목명</div>
        <div className="text-sm font-medium text-text-muted text-right">
          거래 단가 (원)
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          수량 (주)
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          수익률 (%)
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          매수 일자
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          매도 일자
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          보유 비중 (%)
        </div>
        <div className="text-sm font-medium text-text-muted text-right">
          평가 금액 (원)
        </div>
      </div>

      {/* 테이블 바디 */}
      <div>
        {currentTrades.length === 0 ? (
          <div className="py-12 text-center text-text-muted">
            거래 내역이 없습니다.
          </div>
        ) : (
          currentTrades.map((trade, idx) => (
            <div
              key={`${trade.stockCode}-${idx}`}
              className="grid grid-cols-[1fr_120px_100px_100px_120px_120px_100px_120px] gap-4 px-6 py-4 border-b border-border-subtle hover:bg-bg-muted transition-colors"
            >
              <div className="text-text-body font-medium">
                {trade.stockName}
              </div>
              <div className="text-text-body text-right">
                {Math.round(trade.buyPrice).toLocaleString()}
              </div>
              <div className="text-text-body text-right">
                {trade.quantity?.toLocaleString() || 0}
              </div>
              <div
                className={`text-right font-semibold ${
                  trade.profitRate >= 0
                    ? "text-brand-primary"
                    : "text-accent-primary"
                }`}
              >
                {trade.profitRate > 0 ? "+" : ""}
                {trade.profitRate.toFixed(2)}
              </div>
              <div className="text-text-body text-right">{trade.buyDate}</div>
              <div className="text-text-body text-right">{trade.sellDate}</div>
              <div className="text-text-body text-right">
                {trade.weight.toFixed(2)}
              </div>
              <div className="text-text-body text-right">
                {Math.round(trade.valuation).toLocaleString()}
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
              // 현재 페이지 기준으로 앞뒤 2개씩만 표시
              return (
                page === 1 ||
                page === totalPages ||
                Math.abs(page - currentPage) <= 2
              );
            })
            .map((page, idx, arr) => {
              // "..." 표시를 위한 로직
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
  );
}
