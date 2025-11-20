"use client";

import { useState } from "react";
import { authApi } from "@/lib/api/auth";

interface NicknameChangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentNickname: string;
  onSuccess: () => void;
}

export function NicknameChangeModal({
  isOpen,
  onClose,
  currentNickname,
  onSuccess,
}: NicknameChangeModalProps) {
  const [newNickname, setNewNickname] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);

  if (!isOpen) return null;

  const handleCheckNickname = async () => {
    if (!newNickname || newNickname === currentNickname) {
      setError("새로운 닉네임을 입력해주세요");
      return;
    }

    try {
      const result = await authApi.checkNickname(newNickname);
      setIsAvailable(result.available);
      if (!result.available) {
        setError("이미 사용 중인 닉네임입니다");
      } else {
        setError(null);
      }
    } catch (err) {
      setError("닉네임 확인에 실패했습니다");
    }
  };

  const handleSubmit = async () => {
    if (!newNickname || !isAvailable) {
      setError("닉네임 중복 확인을 먼저 해주세요");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await authApi.updateNickname(newNickname);
      onSuccess();
      onClose();
      setNewNickname("");
      setIsAvailable(null);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "닉네임 변경에 실패했습니다";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setNewNickname("");
    setError(null);
    setIsAvailable(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-overlay">
      <div className="bg-base-0 rounded-xl shadow-elev-strong w-full max-w-md p-6">
        <h2 className="text-xl font-bold text-text-body mb-4">닉네임 변경</h2>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            현재 닉네임
          </label>
          <input
            type="text"
            value={currentNickname}
            disabled
            className="w-full px-4 py-3 bg-surface border border-surface rounded-lg text-text-muted"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm text-text-muted mb-2">
            새 닉네임
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newNickname}
              onChange={(e) => {
                setNewNickname(e.target.value);
                setIsAvailable(null);
                setError(null);
              }}
              placeholder="새로운 닉네임을 입력하세요"
              className="flex-1 px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
            />
            <button
              onClick={handleCheckNickname}
              disabled={!newNickname || newNickname === currentNickname}
              className="px-4 py-3 bg-surface text-text-body rounded-lg hover:bg-button-primary-soft hover:text-brand transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              중복확인
            </button>
          </div>
          {isAvailable === true && (
            <p className="text-sm text-positive mt-2">사용 가능한 닉네임입니다</p>
          )}
          {error && <p className="text-sm text-price-down mt-2">{error}</p>}
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleClose}
            className="flex-1 px-4 py-3 bg-surface text-text-body rounded-lg hover:bg-sidebar-item-sub-active transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            disabled={isLoading || !isAvailable}
            className="flex-1 px-4 py-3 bg-button-primary-soft text-brand rounded-lg hover:bg-brand hover:text-base-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "변경 중..." : "변경하기"}
          </button>
        </div>
      </div>
    </div>
  );
}
