/**
 * 백테스트 결과 페이지 - 서버 컴포넌트
 * - 백테스트 결과를 서버에서 미리 불러옵니다 (SSR)
 * - React Query의 prefetch와 dehydrate를 사용하여 초기 데이터를 전달합니다
 */

import {
  dehydrate,
  HydrationBoundary,
} from "@tanstack/react-query";
import { getQueryClient } from "@/lib/query-client";
import { getBacktestResult } from "@/lib/api";
import { backtestQueryKey } from "@/hooks/useBacktestQuery";
import { QuantResultPageClientNew } from "./QuantResultPageClientNew";

/**
 * 백테스트 결과 페이지 Props
 */
interface QuantResultPageProps {
  searchParams: Promise<{
    id?: string;
  }>;
}

/**
 * 백테스트 결과 페이지 (서버 컴포넌트)
 * - URL 쿼리 파라미터에서 백테스트 ID를 받아옵니다
 * - 백테스트 결과를 서버에서 prefetch합니다
 * - 클라이언트 컴포넌트에 hydrated 상태로 데이터를 전달합니다
 */
export default async function QuantResultPage({
  searchParams,
}: QuantResultPageProps) {
  // searchParams를 await하여 해결
  const resolvedSearchParams = await searchParams;
  const backtestId = resolvedSearchParams.id;

  // 백테스트 ID가 없으면 에러 페이지 표시
  if (!backtestId) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 ID가 없습니다
          </h1>
          <p className="text-text-secondary">
            올바른 백테스트 결과 URL을 사용해주세요.
          </p>
        </div>
      </div>
    );
  }

  // 서버용 QueryClient 생성
  const queryClient = getQueryClient();

  try {
    // 백테스트 결과 prefetch
    await queryClient.prefetchQuery({
      queryKey: backtestQueryKey.detail(backtestId),
      queryFn: () => getBacktestResult(backtestId, true), // 서버 사이드 요청
    });

    // QueryClient 상태를 dehydrate하여 클라이언트로 전달
    const dehydratedState = dehydrate(queryClient);

    return (
      <HydrationBoundary state={dehydratedState}>
        <QuantResultPageClientNew backtestId={backtestId} />
      </HydrationBoundary>
    );
  } catch (error) {
    // 백테스트 결과 조회 실패 시 에러 페이지 표시
    console.error("백테스트 결과 조회 실패:", error);

    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 결과를 불러올 수 없습니다
          </h1>
          <p className="text-text-secondary">
            백테스트가 존재하지 않거나 오류가 발생했습니다.
          </p>
        </div>
      </div>
    );
  }
}
