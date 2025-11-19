"use client";

import { useState } from "react";
import { authApi } from "@/lib/api/auth";
import { useRouter } from "next/navigation";

interface DeleteAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  userEmail: string;
  userPhone: string;
}

export function DeleteAccountModal({
  isOpen,
  onClose,
  userEmail,
  userPhone,
}: DeleteAccountModalProps) {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmText, setConfirmText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (confirmText !== "회원탈퇴") {
      setError("'회원탈퇴'를 정확히 입력해주세요");
      return;
    }

    if (!password) {
      setError("비밀번호를 입력해주세요");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await authApi.deleteAccount({
        email: userEmail,
        password,
        phone_number: userPhone,
      });

      alert("회원탈퇴가 완료되었습니다");

      // 로그아웃 처리
      await authApi.logout();

      // 로그인 페이지로 이동
      router.push("/login");
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "회원탈퇴에 실패했습니다";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setPassword("");
    setConfirmText("");
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-overlay">
      <div className="bg-base-0 rounded-xl shadow-elev-strong w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-price-down mb-4">
          회원탈퇴
        </h2>

        <div className="mb-4 p-4 bg-surface rounded-lg border border-price-down">
          <p className="text-sm text-text-body mb-2">
            정말로 탈퇴하시겠습니까?
          </p>
          <p className="text-xs text-text-muted">
            탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다.
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            비밀번호 확인
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
            placeholder="비밀번호를 입력하세요"
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            확인 문구 입력
          </label>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => {
              setConfirmText(e.target.value);
              setError(null);
            }}
            placeholder="'회원탈퇴'를 입력하세요"
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
          />
        </div>

        {error && (
          <div className="mb-4 p-3 bg-price-up rounded-lg">
            <p className="text-sm text-price-down">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleClose}
            className="flex-1 px-4 py-3 bg-surface text-text-body rounded-lg hover:bg-sidebar-item-sub-active transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading || confirmText !== "회원탈퇴"}
            className="flex-1 px-4 py-3 bg-price-down text-base-0 rounded-lg hover:opacity-80 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "처리 중..." : "탈퇴하기"}
          </button>
        </div>
      </div>
    </div>
  );
}
