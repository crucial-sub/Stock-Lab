/**
 * 최근 본 종목 추가/삭제 Mutation 훅
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marketQuoteApi } from "@/lib/api/market-quote";
import { marketQuoteQueryKey } from "./useMarketQuoteQuery";

/**
 * 최근 본 종목 추가 (자동 기록)
 */
export function useAddRecentViewedMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (stockCode: string) =>
      marketQuoteApi.addRecentViewed(stockCode),
    onSuccess: () => {
      // 최근 본 종목 목록 캐시 갱신
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.recentViewed(),
      });
    },
  });
}

/**
 * 최근 본 종목 삭제 (수동 삭제)
 */
export function useRemoveRecentViewedMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (stockCode: string) =>
      marketQuoteApi.removeRecentViewed(stockCode),
    onSuccess: () => {
      // 최근 본 종목 목록 캐시 갱신
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.recentViewed(),
      });
    },
  });
}
