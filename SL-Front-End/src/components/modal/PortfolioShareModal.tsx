"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ToggleSwitch } from "@/components/common/ToggleSwitch";

interface PortfolioShareModalProps {
  isOpen: boolean;
  portfolioName?: string;
  initialDescription?: string;
  initialIsAnonymous?: boolean;
  onClose: () => void;
  onConfirm: (params: {
    description: string;
    isAnonymous: boolean;
  }) => Promise<void>;
}

/**
 * 포트폴리오 공유 설정 모달
 * - 설명 입력 및 익명 여부 토글
 */
export function PortfolioShareModal({
  isOpen,
  portfolioName,
  initialDescription = "",
  initialIsAnonymous = false,
  onClose,
  onConfirm,
}: PortfolioShareModalProps) {
  const [description, setDescription] = useState(initialDescription);
  const [isAnonymous, setIsAnonymous] = useState(initialIsAnonymous);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = useCallback(() => {
    setDescription(initialDescription);
    setIsAnonymous(initialIsAnonymous);
    setError(null);
    onClose();
  }, [initialDescription, initialIsAnonymous, onClose]);

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

  // 초기값 동기화
  useEffect(() => {
    if (isOpen) {
      setDescription(initialDescription);
      setIsAnonymous(initialIsAnonymous);
      setError(null);
    }
  }, [initialDescription, initialIsAnonymous, isOpen]);

  const handleSubmit = async () => {
    if (!description.trim()) {
      setError("전략 설명을 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onConfirm({
        description: description.trim(),
        isAnonymous,
      });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } }; message?: string })
          ?.response?.data?.detail ||
        (err as { message?: string })?.message ||
        "공유 설정에 실패했습니다. 잠시 후 다시 시도해주세요.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || typeof window === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="portfolio-share-modal-title"
    >
      <div
        className="w-full max-w-lg rounded-[16px] bg-white p-6 shadow-elev-strong"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted">포트폴리오 공유</p>
            <h2
              id="portfolio-share-modal-title"
              className="mt-1 text-xl font-semibold text-black"
            >
              {portfolioName || "내 포트폴리오"}
            </h2>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="h-9 w-9 rounded-full text-lg text-[#646464] transition hover:bg-[#f2f2f2]"
            aria-label="닫기"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label
              htmlFor="portfolio-description"
              className="mb-2 block text-sm font-medium text-[#000000]"
            >
              전략 설명
            </label>
            <textarea
              id="portfolio-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="다른 사용자에게 보여줄 전략 설명을 입력하세요."
              className="w-full min-h-[120px] rounded-[12px] border border-[#dbe3f5] bg-[#f9fbff] px-4 py-3 text-sm text-black placeholder:text-[#97a3c1] focus:border-brand-soft focus:bg-white focus:outline-none"
            />
            <p className="mt-1 text-xs text-muted">
              입력한 내용은 portfolio_strategy 테이블의 description 컬럼에 저장됩니다.
            </p>
          </div>

          <div className="flex items-center justify-between rounded-[12px] border border-[#e5e5e5] bg-[#f8f8f8] px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-black">익명으로 공유</p>
              <p className="text-xs text-muted">
                활성화하면 작성자 이름 대신 익명으로 표시됩니다.
              </p>
            </div>
            <ToggleSwitch checked={isAnonymous} onChange={setIsAnonymous} />
          </div>

          {error ? (
            <p className="text-sm text-price-up">{error}</p>
          ) : null}
        </div>

        <div className="mt-6 flex items-center gap-3">
          <button
            type="button"
            onClick={handleClose}
            className="flex-1 rounded-[12px] border border-[#dbe3f5] bg-white px-4 py-3 text-sm font-semibold text-[#646464] transition hover:bg-[#f3f5ff]"
            disabled={isSubmitting}
          >
            취소
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1 rounded-[12px] bg-brand-purple px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-purple/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "저장 중..." : "공유하기"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
