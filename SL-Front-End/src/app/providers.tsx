"use client";

/**
 * 앱 전역 Provider 컴포넌트
 * - React Query Provider를 설정합니다
 * - SSR 환경에서 hydration을 지원합니다
 */

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { getQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: ReactNode }) {
  // 브라우저 환경에서 싱글톤 QueryClient 사용
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
