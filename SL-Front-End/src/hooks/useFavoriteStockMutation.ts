/**
 * 관심 종목 추가/삭제 Mutation 훅
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { marketQuoteApi } from "@/lib/api/market-quote";
import { marketQuoteQueryKey } from "./useMarketQuoteQuery";

/**
 * 관심 종목 추가
 */
export function useAddFavoriteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (stockCode: string) => marketQuoteApi.addFavorite(stockCode),
    onSuccess: () => {
      // 관심 종목 목록 캐시 갱신
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      // 전체 시세 목록도 갱신 (isFavorite 플래그 업데이트)
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });
    },
  });
}

/**
 * 관심 종목 삭제
 */
export function useRemoveFavoriteMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (stockCode: string) =>
      marketQuoteApi.removeFavorite(stockCode),
    onSuccess: () => {
      // 관심 종목 목록 캐시 갱신
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      // 전체 시세 목록도 갱신 (isFavorite 플래그 업데이트)
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });
    },
  });
}
