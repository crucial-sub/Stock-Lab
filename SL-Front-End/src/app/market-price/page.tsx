"use client";

import { useState, useEffect } from "react";

import { Icon } from "@/components/common/Icon";
import { StockInfoCard } from "@/components/market-price/StockInfoCard";
import { marketQuoteApi, type SortBy } from "@/lib/api/market-quote";

const marketTabs: { label: string; sortBy: SortBy }[] = [
  { label: "체결량 순", sortBy: "volume" },
  { label: "등락률 순", sortBy: "change_rate" },
  { label: "거래 대금 순", sortBy: "trading_value" },
  { label: "시가총액 순", sortBy: "market_cap" },
];

const columnTemplate = "grid grid-cols-[2.6fr,1fr,1fr,1fr,1fr,1fr] gap-4";

type MarketRow = {
  rank: number;
  name: string;
  code: string;
  price: string;
  change: string;
  trend: "up" | "down" | "flat";
  volume: string;
  tradingValue: string;
  marketCap: string;
  isFavorite: boolean;
};

export default function MarketPricePage() {
  const [selectedTab, setSelectedTab] = useState(marketTabs[3]); // 시가총액 순 기본값
  const [rows, setRows] = useState<MarketRow[]>([]);
  const [selectedRow, setSelectedRow] = useState<MarketRow | null>(null);
  const todayLabel = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // API 데이터 fetch
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await marketQuoteApi.getMarketQuotes({
          sortBy: selectedTab.sortBy,
          sortOrder: "desc",
          page: 1,
          pageSize: 50,
        });

        console.log("API Response:", response);

        // API 데이터를 표시 형식으로 변환
        const formattedRows = response.items.map((item) => ({
          rank: item.rank,
          name: item.name,
          code: item.code,
          price: `${item.price.toLocaleString()}원`,
          change: `${item.changeRate > 0 ? "+" : ""}${item.changeRate.toFixed(2)}%`,
          trend: item.trend as "up" | "down" | "flat",
          volume: `${item.volume.toLocaleString()}주`,
          tradingValue: `${Math.floor(item.tradingValue / 100000000)}억원`,
          marketCap: item.marketCap ? `${Math.floor(item.marketCap / 100000000)}억원` : "-",
          isFavorite: item.isFavorite,
        }));

        console.log("Formatted Rows:", formattedRows);
        setRows(formattedRows);
      } catch (error) {
        console.error("시세 데이터 조회 실패:", error);
      }
    };

    fetchData();
  }, [selectedTab]);

  const handleToggleFavorite = (rank: number) => {
    setRows((prev) =>
      prev.map((row) =>
        row.rank === rank ? { ...row, isFavorite: !row.isFavorite } : row,
      ),
    );
  };

  return (
    <>
    <section className="flex flex-col gap-4">
      <h1 className="text-[1.8rem] font-semibold text-text-strong">국내 주식 시세</h1>
      <div className="rounded-[8px] bg-white p-6 shadow-card">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-2">
              {marketTabs.map((tab) => {
                const isActive = tab.sortBy === selectedTab.sortBy;
                return (
                  <button
                    key={tab.sortBy}
                    type="button"
                    onClick={() => setSelectedTab(tab)}
                    className={`rounded-[8px] px-[1.5rem] py-[0.5rem] text-[1.25rem] font-semibold transition ${isActive
                      ? "bg-brand-primary text-white"
                      : "text-text-body font-normal"
                      }`}
                  >
                    {tab.label}
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
          <div className="flex flex-col gap-3 px-1">
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

            {rows.map((row) => (
              <div
                key={row.rank}
                className={`${columnTemplate} py-[1rem] items-center rounded-[8px] text-text-body transition hover:bg-white hover:shadow-card cursor-pointer`}
                onClick={() => setSelectedRow(row)}
              >
                <div className="flex">
                  <button
                    type="button"
                    className="px-[0.5rem]"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleToggleFavorite(row.rank);
                    }}
                  >
                    <Icon
                      src={row.isFavorite ? "/icons/star_fill.svg" : "/icons/star.svg"}
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

    {selectedRow && (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        onClick={() => setSelectedRow(null)}
      >
        <div
          className="relative rounded-[8px] max-h-[70vh] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="relative flex items-center shadow-header bg-white px-[0.5rem] py-[0.8rem]">
            <h2 className="absolute left-1/2 -translate-x-1/2 text-[0.9rem] font-normal text-text-strong">
              {selectedRow.name} 종목 정보
            </h2>
            <button
              type="button"
              className="mr-[0.25rem] ml-auto flex h-3 w-3 rounded-full bg-[#FF6464]"
              aria-label="닫기"
              onClick={() => setSelectedRow(null)}
            />
          </div>
          <StockInfoCard name={selectedRow.name} code={selectedRow.code} />
        </div>
      </div>
    )}
    </>
  );
}
