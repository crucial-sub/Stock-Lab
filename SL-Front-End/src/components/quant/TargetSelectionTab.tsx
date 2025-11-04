"use client";

import { Input, Panel } from "@/components/common";
import { useTargetStocks } from "@/hooks";
import { useBacktestConfigStore } from "@/stores";
import { useEffect } from "react";
import { BacktestRunButton } from "./BacktestRunButton";

/**
 * 매매 대상 선택 탭 컴포넌트
 *
 * 선택된 종목들을 BacktestRunRequest의 target_stocks 형식으로 저장합니다.
 * target_stocks: string[] (종목명 배열)
 */
export function TargetSelectionTab() {
  const { stocks, searchQuery, setSearchQuery, toggleStock } =
    useTargetStocks();

  // 전역 백테스트 설정 스토어
  const { setTargetStocks } = useBacktestConfigStore();

  /**
   * 선택된 종목이 변경될 때마다 전역 스토어 업데이트
   * useTargetStocks의 stocks 상태 → backtestConfigStore의 target_stocks 동기화
   */
  useEffect(() => {
    const selectedStockNames = stocks
      .filter((stock) => stock.selected)
      .map((stock) => stock.name);

    setTargetStocks(selectedStockNames);
  }, [stocks, setTargetStocks]);

  return (
    <div className="space-y-6">
      {/* Search and Stock Selection */}
      <Panel className="p-6 space-y-4">
        {/* Search Box */}
        <div className="relative">
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="종목 검색"
            className="w-full pr-10"
          />
          <button
            type="button"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
          >
            🔍
          </button>
        </div>

        {/* Stock Grid */}
        <div className="grid grid-cols-5 gap-3">
          {stocks.map((stock) => (
            <label
              key={stock.id}
              className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-border-default hover:border-border-strong transition-colors"
            >
              <input
                type="checkbox"
                checked={stock.selected}
                onChange={() => toggleStock(stock.id)}
                className="w-4 h-4 rounded accent-brand"
              />
              <span className="text-sm text-text-primary">{stock.name}</span>
            </label>
          ))}
        </div>
      </Panel>

      {/* Bottom Button - 실제 BacktestRunButton 컴포넌트 사용 */}
      <div className="flex justify-center pt-4">
        <BacktestRunButton />
      </div>
    </div>
  );
}
