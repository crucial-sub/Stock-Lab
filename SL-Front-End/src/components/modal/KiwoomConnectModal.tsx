"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { kiwoomApi } from "@/lib/api/kiwoom";

interface KiwoomConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * 키움증권 연동 모달
 * - 앱 키와 시크릿 키 입력
 * - 키움증권 API 인증 토큰 발급
 * - 연동 성공/실패 처리
 */
export function KiwoomConnectModal({
  isOpen,
  onClose,
  onSuccess,
}: KiwoomConnectModalProps) {
  const [appKey, setAppKey] = useState("");
  const [appSecret, setAppSecret] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

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

  // ESC 키로 모달 닫기
  useEffect(() => {
    if (!isOpen) return;

    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        handleClose();
      }
    };

    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [isOpen]);

  const handleClose = () => {
    setAppKey("");
    setAppSecret("");
    setError(null);
    setSuccess(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await kiwoomApi.registerCredentials({
        app_key: appKey.trim(),
        app_secret: appSecret.trim(),
      });

      setSuccess(true);

      // 1.5초 후 자동으로 모달 닫기
      setTimeout(() => {
        handleClose();
        onSuccess?.();
      }, 1500);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        "키움증권 연동에 실패했습니다. 입력하신 정보를 확인해주세요.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;
  if (typeof window === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center"
      style={{ zIndex: 99999 }}
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="kiwoom-connect-modal-title"
    >
      <div
        className="relative bg-white rounded-[8px] w-full max-w-md"
        style={{ zIndex: 100000 }}
        onClick={(event) => event.stopPropagation()}
      >
        {/* 모달 헤더 */}
        <div className="relative flex items-center shadow-header bg-white px-[1rem] py-[1rem] rounded-t-[8px]">
          <h2
            id="kiwoom-connect-modal-title"
            className="absolute left-1/2 -translate-x-1/2 text-[1rem] font-semibold text-text-strong"
          >
            키움증권 연동
          </h2>
          <button
            type="button"
            className="mr-[0.25rem] ml-auto flex h-3 w-3 rounded-full bg-[#FF6464]"
            aria-label="닫기"
            onClick={handleClose}
          />
        </div>

        {/* 모달 컨텐츠 */}
        <div className="p-6">
          {success ? (
            <div className="text-center py-8">
              <div className="mb-4 text-green-500 text-4xl">✓</div>
              <p className="text-lg font-medium text-text-primary">
                키움증권 연동이 완료되었습니다!
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label
                  htmlFor="app-key"
                  className="block text-sm font-medium text-text-primary mb-2"
                >
                  앱 키 (APP KEY)
                </label>
                <input
                  id="app-key"
                  type="text"
                  value={appKey}
                  onChange={(e) => setAppKey(e.target.value.trim())}
                  placeholder="키움증권 앱 키를 입력하세요"
                  className="w-full px-4 py-2 border border-border-primary rounded-md focus:outline-none focus:ring-2 focus:ring-primary-main text-text-primary"
                  required
                  disabled={isLoading}
                />
              </div>

              <div>
                <label
                  htmlFor="app-secret"
                  className="block text-sm font-medium text-text-primary mb-2"
                >
                  시크릿 키 (SECRET KEY)
                </label>
                <input
                  id="app-secret"
                  type="password"
                  value={appSecret}
                  onChange={(e) => setAppSecret(e.target.value.trim())}
                  placeholder="키움증권 시크릿 키를 입력하세요"
                  className="w-full px-4 py-2 border border-border-primary rounded-md focus:outline-none focus:ring-2 focus:ring-primary-main text-text-primary"
                  required
                  disabled={isLoading}
                />
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-border-primary rounded-md text-text-secondary hover:bg-gray-50 transition-colors"
                  disabled={isLoading}
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-main text-white rounded-md hover:bg-primary-dark transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                  disabled={isLoading || !appKey || !appSecret}
                >
                  {isLoading ? "연동 중..." : "등록"}
                </button>
              </div>
            </form>
          )}

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-xs text-blue-800">
              <strong>참고:</strong> 현재 모의투자 API(https://mockapi.kiwoom.com)를 사용합니다.
            </p>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
