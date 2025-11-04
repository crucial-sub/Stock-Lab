/**
 * 팩터 관련 React Query 훅
 * - 팩터 목록 조회 쿼리를 제공합니다
 */

import { useQuery } from "@tanstack/react-query";
import { getFactors, getFactorsByCategory, getFactorById } from "@/lib/api";
import type { Factor } from "@/types/api";

/**
 * 팩터 목록 조회 쿼리 키
 */
export const factorsQueryKey = {
  all: ["factors"] as const,
  lists: () => [...factorsQueryKey.all, "list"] as const,
  list: () => [...factorsQueryKey.lists()] as const,
  byCategory: (category: string) =>
    [...factorsQueryKey.lists(), { category }] as const,
  detail: (id: string) => [...factorsQueryKey.all, "detail", id] as const,
};

/**
 * 팩터 목록 조회 훅
 * - 모든 팩터 목록을 조회합니다
 * - SSR에서 prefetch된 데이터를 자동으로 사용합니다
 *
 * @returns 팩터 목록 쿼리 결과
 */
export function useFactorsQuery() {
  return useQuery<Factor[], Error>({
    queryKey: factorsQueryKey.list(),
    queryFn: () => getFactors(false),
  });
}

/**
 * 카테고리별 팩터 조회 훅
 * - 특정 카테고리의 팩터를 조회합니다
 *
 * @param category - 팩터 카테고리
 * @returns 팩터 목록 쿼리 결과
 */
export function useFactorsByCategoryQuery(category: string) {
  return useQuery<Factor[], Error>({
    queryKey: factorsQueryKey.byCategory(category),
    queryFn: () => getFactorsByCategory(category, false),
    enabled: !!category,
  });
}

/**
 * 팩터 상세 조회 훅
 * - 특정 팩터의 상세 정보를 조회합니다
 *
 * @param factorId - 팩터 ID
 * @returns 팩터 상세 쿼리 결과
 */
export function useFactorQuery(factorId: string) {
  return useQuery<Factor, Error>({
    queryKey: factorsQueryKey.detail(factorId),
    queryFn: () => getFactorById(factorId, false),
    enabled: !!factorId,
  });
}
