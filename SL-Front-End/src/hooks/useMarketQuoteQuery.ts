/**
 * 시세 데이터 조회용 React Query 훅
 */

import { useQuery } from "@tanstack/react-query";
import { marketQuoteApi, type SortBy } from "@/lib/api/market-quote";

// 쿼리 키 체계화
export const marketQuoteQueryKey = {
  all: ["marketQuote"] as const,
  lists: () => [...marketQuoteQueryKey.all, "list"] as const,
  list: (sortBy: SortBy, page: number, pageSize: number, userId?: string) =>
    [...marketQuoteQueryKey.lists(), { sortBy, page, pageSize, userId }] as const,
  favorites: () => [...marketQuoteQueryKey.all, "favorites"] as const,
  recentViewed: () => [...marketQuoteQueryKey.all, "recentViewed"] as const,
};

/**
 * 전체 시세 조회 (정렬 기준 적용)
 */
export function useMarketQuotesQuery(
  sortBy: SortBy,
  page = 1,
  pageSize = 50,
  userId?: string
) {
  return useQuery({
    queryKey: marketQuoteQueryKey.list(sortBy, page, pageSize, userId),
    queryFn: () =>
      marketQuoteApi.getMarketQuotes({
        sortBy,
        sortOrder: "desc",
        page,
        pageSize,
        userId,
      }),
    staleTime: 1000 * 30, // 30초
  });
}

/**
 * 관심 종목 목록 조회
 * @param enabled - 쿼리 실행 여부 (로그인 상태에 따라 제어)
 */
export function useFavoriteStocksQuery(enabled = true) {
  return useQuery({
    queryKey: marketQuoteQueryKey.favorites(),
    queryFn: () => marketQuoteApi.getFavorites(),
    staleTime: 1000 * 60, // 1분
    enabled, // 로그인하지 않았으면 실행하지 않음
  });
}

/**
 * 최근 본 종목 목록 조회
 * @param enabled - 쿼리 실행 여부 (로그인 상태에 따라 제어)
 */
export function useRecentViewedStocksQuery(enabled = true) {
  return useQuery({
    queryKey: marketQuoteQueryKey.recentViewed(),
    queryFn: () => marketQuoteApi.getRecentViewed(),
    staleTime: 1000 * 60, // 1분
    enabled, // 로그인하지 않았으면 실행하지 않음
  });
}
