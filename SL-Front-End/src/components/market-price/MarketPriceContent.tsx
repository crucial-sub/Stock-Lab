"use client";

import { useState, useMemo } from "react";

import { Icon } from "@/components/common/Icon";
import { StockDetailModal } from "@/components/modal/StockDetailModal";
import { type SortBy } from "@/lib/api/market-quote";
import {
  useMarketQuotesQuery,
  useFavoriteStocksQuery,
  useRecentViewedStocksQuery,
} from "@/hooks/useMarketQuoteQuery";
import {
  useAddFavoriteMutation,
  useRemoveFavoriteMutation,
} from "@/hooks/useFavoriteStockMutation";
import { useAddRecentViewedMutation } from "@/hooks/useRecentViewedMutation";

type TabType = "sort" | "favorite" | "recent";

// Figma 디자인 순서대로 탭 정렬: 최근 본 주식 → 정렬 옵션들 → 즐겨찾기한 종목
const marketTabs: { label: string; sortBy?: SortBy; type: TabType }[] = [
  { label: "최근 본 주식", type: "recent" },
  { label: "체결량 순", sortBy: "volume", type: "sort" },
  { label: "등락률 순", sortBy: "change_rate", type: "sort" },
  { label: "거래 대금 순", sortBy: "trading_value", type: "sort" },
  { label: "시가총액 순", sortBy: "market_cap", type: "sort" },
  { label: "즐겨찾기한 종목", type: "favorite" },
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

export function MarketPriceContent() {
  // 기본 탭을 시가총액 순으로 설정 (로그인 불필요)
  const [selectedTab, setSelectedTab] = useState(
    marketTabs.find((tab) => tab.sortBy === "market_cap") || marketTabs[0]
  );
  const [selectedRow, setSelectedRow] = useState<MarketRow | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const todayLabel = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  // Queries
  const marketQuotesQuery = useMarketQuotesQuery(
    selectedTab.sortBy || "market_cap",
    1,
    50
  );
  const favoritesQuery = useFavoriteStocksQuery();
  const recentViewedQuery = useRecentViewedStocksQuery();

  // Mutations
  const addFavoriteMutation = useAddFavoriteMutation();
  const removeFavoriteMutation = useRemoveFavoriteMutation();
  const addRecentViewedMutation = useAddRecentViewedMutation();

  // 현재 탭에 따라 적절한 쿼리 선택
  const currentQuery =
    selectedTab.type === "favorite"
      ? favoritesQuery
      : selectedTab.type === "recent"
        ? recentViewedQuery
        : marketQuotesQuery;

  // 데이터 포맷팅 - 중복 제거 및 최적화
  const rows = useMemo<MarketRow[]>(() => {
    if (!currentQuery.data) return [];

    // 공통 포맷팅 함수
    const formatStockItem = (
      item: {
        stockName?: string;
        name?: string;
        stockCode?: string;
        code?: string;
        currentPrice?: number | null;
        price?: number;
        changeRate?: number | null;
        volume?: number | null;
        tradingValue?: number | null;
        marketCap?: number | null;
        rank?: number;
        trend?: string;
        isFavorite?: boolean;
      },
      index: number,
      isFav: boolean = false
    ): MarketRow => {
      const changeRateValue = item.changeRate ?? 0;
      return {
        rank: item.rank ?? index + 1,
        name: item.stockName ?? item.name ?? "",
        code: item.stockCode ?? item.code ?? "",
        price: (item.currentPrice ?? item.price)
          ? `${(item.currentPrice ?? item.price)!.toLocaleString()}원`
          : "-",
        change: changeRateValue !== 0
          ? `${changeRateValue > 0 ? "+" : ""}${changeRateValue.toFixed(2)}%`
          : "-",
        trend: (item.trend ??
          (changeRateValue > 0
            ? "up"
            : changeRateValue < 0
              ? "down"
              : "flat")) as "up" | "down" | "flat",
        volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
        tradingValue: item.tradingValue
          ? `${Math.floor(item.tradingValue / 100000000)}억원`
          : "-",
        marketCap: item.marketCap
          ? `${Math.floor(item.marketCap / 100000000)}억원`
          : "-",
        isFavorite: item.isFavorite ?? isFav,
      };
    };

    // 탭 타입별 데이터 처리
    if (selectedTab.type === "favorite" && favoritesQuery.data) {
      return favoritesQuery.data.items.map((item, index) =>
        formatStockItem(item, index, true)
      );
    }

    if (selectedTab.type === "recent" && recentViewedQuery.data) {
      return recentViewedQuery.data.items.map((item, index) =>
        formatStockItem(item, index, false)
      );
    }

    // 일반 시세 조회
    if (marketQuotesQuery.data) {
      return marketQuotesQuery.data.items.map((item, index) =>
        formatStockItem(item, index)
      );
    }

    return [];
  }, [
    currentQuery.data,
    selectedTab.type,
    favoritesQuery.data,
    recentViewedQuery.data,
    marketQuotesQuery.data,
  ]);

  // 검색 필터링 적용
  const filteredRows = useMemo(() => {
    if (!searchQuery.trim()) return rows;

    const query = searchQuery.toLowerCase().trim();
    return rows.filter((row) =>
      row.name.toLowerCase().includes(query) ||
      row.code.toLowerCase().includes(query)
    );
  }, [rows, searchQuery]);

  const handleToggleFavorite = (code: string, isFavorite: boolean) => {
    if (isFavorite) {
      removeFavoriteMutation.mutate(code);
    } else {
      addFavoriteMutation.mutate(code);
    }
  };

  const handleRowClick = (row: MarketRow) => {
    addRecentViewedMutation.mutate(row.code);
    setSelectedRow(row);
  };

  // 로그인 필요 여부 체크
  const isAuthRequired =
    (selectedTab.type === "favorite" || selectedTab.type === "recent") &&
    currentQuery.isError;

  const isAuthError =
    isAuthRequired &&
    currentQuery.error &&
    typeof currentQuery.error === "object" &&
    "response" in currentQuery.error &&
    currentQuery.error.response &&
    typeof currentQuery.error.response === "object" &&
    "status" in currentQuery.error.response &&
    (currentQuery.error.response.status === 401 ||
      currentQuery.error.response.status === 403);

  return (
    <>
      <div className="rounded-[8px] bg-white p-6 shadow-card">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap gap-2">
              {marketTabs.map((tab) => {
                const isActive =
                  tab.type === "sort"
                    ? tab.sortBy === selectedTab.sortBy
                    : tab.type === selectedTab.type;
                return (
                  <button
                    key={tab.label}
                    type="button"
                    onClick={() => setSelectedTab(tab)}
                    className={`rounded-[8px] px-[1.5rem] py-[0.5rem] text-[1.25rem] font-semibold transition ${
                      isActive
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
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-[8px] border border-border-default py-[0.7rem] px-[1rem] text-[0.75rem] text-text-body placeholder:text-tag-neutral focus:border-brand-primary focus:outline-none"
                />
              </div>
              <button
                type="button"
                className="flex p-[0.7rem] items-center justify-center rounded-[8px] bg-brand-primary hover:bg-brand-primary/90 transition"
                aria-label="검색"
              >
                <Icon
                  src="/icons/search.svg"
                  alt="검색"
                  size={20}
                  color="white"
                />
              </button>
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

            {currentQuery.isLoading ? (
              <div className="flex items-center justify-center py-20">
                <p className="text-text-body">로딩 중...</p>
              </div>
            ) : isAuthError ? (
              <div className="flex items-center justify-center py-20">
                <p className="text-text-body">로그인 후 이용 가능합니다</p>
              </div>
            ) : currentQuery.isError ? (
              <div className="flex items-center justify-center py-20">
                <p className="text-accent-primary">
                  데이터를 불러오는데 실패했습니다.
                </p>
              </div>
            ) : filteredRows.length === 0 ? (
              <div className="flex items-center justify-center py-20">
                <p className="text-text-body">
                  {searchQuery.trim()
                    ? "검색 결과가 없습니다"
                    : "데이터가 없습니다"}
                </p>
              </div>
            ) : (
              filteredRows.map((row) => (
                <div
                  key={row.rank}
                  className={`${columnTemplate} py-[1rem] items-center rounded-[8px] text-text-body transition hover:bg-white hover:shadow-card cursor-pointer`}
                  onClick={() => handleRowClick(row)}
                >
                  <div className="flex">
                    <button
                      type="button"
                      className="px-[0.5rem]"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleToggleFavorite(row.code, row.isFavorite);
                      }}
                    >
                      <Icon
                        src={
                          row.isFavorite
                            ? "/icons/star_fill.svg"
                            : "/icons/star.svg"
                        }
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
                      <span className="pr-[1rem] text-[1.2rem] font-semibold text-text-strong">
                        {row.rank}
                      </span>
                      <div className="">
                        <span className="text-[1.2rem] font-semibold text-text-strong">
                          {row.name}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-[1.2rem] font-medium text-text-strong text-right">
                    {row.price}
                  </div>
                  <div
                    className={`text-[1.2rem] font-semibold text-right ${
                      row.trend === "up"
                        ? "text-brand-primary"
                        : "text-accent-primary"
                    }`}
                  >
                    {row.change}
                  </div>
                  <div className="text-[1.2rem] font-semibold text-right">
                    {row.volume}
                  </div>
                  <div className="text-[1.2rem] font-semibold text-right">
                    {row.tradingValue}
                  </div>
                  <div className="text-[1.2rem] font-semibold text-right">
                    {row.marketCap}
                  </div>
                </div>
              ))
            )}
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

      <StockDetailModal
        isOpen={!!selectedRow}
        onClose={() => setSelectedRow(null)}
        stockName={selectedRow?.name || ""}
        stockCode={selectedRow?.code || ""}
      />
    </>
  );
}
