/**
 * 함수 관련 React Query 훅
 * - 함수 목록 조회 쿼리를 제공합니다
 */

import { getSubFactorById, getSubFactors } from "@/lib/api";
import type { SubFactor } from "@/types/api";
import { useQuery } from "@tanstack/react-query";

/**
 * 함수 목록 조회 쿼리 키
 */
export const subFactorsQueryKey = {
  all: ["sub-factors"] as const,
  lists: () => [...subFactorsQueryKey.all, "list"] as const,
  list: () => [...subFactorsQueryKey.lists()] as const,
  detail: (id: string) => [...subFactorsQueryKey.all, "detail", id] as const,
};

/**
 * 함수 목록 조회 훅
 * - 모든 함수 목록을 조회합니다
 * - SSR에서 prefetch된 데이터를 자동으로 사용합니다
 *
 * @returns 함수 목록 쿼리 결과
 */
export function useSubFactorsQuery() {
  return useQuery<SubFactor[], Error>({
    queryKey: subFactorsQueryKey.list(),
    queryFn: () => getSubFactors(false),
  });
}

/**
 * 함수 상세 조회 훅
 * - 특정 함수의 상세 정보를 조회합니다
 *
 * @param subFactorId - 함수 ID
 * @returns 함수 상세 쿼리 결과
 */
export function useSubFactorQuery(subFactorId: string) {
  return useQuery<SubFactor, Error>({
    queryKey: subFactorsQueryKey.detail(subFactorId),
    queryFn: () => getSubFactorById(subFactorId, false),
    enabled: !!subFactorId,
  });
}
