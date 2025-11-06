/**
 * 테마 관련 React Query 훅
 * - 테마 목록 조회 쿼리를 제공합니다
 */

import { getThemes, getThemesById } from "@/lib/api";
import type { Themes } from "@/types/api";
import { useQuery } from "@tanstack/react-query";

/**
 * 테마 목록 조회 쿼리 키
 * 테마 관련 쿼리의 캐싱과 무효화를 관리하기 위한 키 팩토리
 */
export const themesQueryKey = {
  all: ["themes"] as const,
  lists: () => [...themesQueryKey.all, "list"] as const,
  list: () => [...themesQueryKey.lists()] as const,
  detail: (id: string) => [...themesQueryKey.all, "detail", id] as const,
};

/**
 * 테마 목록 조회 훅
 * - 모든 테마 목록을 조회합니다
 * - SSR에서 prefetch된 데이터를 자동으로 사용합니다
 *
 * @returns 테마 목록 쿼리 결과
 */
export function useThemesQuery() {
  return useQuery<Themes[], Error>({
    queryKey: themesQueryKey.list(),
    queryFn: () => getThemes(false),
  });
}

/**
 * 테마 상세 조회 훅
 * - 특정 함수의 상세 정보를 조회합니다
 *
 * @param themeId - 테마 ID
 * @returns 테마 상세 쿼리 결과
 */
export function useThemeQuery(themeId: string) {
  return useQuery<Themes, Error>({
    queryKey: themesQueryKey.detail(themeId),
    queryFn: () => getThemesById(themeId, false),
    enabled: !!themeId,
  });
}
