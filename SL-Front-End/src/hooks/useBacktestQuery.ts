/**
 * 백테스트 관련 React Query 훅
 * - 백테스트 실행, 결과 조회, 폴링 등의 쿼리를 제공합니다
 */

import {
  useQuery,
  useMutation,
  useInfiniteQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  runBacktest,
  getBacktestResult,
  getBacktestList,
  getBacktestTrades,
  getBacktestYieldPoints,
  getBacktestStatus,
  deleteBacktest,
} from "@/lib/api";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  BacktestResult,
  PaginatedResponse,
  PaginationParams,
} from "@/types/api";

/**
 * 백테스트 쿼리 키
 */
export const backtestQueryKey = {
  all: ["backtest"] as const,
  lists: () => [...backtestQueryKey.all, "list"] as const,
  list: (params?: PaginationParams) =>
    [...backtestQueryKey.lists(), params] as const,
  details: () => [...backtestQueryKey.all, "detail"] as const,
  detail: (id: string) => [...backtestQueryKey.details(), id] as const,
  trades: (id: string) => [...backtestQueryKey.detail(id), "trades"] as const,
  yieldPoints: (id: string) =>
    [...backtestQueryKey.detail(id), "yield-points"] as const,
  status: (id: string) => [...backtestQueryKey.detail(id), "status"] as const,
};

/**
 * 백테스트 실행 뮤테이션 훅
 * - 백테스트를 실행합니다
 *
 * @returns 백테스트 실행 뮤테이션
 */
export function useRunBacktestMutation() {
  const queryClient = useQueryClient();

  return useMutation<BacktestRunResponse, Error, BacktestRunRequest>({
    mutationFn: runBacktest,
    onSuccess: () => {
      // 백테스트 목록 쿼리 무효화
      queryClient.invalidateQueries({ queryKey: backtestQueryKey.lists() });
    },
  });
}

/**
 * 백테스트 결과 조회 훅
 * - 완료된 백테스트의 결과를 조회합니다
 * - SSR에서 prefetch된 데이터를 자동으로 사용합니다
 *
 * @param backtestId - 백테스트 ID
 * @param enabled - 쿼리 활성화 여부
 * @returns 백테스트 결과 쿼리
 */
export function useBacktestResultQuery(
  backtestId: string,
  enabled = true,
) {
  return useQuery<BacktestResult, Error>({
    queryKey: backtestQueryKey.detail(backtestId),
    queryFn: () => getBacktestResult(backtestId, false),
    enabled: enabled && !!backtestId,
  });
}

/**
 * 백테스트 목록 조회 훅
 * - 사용자의 백테스트 목록을 조회합니다
 *
 * @param params - 페이지네이션 파라미터
 * @returns 백테스트 목록 쿼리
 */
export function useBacktestListQuery(params?: PaginationParams) {
  return useQuery<PaginatedResponse<BacktestResult>, Error>({
    queryKey: backtestQueryKey.list(params),
    queryFn: () => getBacktestList(params, false),
  });
}

/**
 * 백테스트 매매 내역 무한 스크롤 훅
 * - 매매 내역을 페이지네이션으로 조회합니다
 * - 대용량 데이터 처리를 위해 무한 스크롤을 지원합니다
 *
 * @param backtestId - 백테스트 ID
 * @param limit - 페이지당 아이템 수
 * @returns 무한 스크롤 쿼리
 */
export function useBacktestTradesInfiniteQuery(
  backtestId: string,
  limit = 50,
) {
  return useInfiniteQuery<
    PaginatedResponse<BacktestResult["trades"][number]>,
    Error
  >({
    queryKey: [...backtestQueryKey.trades(backtestId), { limit }],
    queryFn: ({ pageParam = 1 }) =>
      getBacktestTrades(backtestId, { page: pageParam as number, limit }, false),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
    enabled: !!backtestId,
  });
}

/**
 * 백테스트 수익률 차트 데이터 무한 스크롤 훅
 * - 수익률 차트 데이터를 페이지네이션으로 조회합니다
 * - 5년치 대용량 데이터 처리를 위해 무한 스크롤을 지원합니다
 *
 * @param backtestId - 백테스트 ID
 * @param limit - 페이지당 아이템 수
 * @returns 무한 스크롤 쿼리
 */
export function useBacktestYieldPointsInfiniteQuery(
  backtestId: string,
  limit = 100,
) {
  return useInfiniteQuery<
    PaginatedResponse<BacktestResult["yieldPoints"][number]>,
    Error
  >({
    queryKey: [...backtestQueryKey.yieldPoints(backtestId), { limit }],
    queryFn: ({ pageParam = 1 }) =>
      getBacktestYieldPoints(backtestId, { page: pageParam as number, limit }, false),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const { page, totalPages } = lastPage.pagination;
      return page < totalPages ? page + 1 : undefined;
    },
    enabled: !!backtestId,
  });
}

/**
 * 백테스트 상태 폴링 훅
 * - 백테스트 실행 상태를 주기적으로 확인합니다
 * - 백테스트가 완료되면 자동으로 폴링을 중단합니다
 *
 * @param backtestId - 백테스트 ID
 * @param enabled - 폴링 활성화 여부
 * @param interval - 폴링 간격 (밀리초, 기본 2초)
 * @returns 백테스트 상태 쿼리
 */
export function useBacktestStatusQuery(
  backtestId: string,
  enabled = true,
  interval = 2000,
) {
  return useQuery<
    { status: BacktestResult["status"]; progress?: number },
    Error
  >({
    queryKey: backtestQueryKey.status(backtestId),
    queryFn: () => getBacktestStatus(backtestId),
    enabled: enabled && !!backtestId,
    // 백테스트가 완료되거나 실패하면 폴링 중단
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return interval;
    },
    // 폴링 중에는 항상 재요청
    refetchIntervalInBackground: true,
  });
}

/**
 * 백테스트 삭제 뮤테이션 훅
 * - 백테스트를 삭제합니다
 *
 * @returns 백테스트 삭제 뮤테이션
 */
export function useDeleteBacktestMutation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteBacktest,
    onSuccess: (_, backtestId) => {
      // 백테스트 목록 쿼리 무효화
      queryClient.invalidateQueries({ queryKey: backtestQueryKey.lists() });
      // 삭제된 백테스트 상세 쿼리 제거
      queryClient.removeQueries({
        queryKey: backtestQueryKey.detail(backtestId),
      });
    },
  });
}
