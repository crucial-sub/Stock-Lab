"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { authApi } from "@/lib/api/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * 로그인 상태를 확인하여 인증이 필요한 페이지를 보호하는 컴포넌트
 * - 로그인 상태: 페이지 렌더링
 * - 비로그인 상태: /login 페이지로 리다이렉트
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;

    const checkAuth = async () => {
      try {
        await authApi.getCurrentUser();
        if (!mounted) {
          return;
        }
        setIsAuthenticated(true);
      } catch {
        if (!mounted) {
          return;
        }
        setIsAuthenticated(false);
        router.push("/login");
      } finally {
        if (mounted) {
          setIsChecking(false);
        }
      }
    };

    checkAuth();

    return () => {
      mounted = false;
    };
  }, [router]);

  // 인증 확인 중에는 아무것도 렌더링하지 않음 (깜빡임 방지)
  if (isChecking) {
    return null;
  }

  // 인증된 경우에만 children 렌더링
  return isAuthenticated ? children : null;
}
