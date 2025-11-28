"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

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

/**
 * 데스크톱용 테이블 그리드 템플릿
 * 모바일에서는 카드 뷰로 전환되어 사용되지 않음
 */
const columnTemplate = "grid grid-cols-[2fr,1fr,1fr,1fr,1fr,1fr] gap-4";

const DEFAULT_MARKET_TAB =
  marketTabs.find((tab) => tab.sortBy === "market_cap") || marketTabs[0];

const findTabByParam = (param: string | null) => {
  if (!param) return null;
  if (param === "favorite" || param === "recent") {
    return marketTabs.find((tab) => tab.type === param) ?? null;
  }
  return marketTabs.find((tab) => tab.sortBy === param) ?? null;
};

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
  const searchParams = useSearchParams();
  const initialTab = findTabByParam(searchParams.get("tab")) ?? DEFAULT_MARKET_TAB;

  const [selectedTab, setSelectedTab] = useState(initialTab);
  const [selectedStock, setSelectedStock] = useState<{ name: string; code: string } | null>(null);
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

  // Queries (검색어 포함)
  const marketQuotesQuery = useMarketQuotesQuery(
    selectedTab.sortBy || "market_cap",
    1,
    50,
    userId,
    searchQuery.trim() || undefined, // 검색어가 있으면 전달
  );
  // 로그인한 사용자만 즐겨찾기/최근 본 종목 조회
  const favoritesQuery = useFavoriteStocksQuery(!!userId);
  const recentViewedQuery = useRecentViewedStocksQuery(!!userId);

  // Mutations
  const addFavoriteMutation = useAddFavoriteMutation();
  const removeFavoriteMutation = useRemoveFavoriteMutation();
  const addRecentViewedMutation = useAddRecentViewedMutation();

  useEffect(() => {
    const queryTab = findTabByParam(searchParams.get("tab"));
    if (queryTab && queryTab !== selectedTab) {
      setSelectedTab(queryTab);
    }
  }, [searchParams, selectedTab]);

  useEffect(() => {
    const stockCode = searchParams.get("stockCode");
    if (!stockCode) return;
    const stockName = searchParams.get("stockName") ?? stockCode;
    setSelectedStock({ name: stockName, code: stockCode });
  }, [searchParams]);

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

  // 검색은 이제 Backend에서 처리 (filteredRows 제거)

  const handleToggleFavorite = (code: string, isFavorite: boolean) => {
    if (isFavorite) {
      removeFavoriteMutation.mutate(code);
    } else {
      addFavoriteMutation.mutate(code);
    }
  };

  const handleRowClick = (row: MarketRow) => {
    addRecentViewedMutation.mutate(row.code);
    setSelectedStock({ name: row.name, code: row.code });
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
      <div className="mx-auto w-full max-w-[1000px]">
          <div className="flex flex-col p-4 sm:p-5">
            {/* 탭과 검색 영역 - 모바일에서 세로 정렬, 데스크톱에서 가로 정렬 */}
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              {/* 탭 버튼 그룹 - 모바일에서 가로 스크롤 */}
              <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0 sm:overflow-visible">
                <div className="flex gap-1 min-w-max sm:flex-wrap sm:min-w-0">
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
                        className={[
                          "rounded-full px-4 py-2 text-sm sm:text-base tracking-[-0.02em] transition",
                          "whitespace-nowrap min-h-[2.75rem] sm:min-h-0",
                          isActive
                            ? "bg-brand-purple text-white font-semibold"
                            : "text-black font-normal",
                        ].join(" ")}
                      >
                        {tab.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 검색 영역 - 모바일에서 전체 너비 */}
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:flex-none sm:w-[240px]">
                  <input
                    type="search"
                    placeholder="종목명/종목코드로 검색하기"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className={[
                      "w-full h-11 sm:h-9 rounded-xl",
                      "bg-surface border-[0.5px] border-surface",
                      "py-2 pl-3 pr-4 text-base sm:text-xs",
                      "text-gray-600 placeholder:text-gray-600",
                      "focus:border-brand-purple focus:outline-none",
                    ].join(" ")}
                  />
                </div>
                <button
                  type="button"
                  className="flex w-11 h-11 sm:w-9 sm:h-9 items-center justify-center rounded-xl bg-brand-purple hover:bg-brand-purple/90 transition shrink-0"
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

          {/* 데이터 영역 - 모바일: 카드 뷰, 데스크톱: 테이블 뷰 */}
          <div className="p-4 sm:p-5">
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
            ) : rows.length === 0 ? (
              <div className="flex items-center justify-center">
                <p className="font-semibold text-base pt-20 text-muted">
                  {searchQuery.trim()
                    ? "검색 결과가 없습니다"
                    : "데이터가 없습니다"}
                </p>
              </div>
            ) : (
              <>
                {/* 데스크톱 테이블 뷰 - md 이상에서만 표시 */}
                <div className="hidden md:block overflow-x-auto">
                  <div className="flex flex-col gap-2 min-w-[720px]">
                    {/* 테이블 헤더 */}
                    <div
                      className={`${columnTemplate} items-center py-2 border-b-[0.5px] border-[#C8C8C8] text-base text-[#C8C8C8] font-normal`}
                    >
                      <div className="flex items-center pl-[60px]">
                        <span>종목명</span>
                      </div>
                      <div className="text-right">전일 종가</div>
                      <div className="text-right">등락률</div>
                      <div className="text-right">체결량</div>
                      <div className="text-right">거래대금</div>
                      <div className="text-right pr-2">시가총액</div>
                    </div>

                    {rows.map((row) => (
                      <div
                        key={row.rank}
                        role="button"
                        tabIndex={0}
                        className={`${columnTemplate} h-12 items-center rounded-xl text-black transition hover:border-[0.5px] hover:border-[#646464] hover:shadow-[0px_0px_9px_0px_rgba(0,0,0,0.1)] cursor-pointer hover:bg-[#1822340D]`}
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
                          <button
                            type="button"
                            className="flex items-center justify-center p-2 min-w-[2.75rem] min-h-[2.75rem]"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleToggleFavorite(row.code, row.isFavorite);
                            }}
                          >
                            <Icon
                              src={row.isFavorite ? "/icons/star_fill.svg" : "/icons/star.svg"}
                              alt="즐겨찾기"
                              size={24}
                              color={row.isFavorite ? "rgb(172, 100, 255)" : "rgba(0, 0, 0, 0.2)"}
                            />
                          </button>
                          <span className="text-base font-normal text-black text-right w-2">
                            {row.rank}
                          </span>
                          <div className="ml-5">
                            <span className="text-base font-semibold text-black">{row.name}</span>
                          </div>
                        </div>
                        <div className="text-base font-normal text-black text-right">{row.price}</div>
                        <div className={`text-base font-normal text-right ${
                          row.trend === "up" ? "text-red-500" : row.trend === "down" ? "text-blue-500" : "text-black"
                        }`}>
                          {row.change}
                        </div>
                        <div className="text-base font-normal text-black text-right">{row.volume}</div>
                        <div className="text-base font-normal text-black text-right overflow-hidden text-ellipsis whitespace-nowrap">
                          {row.tradingValue}
                        </div>
                        <div className="text-base font-normal text-black text-right overflow-hidden text-ellipsis whitespace-nowrap pr-2">
                          {row.marketCap}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 모바일 카드 뷰 - md 미만에서만 표시 */}
                <div className="md:hidden flex flex-col gap-3">
                  {rows.map((row) => (
                    <div
                      key={row.rank}
                      role="button"
                      tabIndex={0}
                      className="p-4 rounded-xl border border-gray-100 bg-white shadow-sm active:bg-gray-50 transition"
                      onClick={() => handleRowClick(row)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleRowClick(row);
                        }
                      }}
                    >
                      {/* 상단: 순위, 종목명, 즐겨찾기 */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-500 w-6">{row.rank}</span>
                          <span className="text-base font-semibold text-black">{row.name}</span>
                        </div>
                        <button
                          type="button"
                          className="flex items-center justify-center w-11 h-11 -mr-2"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleToggleFavorite(row.code, row.isFavorite);
                          }}
                        >
                          <Icon
                            src={row.isFavorite ? "/icons/star_fill.svg" : "/icons/star.svg"}
                            alt="즐겨찾기"
                            size={24}
                            color={row.isFavorite ? "rgb(172, 100, 255)" : "rgba(0, 0, 0, 0.2)"}
                          />
                        </button>
                      </div>

                      {/* 중앙: 가격, 등락률 */}
                      <div className="flex items-baseline justify-between mb-3">
                        <span className="text-lg font-semibold text-black">{row.price}</span>
                        <span className={`text-base font-semibold ${
                          row.trend === "up" ? "text-red-500" : row.trend === "down" ? "text-blue-500" : "text-black"
                        }`}>
                          {row.change}
                        </span>
                      </div>

                      {/* 하단: 체결량, 거래대금, 시가총액 */}
                      <div className="grid grid-cols-3 gap-2 text-center border-t border-gray-100 pt-3">
                        <div>
                          <p className="text-xs text-gray-400 mb-0.5">체결량</p>
                          <p className="text-sm text-black truncate">{row.volume}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-0.5">거래대금</p>
                          <p className="text-sm text-black truncate">{row.tradingValue}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400 mb-0.5">시가총액</p>
                          <p className="text-sm text-black truncate">{row.marketCap}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
      </div>

      <StockDetailModal
        isOpen={!!selectedStock}
        onClose={() => setSelectedStock(null)}
        stockName={selectedStock?.name || ""}
        stockCode={selectedStock?.code || ""}
      />
    </>
  );
}
