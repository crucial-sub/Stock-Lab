"use client";

import { useEffect, useMemo, useState } from "react";

import { Icon } from "@/components/common/Icon";
import { StockDetailModal } from "@/components/modal/StockDetailModal";
import {
  useAddFavoriteMutation,
  useRemoveFavoriteMutation,
} from "@/hooks/useFavoriteStockMutation";
import {
  useFavoriteStocksQuery,
  useMarketQuotesQuery,
  useRecentViewedStocksQuery,
} from "@/hooks/useMarketQuoteQuery";
import { useAddRecentViewedMutation } from "@/hooks/useRecentViewedMutation";
import { authApi } from "@/lib/api/auth";
import type { SortBy } from "@/lib/api/market-quote";

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
    marketTabs.find((tab) => tab.sortBy === "market_cap") || marketTabs[0],
  );
  const [selectedRow, setSelectedRow] = useState<MarketRow | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [userId, setUserId] = useState<string | undefined>(undefined);

  // 현재 로그인한 사용자 정보 가져오기
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const user = await authApi.getCurrentUser();
        setUserId(user.user_id);
      } catch {
        // 로그인하지 않은 경우 userId는 undefined로 유지
        setUserId(undefined);
      }
    };
    fetchUser();
  }, []);

  // Queries
  const marketQuotesQuery = useMarketQuotesQuery(
    selectedTab.sortBy || "market_cap",
    1,
    50,
    userId,
  );
  // 로그인한 사용자만 즐겨찾기/최근 본 종목 조회
  const favoritesQuery = useFavoriteStocksQuery(!!userId);
  const recentViewedQuery = useRecentViewedStocksQuery(!!userId);

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

    // 즐겨찾기 종목 코드 Set 생성 (최근 본 주식 탭에서 사용)
    const favoriteStockCodes = new Set(
      favoritesQuery.isSuccess && favoritesQuery.data
        ? favoritesQuery.data.items.map((item) => item.stockCode ?? "")
        : [],
    );

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
      isFav: boolean = false,
    ): MarketRow => {
      const changeRateValue = item.changeRate ?? 0;
      const stockCode = item.stockCode ?? item.code ?? "";

      // 즐겨찾기 여부:
      // 1. API 응답의 isFavorite (시세 탭)
      // 2. isFav 파라미터 (즐겨찾기 탭)
      // 3. favoriteStockCodes Set (최근 본 주식 탭)
      const isFavorite =
        item.isFavorite ?? (isFav || favoriteStockCodes.has(stockCode));

      return {
        rank: item.rank ?? index + 1,
        name: item.stockName ?? item.name ?? "",
        code: stockCode,
        price:
          (item.currentPrice ?? item.price)
            ? `${(item.currentPrice ?? item.price)?.toLocaleString()}원`
            : "-",
        change: `${changeRateValue > 0 ? "+" : ""}${changeRateValue.toFixed(2)}%`,
        trend: (item.trend ??
          (changeRateValue > 0
            ? "up"
            : changeRateValue < 0
              ? "down"
              : "flat")) as "up" | "down" | "flat",
        volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
        tradingValue: item.tradingValue
          ? `${Math.floor(item.tradingValue / 100000000).toLocaleString()}억원`
          : "-",
        marketCap: item.marketCap
          ? `${Math.floor(item.marketCap / 100000000).toLocaleString()}억원`
          : "-",
        isFavorite,
      };
    };

    // 탭 타입별 데이터 처리
    if (selectedTab.type === "favorite" && favoritesQuery.data) {
      return favoritesQuery.data.items.map((item, index) =>
        formatStockItem(item, index, true),
      );
    }

    if (selectedTab.type === "recent" && recentViewedQuery.data) {
      return recentViewedQuery.data.items.map((item, index) =>
        formatStockItem(item, index, false),
      );
    }

    // 일반 시세 조회
    if (marketQuotesQuery.data) {
      return marketQuotesQuery.data.items.map((item, index) =>
        formatStockItem(item, index),
      );
    }

    return [];
  }, [
    currentQuery.data,
    selectedTab.type,
    favoritesQuery.data,
    favoritesQuery.isSuccess,
    recentViewedQuery.data,
    marketQuotesQuery.data,
  ]);

  // 검색 필터링 적용
  const filteredRows = useMemo(() => {
    if (!searchQuery.trim()) return rows;

    const query = searchQuery.toLowerCase().trim();
    return rows.filter(
      (row) =>
        row.name.toLowerCase().includes(query) ||
        row.code.toLowerCase().includes(query),
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
      {/*
        Figma 디자인 기준:
        - 컨테이너: 흰색 배경, rounded-lg(12px), shadow-elev-sm
        - 탭: pill 형태 (rounded-full), 활성 탭은 보라색 배경
        - 검색: surface 배경색과 테두리 적용
      */}
      <div className="rounded-lg shadow-elev-sm overflow-hidden">
        <div className="flex flex-col gap-4 p-5">
          {/* 탭과 검색 영역 */}
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            {/* 탭 버튼 그룹 */}
            <div className="flex flex-wrap gap-1">
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
                    className={`rounded-full px-3 py-2 text-[1rem] tracking-[-0.02em] transition ${
                      isActive
                        ? "bg-brand-purple text-white font-semibold"
                        : "text-black font-normal"
                    }`}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* 검색 영역 */}
            <div className="flex items-center gap-3">
              <div className="relative w-full max-w-[260px]">
                <input
                  type="search"
                  placeholder="전략 이름으로 검색하기"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-9 rounded-lg bg-surface border-[0.5px] border-surface py-[0.5rem] px-[0.813rem] text-[0.75rem] text-gray-600 placeholder:text-gray-600 focus:border-brand-purple focus:outline-none"
                />
              </div>
              <button
                type="button"
                className="flex size-9 items-center justify-center rounded-lg bg-brand-purple hover:bg-brand-purple/90 transition"
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

        {/* 테이블 영역 */}
        <div className="px-5 pb-5">
          <div className="flex flex-col gap-2">
            {/* 테이블 헤더 */}
            <div
              className={`${columnTemplate} items-center h-10 border-b-[0.5px] border-gray-400 text-[1rem] text-gray-400`}
            >
              <div className="flex items-center pl-[105px]">
                <span>종목명</span>
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
              filteredRows.map((row, _index) => (
                <div
                  key={row.rank}
                  role="button"
                  tabIndex={0}
                  className={`${columnTemplate} h-12 items-center rounded-lg border-[0.5px] border-surface text-black transition hover:shadow-[0px_0px_9px_0px_rgba(0,0,0,0.1)] cursor-pointer hover:bg-[#1822340D]`}
                  onClick={() => handleRowClick(row)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleRowClick(row);
                    }
                  }}
                >
                  {/* 순위 + 즐겨찾기 + 종목명 */}
                  <div className="flex items-center gap-0">
                    {/* 즐겨찾기 아이콘 */}
                    <button
                      type="button"
                      className="px-3"
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
                        size={24}
                        color={
                          row.isFavorite
                            ? "rgb(172, 100, 255)"
                            : "rgba(0, 0, 0, 0.2)"
                        }
                      />
                    </button>
                    {/* 순위 */}
                    <span className="text-[1rem] font-normal text-black text-right w-8">
                      {row.rank}
                    </span>
                    {/* 종목명 */}
                    <div className="ml-5">
                      <span className="text-[1rem] font-normal text-black">
                        {row.name}
                      </span>
                    </div>
                  </div>

                  {/* 전일 종가 */}
                  <div className="text-[1rem] font-normal text-black text-right">
                    {row.price}
                  </div>

                  {/* 등락률 */}
                  <div
                    className={`text-[1rem] font-normal text-right ${
                      row.trend === "up"
                        ? "text-red-500"
                        : row.trend === "down"
                          ? "text-blue-500"
                          : "text-black"
                    }`}
                  >
                    {row.change}
                  </div>

                  {/* 체결량 */}
                  <div className="text-[1rem] font-normal text-black text-right">
                    {row.volume}
                  </div>

                  {/* 거래대금 */}
                  <div className="text-[1rem] font-normal text-black text-right overflow-hidden text-ellipsis whitespace-nowrap">
                    {row.tradingValue}
                  </div>

                  {/* 시가총액 */}
                  <div className="text-[1rem] font-normal text-black text-right overflow-hidden text-ellipsis whitespace-nowrap">
                    {row.marketCap}
                  </div>
                </div>
              ))
            )}
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
