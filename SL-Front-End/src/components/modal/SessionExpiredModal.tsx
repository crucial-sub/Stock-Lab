"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import { clearAuthTokenCookie } from "@/lib/auth/token";

interface SessionExpiredModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * 세션 만료 모달
 * - JWT 토큰 만료 시 표시
 * - 사용자에게 재로그인 안내
 * - 로그인 페이지로 리다이렉트
 */
export function SessionExpiredModal({
  isOpen,
  onClose,
}: SessionExpiredModalProps) {
  const router = useRouter();

  // 모달 열릴 때 배경 스크롤 차단
  useEffect(() => {
    if (!isOpen) return;

    const scrollY = window.scrollY;
    document.body.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = "100%";

    return () => {
      document.body.style.overflow = "";
      document.body.style.position = "";
      document.body.style.top = "";
      document.body.style.width = "";
      window.scrollTo(0, scrollY);
    };
  }, [isOpen]);

  const handleLogin = () => {
    // 토큰 삭제
    clearAuthTokenCookie();

    // 모달 닫기
    onClose();

    // 로그인 페이지로 리다이렉트
    router.push("/login");
  };

  if (!isOpen) return null;

  // Portal을 사용하여 body에 직접 렌더링
  if (typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center">
      {/* 배경 오버레이 */}
      <div className="absolute inset-0 bg-black/50" />

      {/* 모달 컨텐츠 */}
      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        {/* 아이콘 */}
        <div className="mb-4 flex justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-yellow-100">
            <svg
              className="h-8 w-8 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
        </div>

        {/* 제목 */}
        <h2 className="mb-2 text-center text-xl font-bold text-gray-900">
          로그인 세션 만료
        </h2>

        {/* 설명 */}
        <p className="mb-6 text-center text-gray-600">
          로그인 세션이 만료되었습니다.
          <br />
          다시 로그인해 주세요.
        </p>

        {/* 버튼 */}
        <div className="flex justify-center">
          <button
            onClick={handleLogin}
            className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            로그인하러 가기
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
