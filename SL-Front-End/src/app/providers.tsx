"use client";

/**
 * 앱 전역 Provider 컴포넌트
 * - React Query Provider를 설정합니다
 * - SSR 환경에서 hydration을 지원합니다
 * - 세션 만료 모달을 전역으로 관리합니다
 */

import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { getQueryClient } from "@/lib/query-client";
import { SessionExpiredModal } from "@/components/modal/SessionExpiredModal";
import { useAuthStore } from "@/stores/authStore";

export function Providers({ children }: { children: ReactNode }) {
  // 브라우저 환경에서 싱글톤 QueryClient 사용
  const queryClient = getQueryClient();

  // 세션 만료 상태 구독
  const isSessionExpired = useAuthStore((state) => state.isSessionExpired);
  const setSessionExpired = useAuthStore((state) => state.setSessionExpired);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* 세션 만료 모달 */}
      <SessionExpiredModal
        isOpen={isSessionExpired}
        onClose={() => setSessionExpired(false)}
      />
    </QueryClientProvider>
  );
}
