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
import { FloatingChatWidget } from "@/components/home/FloatingChatWidget";

export function Providers({ children }: { children: ReactNode }) {
  // 브라우저 환경에서 싱글톤 QueryClient 사용
  const queryClient = getQueryClient();

  // 세션 만료 상태 구독
  const isSessionExpired = useAuthStore((state) => state.isSessionExpired);
  const setSessionExpired = useAuthStore((state) => state.setSessionExpired);
  const authErrorMessage = useAuthStore((state) => state.authErrorMessage);
  const setAuthErrorMessage = useAuthStore(
    (state) => state.setAuthErrorMessage,
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* 세션 만료 모달 */}
      <SessionExpiredModal
        isOpen={isSessionExpired || !!authErrorMessage}
        message={authErrorMessage}
        onClose={() => {
          setSessionExpired(false);
          setAuthErrorMessage(null);
        }}
      />
      {/* 전역 플로팅 챗봇 (시세/뉴스/커뮤니티/퀀트 탭에서도 노출) */}
      <FloatingChatWidget />
    </QueryClientProvider>
  );
}
