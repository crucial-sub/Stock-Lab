/**
 * 백테스트 결과 페이지 - 동적 라우트
 * - URL: /quant/result/[id]
 * - 백테스트 ID를 URL 파라미터로 받아옵니다
 */

import { backtestQueryKey } from "@/hooks/useBacktestQuery";
import { getBacktestResult } from "@/lib/api";
import { getQueryClient } from "@/lib/query-client";
import {
  dehydrate,
  HydrationBoundary,
} from "@tanstack/react-query";
import { QuantResultPageClient } from "../QuantResultPageClient";

/**
 * 백테스트 결과 페이지 Props
 */
interface QuantResultPageProps {
  params: Promise<{
    id: string;
  }>;
}

/**
 * 백테스트 결과 페이지 (서버 컴포넌트)
 * - URL 파라미터에서 백테스트 ID를 받아옵니다
 * - 백테스트 결과를 서버에서 prefetch합니다
 * - 클라이언트 컴포넌트에 hydrated 상태로 데이터를 전달합니다
 */
export default async function QuantResultPage({
  params,
}: QuantResultPageProps) {
  // params를 await하여 해결
  const resolvedParams = await params;
  const backtestId = resolvedParams.id;

  // Mock 모드 체크
  const isMockMode = backtestId.startsWith("mock");

  // Mock 모드면 prefetch 스킵
  if (isMockMode) {
    return <QuantResultPageClient backtestId={backtestId} />;
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
        <QuantResultPageClient backtestId={backtestId} />
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