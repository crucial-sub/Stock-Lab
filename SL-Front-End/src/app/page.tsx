"use client";

import Image from "next/image";
import { useState } from "react";
import { FilterGroup } from "@/components/common";
import { HOME_PERIOD_TABS, HOME_SORT_TABS, MOCK_STOCKS } from "@/constants";

export default function Home() {
  const [activeSort, setActiveSort] = useState("asc");
  const [activePeriod, setActivePeriod] = useState("1d");
  const [favorites, setFavorites] = useState<number[]>([]);
  const [hoveredStock, setHoveredStock] = useState<number | null>(null);

  const toggleFavorite = (id: number) => {
    setFavorites((prev) =>
      prev.includes(id) ? prev.filter((fav) => fav !== id) : [...prev, id],
    );
  };

  return (
    <div className="quant-container w-[1000px] pt-[40px]">
      {/* Filter Section - 한 줄에 나란히 배치 */}
      <div className="flex items-center justify-center gap-4">
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
      <div className="py-[40px] px-[12px] text-[1rem]">
        <span className="text-text-tertiary">순위 및 종목명, 2025년 10월 27일 기준</span>
        <span className="text-text-tertiary ml-[200px]">전일 종가</span>
        <span className="text-text-tertiary ml-[172px]">등락률</span>
        <span className="text-text-tertiary ml-[164px]">거래대금</span>
      </div>

      {/* Stock List */}
      <div className="space-y-[12px]">
        {MOCK_STOCKS.map((stock) => {
          const isHovered = hoveredStock === stock.id;
          const isFavorite = favorites.includes(stock.id);

          return (
            <article
              key={stock.id}
              className="list-item"
              onMouseEnter={() => setHoveredStock(stock.id)}
              onMouseLeave={() => setHoveredStock(null)}
            >
              <div className="flex w-full items-center gap-6 px-[12px] text-[1.3rem]">
                {/* Star and Rank */}
                <div className="flex w-[60px] items-center gap-3">
                  <button
                    type="button"
                    onClick={() => toggleFavorite(stock.id)}
                    className="flex h-[40px] w-[40px] items-center justify-center transition-transform duration-200 hover:scale-110"
                    aria-label={isFavorite ? "즐겨찾기 해제" : "즐겨찾기 추가"}
                    aria-pressed={isFavorite}
                  >
                    <Image
                      src={isFavorite ? "/icons/star_selected.svg" : "/icons/star.svg"}
                      alt=""
                      width={40}
                      height={40}
                    />
                  </button>
                  <span
                    className={`font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                  >
                    {stock.id}
                  </span>
                </div>

                {/* Stock Name */}
                <div
                  className={`flex w-[200px] items-center font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {stock.name}
                </div>

                {/* Current Price */}
                <div
                  className={`flex flex-1 items-center justify-end font-medium ${isHovered ? "text-hover" : "text-normal"}`}
                >
                  {stock.currentPrice.toLocaleString()}원
                </div>

                {/* Change Rate */}
                <div
                  className={`flex flex-1 w-[120px] items-center justify-end font-medium ${stock.changeRate >= 0
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
                  className={`flex flex-1 w-[120px] items-center justify-end ${isHovered ? "text-hover" : "text-normal"}`}
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
