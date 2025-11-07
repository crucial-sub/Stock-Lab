"use client";

import { useState } from "react";

import { Icon } from "@/components/common/Icon";

const marketTabs = [
  "최근 본 주식",
  "체결량 순",
  "등락률 순",
  "거래 대금 순",
  "시가총액 순",
];

const mockMarketRows = [
  {
    rank: 1,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "+5.55%",
    trend: "up" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: true,
  },
  {
    rank: 2,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "-5.55%",
    trend: "down" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: true,
  },
  {
    rank: 3,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "+5.55%",
    trend: "up" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 4,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "-5.55%",
    trend: "down" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 5,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "+5.55%",
    trend: "up" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 6,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "-5.55%",
    trend: "down" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 7,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "+5.55%",
    trend: "up" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 8,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "-5.55%",
    trend: "down" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 9,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "+5.55%",
    trend: "up" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
  {
    rank: 10,
    name: "크래프톤",
    code: "KRAFTON",
    price: "263,500원",
    change: "-5.55%",
    trend: "down" as const,
    volume: "304,016주",
    tradingValue: "439억원",
    marketCap: "439억원",
    asOfDate: "2025.12.31",
    isFavorite: false,
  },
];

const columnTemplate = "grid grid-cols-[2.6fr,1fr,1fr,1fr,1fr,1fr] gap-4";

export default function MarketPricePage() {
  const [selectedTab, setSelectedTab] = useState(marketTabs[0]);
  const todayLabel = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-[1.8rem] font-semibold text-text-strong">국내 주식 시세</h1>
      <div className="rounded-[8px] bg-white p-6 shadow-card">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-2">
              {marketTabs.map((tab) => {
                const isActive = tab === selectedTab;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setSelectedTab(tab)}
                    className={`rounded-[8px] px-[1.5rem] py-[0.5rem] text-[1.25rem] font-semibold transition ${isActive
                      ? "bg-brand-primary text-white"
                      : "text-text-body font-normal"
                      }`}
                  >
                    {tab}
                  </button>
                );
              })}
            </div>
            <div className="flex items-center gap-[0.75rem]">
              <div className="relative w-full max-w-[15rem]">
                <input
                  type="search"
                  placeholder="종목 이름으로 검색하기"
                  className="w-full rounded-[8px] border border-border-default py-[0.7rem] px-[1rem] text-[0.75rem] text-text-body placeholder:text-tag-neutral focus:border-brand-primary focus:outline-none"
                />
              </div>
              <div className="flex p-[0.7rem] items-center justify-center rounded-[8px] bg-[#F0F0F0]">
                <Icon src="/icons/search.svg" alt="검색" size={20} color="var(--color-text-strong)" />
              </div>
            </div>
          </div>
        </div>

        <div className="pt-[1rem] overflow-hidden">
          <div className="flex flex-col gap-3 px-2 py-2">
            <div
              className={`${columnTemplate} items-center py-[0.7rem] text-[1rem] font-normal text-tag-neutral`}
            >
              <div className="flex items-center">
                <span className="inline-block" />
                <div className="flex flex-col">
                  <span>순위 및 종목 {todayLabel} 기준</span>
                </div>
              </div>
              <div className="text-right">전일 종가</div>
              <div className="text-right">등락률</div>
              <div className="text-right">체결량</div>
              <div className="text-right">거래대금</div>
              <div className="text-right">시가총액</div>
            </div>

            {mockMarketRows.map((row) => (
              <div
                key={row.rank}
                className={`${columnTemplate} py-[1rem] items-center text-text-body transition hover:bg-white hover:shadow-card`}
              >
                <div className="flex">
                  <button type="button" className="px-[0.5rem] py-[0rem]">
                    <Icon
                      src={row.isFavorite ? "/icons/star_selected.svg" : "/icons/star.svg"}
                      alt="즐겨찾기"
                      size={28}
                      color={
                        row.isFavorite
                          ? "var(--color-brand-primary)"
                          : "var(--color-border-default)"
                      }
                    />
                  </button>
                  <div className="flex">
                    <span className="pr-[1rem] text-[1.2rem] font-semibold text-text-strong">{row.rank}</span>
                    <div className="">
                      <span className="text-[1.2rem] font-semibold text-text-strong">{row.name}</span>
                    </div>
                  </div>
                </div>
                <div className="text-[1.2rem] font-medium text-text-strong text-right">{row.price}</div>
                <div
                  className={`text-[1.2rem] font-semibold text-right ${row.trend === "up" ? "text-brand-primary" : "text-accent-primary"
                    }`}
                >
                  {row.change}
                </div>
                <div className="text-[1.2rem] font-semibold text-right">{row.volume}</div>
                <div className="text-[1.2rem] font-semibold text-right">{row.tradingValue}</div>
                <div className="text-[1.2rem] font-semibold text-right">{row.marketCap}</div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-center gap-6 px-4 py-4 text-sm text-text-body">
            <button type="button" className="text-tag-neutral">
              &lt;
            </button>
            <span className="text-base font-semibold text-text-strong">1</span>
            <button type="button" className="text-tag-neutral">
              &gt;
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
