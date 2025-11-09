/**
 * Quant 페이지 - 서버 컴포넌트
 * - 팩터 목록, 함수 목록, 테마 목록을 서버에서 미리 불러옵니다 (SSR)
 * - React Query의 prefetch와 dehydrate를 사용하여 초기 데이터를 전달합니다
 * - 통합 API를 사용하여 3번의 요청을 1번으로 최적화 (5초 → 1초 개선)
 */

import { factorsQueryKey } from "@/hooks/useFactorsQuery";
import { subFactorsQueryKey } from "@/hooks/useSubFactorsQuery";
import { themesQueryKey } from "@/hooks/useThemesQuery";
import { getBacktestInitData } from "@/lib/api";
import { getQueryClient } from "@/lib/query-client";
import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { QuantNewPageClient } from "./QuantNewPageClient";

/**
 * Quant 새 전략 페이지 (서버 컴포넌트)
 * - 통합 API로 팩터, 함수, 테마 목록을 한 번에 조회
 * - 클라이언트 컴포넌트에 hydrated 상태로 데이터를 전달합니다
 */
export default async function NewScriptPage() {
  // 서버용 QueryClient 생성
  const queryClient = getQueryClient();

  // 통합 API로 모든 데이터를 한 번에 조회 (성능 최적화)
  const initData = await getBacktestInitData(true);

  // 각 데이터를 React Query 캐시에 저장
  queryClient.setQueryData(factorsQueryKey.list(), initData.factors);
  queryClient.setQueryData(subFactorsQueryKey.list(), initData.sub_factors);
  queryClient.setQueryData(themesQueryKey.list(), initData.themes);

  // QueryClient 상태를 dehydrate하여 클라이언트로 전달
  const dehydratedState = dehydrate(queryClient);

  return (
    <HydrationBoundary state={dehydratedState}>
      <QuantNewPageClient />
    </HydrationBoundary>
  );
}
