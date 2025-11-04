"use client";

import { useState } from "react";
import { FilterGroup } from "@/components/common";
import { HOME_PERIOD_TABS, HOME_SORT_TABS, MOCK_STOCKS } from "@/constants";

export default function Home() {
  const [activeSort, setActiveSort] = useState("asc");
  const [activePeriod, setActivePeriod] = useState("1d");
  const [favorites, setFavorites] = useState<number[]>([1]);
  const [hoveredStock, setHoveredStock] = useState<number | null>(null);

  const toggleFavorite = (id: number) => {
    setFavorites((prev) =>
      prev.includes(id) ? prev.filter((fav) => fav !== id) : [...prev, id],
    );
  };

  return (
    <div className="quant-container py-8 space-y-6">
      {/* Filter Section - 한 줄에 나란히 배치 */}
      <div className="flex items-center gap-4">
        <FilterGroup
          items={HOME_SORT_TABS}
          activeId={activeSort}
          onChange={setActiveSort}
        />
        <FilterGroup
          items={HOME_PERIOD_TABS}
          activeId={activePeriod}
          onChange={setActivePeriod}
        />
      </div>

      {/* Date Header */}
      <div className="flex items-center gap-6 px-5 text-sm">
        <span className="text-text-tertiary">순위 및 종목명</span>
        <span className="text-text-tertiary">2025년 10월 27일 기준</span>
      </div>

      {/* Stock List */}
      <div className="space-y-3">
        {MOCK_STOCKS.map((stock) => {
          const isHovered = hoveredStock === stock.id;
          const isFavorite = favorites.includes(stock.id);

          return (
            <article
              key={stock.id}
              className={`list-item ${isFavorite ? "is-selected" : ""}`}
              onMouseEnter={() => setHoveredStock(stock.id)}
              onMouseLeave={() => setHoveredStock(null)}
            >
              <div className="grid grid-cols-[60px_200px_1fr_120px_120px] gap-6 items-center w-full px-5">
                {/* Star and Rank */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => toggleFavorite(stock.id)}
                    className="text-lg"
                  >
                    {isFavorite ? "⭐" : "☆"}
                  </button>
                  <div className="w-px h-8 bg-border-subtle transform rotate-0" />
                  <span
                    className={`text-sm font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                  >
                    {stock.id}
                  </span>
                </div>

                {/* Stock Name */}
                <div
                  className={`text-base font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {stock.name}
                </div>

                {/* Current Price */}
                <div
                  className={`text-base font-medium text-right ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {stock.currentPrice.toLocaleString()}원
                </div>

                {/* Change Rate */}
                <div
                  className={`text-base font-medium text-right ${
                    stock.changeRate >= 0
                      ? isHovered
                        ? "value-positive"
                        : "value-positive-normal"
                      : isHovered
                        ? "value-negative"
                        : "value-negative-normal"
                  }`}
                >
                  {stock.changeRate >= 0 ? "+" : ""}
                  {stock.changeRate}%
                </div>

                {/* Trading Volume */}
                <div
                  className={`text-sm ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {Math.round(stock.tradingVolume / 100000000)}억원
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {/* Divider */}
      <div className="h-px bg-border-subtle" />

      {/* Load More Link */}
      <div className="text-center py-4">
        <button
          type="button"
          className="text-sm text-text-tertiary hover:text-text-primary transition-colors"
        >
          클릭하여 더 불러오기
        </button>
      </div>
    </div>
  );
}
