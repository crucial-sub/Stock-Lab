/**
 * Quant 페이지 - 서버 컴포넌트
 * - 팩터 목록과 함수 목록을 서버에서 미리 불러옵니다 (SSR)
 * - React Query의 prefetch와 dehydrate를 사용하여 초기 데이터를 전달합니다
 */

import { factorsQueryKey } from "@/hooks/useFactorsQuery";
import { subFactorsQueryKey } from "@/hooks/useSubFactorsQuery";
import { getFactors, getSubFactors } from "@/lib/api";
import { getQueryClient } from "@/lib/query-client";
import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { QuantNewPageClient } from "./QuantNewPageClient";

/**
 * Quant 새 전략 페이지 (서버 컴포넌트)
 * - 팩터와 함수 목록을 서버에서 prefetch합니다
 * - 클라이언트 컴포넌트에 hydrated 상태로 데이터를 전달합니다
 */
export default async function NewScriptPage() {
  // 서버용 QueryClient 생성
  const queryClient = getQueryClient();

  // 팩터 목록 prefetch
  await queryClient.prefetchQuery({
    queryKey: factorsQueryKey.list(),
    queryFn: () => getFactors(true), // 서버 사이드 요청
  });

  // 함수 목록 prefetch
  await queryClient.prefetchQuery({
    queryKey: subFactorsQueryKey.list(),
    queryFn: () => getSubFactors(true), // 서버 사이드 요청
  });

  // QueryClient 상태를 dehydrate하여 클라이언트로 전달
  const dehydratedState = dehydrate(queryClient);

  return (
    <HydrationBoundary state={dehydratedState}>
      <QuantNewPageClient />
    </HydrationBoundary>
  );
}
