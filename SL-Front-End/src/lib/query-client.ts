/**
 * React Query QueryClient 설정
 * - 서버와 클라이언트에서 사용할 QueryClient를 생성합니다
 * - SSR을 위한 설정을 포함합니다
 */

import { QueryClient, defaultShouldDehydrateQuery } from "@tanstack/react-query";

/**
 * QueryClient 기본 옵션을 생성하는 함수
 * - 서버와 클라이언트에서 일관된 설정을 사용합니다
 */
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // 클라이언트에서 즉시 재요청하지 않도록 staleTime 설정
        staleTime: 60 * 1000, // 1분
        // 윈도우 포커스 시 자동 재요청 비활성화
        refetchOnWindowFocus: false,
        // 재연결 시 자동 재요청 활성화
        refetchOnReconnect: true,
        // 마운트 시 자동 재요청 비활성화 (SSR 데이터 활용)
        refetchOnMount: false,
        // 에러 재시도 설정
        retry: 1,
        // 에러 재시도 지연 시간
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      },
      dehydrate: {
        // SSR 시 어떤 쿼리를 dehydrate할지 결정
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) ||
          query.state.status === "pending",
      },
    },
  });
}

/**
 * 서버 사이드 전용 QueryClient
 * - 각 요청마다 새로운 인스턴스를 생성합니다
 */
let browserQueryClient: QueryClient | undefined = undefined;

/**
 * 브라우저 환경에서 사용할 QueryClient를 반환합니다
 * - 싱글톤 패턴으로 관리합니다
 * - 서버에서는 매번 새로운 인스턴스를 생성합니다
 */
export function getQueryClient() {
  if (typeof window === "undefined") {
    // 서버: 항상 새로운 QueryClient 생성
    return makeQueryClient();
  }

  // 브라우저: 기존 QueryClient가 없으면 생성
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }

  return browserQueryClient;
}
