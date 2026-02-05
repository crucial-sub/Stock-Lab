/**
 * 관심 종목 추가/삭제 Mutation 훅 (Optimistic Update 적용)
 * - 서버 응답을 기다리지 않고 UI 먼저 업데이트
 * - 실패 시 자동 롤백
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  marketQuoteApi,
  type FavoriteStockListResponse,
  type MarketQuoteListResponse,
} from "@/lib/api/market-quote";
import { marketQuoteQueryKey } from "./useMarketQuoteQuery";

interface OptimisticContext {
  previousFavorites: FavoriteStockListResponse | undefined;
  previousLists: MarketQuoteListResponse | undefined;
}

/**
 * 관심 종목 추가 (Optimistic Update)
 */
export function useAddFavoriteMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string, OptimisticContext>({
    mutationFn: (stockCode: string) => marketQuoteApi.addFavorite(stockCode),

    // 1. Optimistic Update
    onMutate: async (stockCode: string) => {
      // 진행중인 refetch 취소
      await queryClient.cancelQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      await queryClient.cancelQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });

      // 이전 데이터 스냅샷
      const previousFavorites =
        queryClient.getQueryData<FavoriteStockListResponse>(
          marketQuoteQueryKey.favorites()
        );
      const previousLists = queryClient.getQueryData<MarketQuoteListResponse>(
        marketQuoteQueryKey.lists()
      );

      // 시세 목록에서 해당 종목 정보 찾기
      const allLists = queryClient.getQueriesData<MarketQuoteListResponse>({
        queryKey: marketQuoteQueryKey.lists(),
      });
      let stockInfo = null;
      for (const [, data] of allLists) {
        if (data?.items) {
          const found = data.items.find((item) => item.code === stockCode);
          if (found) {
            stockInfo = found;
            break;
          }
        }
      }

      // 관심 종목 목록에 즉시 추가
      if (stockInfo) {
        queryClient.setQueryData<FavoriteStockListResponse>(
          marketQuoteQueryKey.favorites(),
          (old) =>
            old
              ? {
                  ...old,
                  items: [
                    ...old.items,
                    {
                      stockCode: stockInfo.code,
                      stockName: stockInfo.name,
                      theme: stockInfo.theme,
                      currentPrice: stockInfo.price,
                      changeRate: stockInfo.changeRate,
                      previousClose: null,
                      volume: stockInfo.volume,
                      tradingValue: stockInfo.tradingValue,
                      marketCap: stockInfo.marketCap,
                      createdAt: new Date().toISOString(),
                    },
                  ],
                  total: old.total + 1,
                }
              : old
        );
      }

      // 시세 목록의 isFavorite 플래그 업데이트
      queryClient.setQueriesData<MarketQuoteListResponse>(
        { queryKey: marketQuoteQueryKey.lists() },
        (old) =>
          old
            ? {
                ...old,
                items: old.items.map((item) =>
                  item.code === stockCode
                    ? { ...item, isFavorite: true }
                    : item
                ),
              }
            : old
      );

      return { previousFavorites, previousLists };
    },

    // 2. 에러 시 롤백
    onError: (_err, _stockCode, context) => {
      if (context?.previousFavorites) {
        queryClient.setQueryData(
          marketQuoteQueryKey.favorites(),
          context.previousFavorites
        );
      }
      if (context?.previousLists) {
        queryClient.setQueryData(
          marketQuoteQueryKey.lists(),
          context.previousLists
        );
      }
    },

    // 3. 완료 후 서버와 동기화
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });
    },
  });
}

/**
 * 관심 종목 삭제 (Optimistic Update)
 */
export function useRemoveFavoriteMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string, OptimisticContext>({
    mutationFn: (stockCode: string) => marketQuoteApi.removeFavorite(stockCode),

    // 1. Optimistic Update
    onMutate: async (stockCode: string) => {
      // 진행중인 refetch 취소
      await queryClient.cancelQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      await queryClient.cancelQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });

      // 이전 데이터 스냅샷
      const previousFavorites =
        queryClient.getQueryData<FavoriteStockListResponse>(
          marketQuoteQueryKey.favorites()
        );
      const previousLists = queryClient.getQueryData<MarketQuoteListResponse>(
        marketQuoteQueryKey.lists()
      );

      // 관심 종목 목록에서 즉시 제거
      queryClient.setQueryData<FavoriteStockListResponse>(
        marketQuoteQueryKey.favorites(),
        (old) =>
          old
            ? {
                ...old,
                items: old.items.filter(
                  (item) => item.stockCode !== stockCode
                ),
                total: old.total - 1,
              }
            : old
      );

      // 시세 목록의 isFavorite 플래그 업데이트
      queryClient.setQueriesData<MarketQuoteListResponse>(
        { queryKey: marketQuoteQueryKey.lists() },
        (old) =>
          old
            ? {
                ...old,
                items: old.items.map((item) =>
                  item.code === stockCode
                    ? { ...item, isFavorite: false }
                    : item
                ),
              }
            : old
      );

      return { previousFavorites, previousLists };
    },

    // 2. 에러 시 롤백
    onError: (_err, _stockCode, context) => {
      if (context?.previousFavorites) {
        queryClient.setQueryData(
          marketQuoteQueryKey.favorites(),
          context.previousFavorites
        );
      }
      if (context?.previousLists) {
        queryClient.setQueryData(
          marketQuoteQueryKey.lists(),
          context.previousLists
        );
      }
    },

    // 3. 완료 후 서버와 동기화
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.favorites(),
      });
      queryClient.invalidateQueries({
        queryKey: marketQuoteQueryKey.lists(),
      });
    },
  });
}
