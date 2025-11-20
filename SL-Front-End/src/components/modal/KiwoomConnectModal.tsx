"use client";

import { useCallback, useEffect, useState } from "react";
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

  const handleClose = useCallback(() => {
    setAppKey("");
    setAppSecret("");
    setError(null);
    setSuccess(false);
    onClose();
  }, [onClose]);

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
  }, [isOpen, handleClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const _response = await kiwoomApi.registerCredentials({
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-overlay"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="kiwoom-connect-modal-title"
    >
      <div
        className="w-full max-w-md rounded-xl bg-base-0 p-6 shadow-elev-strong"
        onClick={(event) => event.stopPropagation()}
      >
        <h2
          id="kiwoom-connect-modal-title"
          className="mb-4 text-xl font-bold text-text-body"
        >
          키움증권 연동
        </h2>

        {success ? (
          <div className="py-10 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-brand-soft text-brand text-2xl">
              ✓
            </div>
            <p className="text-lg font-medium text-text-body">
              키움증권 연동이 완료되었습니다!
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="app-key"
                className="mb-2 block text-sm text-text-muted"
              >
                앱 키 (APP KEY)
              </label>
              <input
                id="app-key"
                type="text"
                value={appKey}
                onChange={(e) => setAppKey(e.target.value)}
                placeholder="키움증권 앱 키를 입력하세요"
                className="w-full rounded-lg border border-surface bg-surface px-4 py-3 text-text-body transition-all focus:border-brand-soft focus:shadow-elev-brand"
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label
                htmlFor="app-secret"
                className="mb-2 block text-sm text-text-muted"
              >
                시크릿 키 (SECRET KEY)
              </label>
              <input
                id="app-secret"
                type="password"
                value={appSecret}
                onChange={(e) => setAppSecret(e.target.value)}
                placeholder="키움증권 시크릿 키를 입력하세요"
                className="w-full rounded-lg border border-surface bg-surface px-4 py-3 text-text-body transition-all focus:border-brand-soft focus:shadow-elev-brand"
                required
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="px-1">
                <p className="text-[0.75rem] text-price-up">{error}</p>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={handleClose}
                className="flex-1 px-4 py-3 bg-[#1822340D] text-body rounded-[12px] hover:bg-[#C8C8C8] transition-colors"
                disabled={isLoading}
              >
                취소
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-3 bg-brand-purple text-white rounded-[12px] hover:bg-brand-purple/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading || !appKey.trim() || !appSecret.trim()}
              >
                {isLoading ? "연동 중..." : "등록"}
              </button>
            </div>
          </form>
        )}

        <div className="mt-3 rounded-[12px] text-[0.75rem] text-muted">
          참고: 현재 모의투자 API는 https://mockapi.kiwoom.com를 사용합니다.
        </div>
      </div>
    </div>,
    document.body,
  );
}
