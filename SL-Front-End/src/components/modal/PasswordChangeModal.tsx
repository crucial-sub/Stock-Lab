"use client";

import { useState } from "react";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
import { authApi } from "@/lib/api/auth";

interface PasswordChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PasswordChangeModal({
  isOpen,
  onClose,
}: PasswordChangeModalProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    // 유효성 검사
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("모든 필드를 입력해주세요");
      return;
    }

    if (newPassword.length < 8) {
      setError("새 비밀번호는 최소 8자 이상이어야 합니다");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("새 비밀번호가 일치하지 않습니다");
      return;
    }

    if (currentPassword === newPassword) {
      setError("새 비밀번호는 현재 비밀번호와 달라야 합니다");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await authApi.updatePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      setShowSuccessModal(true);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "비밀번호 변경에 실패했습니다";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setError(null);
    onClose();
  };

  // 성공 모달 확인 후 닫기
  const handleSuccessConfirm = () => {
    setShowSuccessModal(false);
    handleClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-overlay">
      <div className="bg-base-0 rounded-xl shadow-elev-strong w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-text-body mb-4">비밀번호 변경</h2>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            현재 비밀번호
          </label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => {
              setCurrentPassword(e.target.value);
              setError(null);
            }}
            placeholder="현재 비밀번호를 입력하세요"
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            새 비밀번호
          </label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              setError(null);
            }}
            placeholder="새 비밀번호를 입력하세요 (최소 8자)"
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            새 비밀번호 확인
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setError(null);
            }}
            placeholder="새 비밀번호를 다시 입력하세요"
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
          />
        </div>

        {error && (
          <div className="px-1 mb-5">
            <p className="text-[0.75rem] text-price-up">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleClose}
            className="flex-1 px-4 py-3 bg-[#1822340D] text-body rounded-[12px] hover:bg-[#C8C8C8] transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-brand-purple text-white rounded-[12px] hover:bg-brand-purple/80 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "변경 중..." : "변경하기"}
          </button>
        </div>
      </div>

      {/* 성공 모달 */}
      <ConfirmModal
        isOpen={showSuccessModal}
        onClose={handleSuccessConfirm}
        onConfirm={handleSuccessConfirm}
        title="비밀번호 변경 완료"
        message="비밀번호가 성공적으로 변경되었습니다."
        confirmText="확인"
        iconType="success"
        alertOnly
      />
    </div>
  );
}
