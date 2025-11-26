"use client";

import { useCallback, useEffect } from "react";
import { createPortal } from "react-dom";

/**
 * 아이콘 타입별 설정
 */
type IconType = "info" | "warning" | "error" | "success" | "question";

interface ConfirmModalProps {
  /** 모달 열림 상태 */
  isOpen: boolean;
  /** 모달 닫기 콜백 */
  onClose: () => void;
  /** 확인 버튼 클릭 콜백 */
  onConfirm: () => void;
  /** 모달 제목 */
  title: string;
  /** 모달 메시지 (줄바꿈은 \n으로 구분) */
  message: string;
  /** 확인 버튼 텍스트 */
  confirmText?: string;
  /** 취소 버튼 텍스트 */
  cancelText?: string;
  /** 아이콘 타입 */
  iconType?: IconType;
  /** 확인 버튼만 표시 (alert 모드) */
  alertOnly?: boolean;
}

/**
 * 아이콘 타입별 스타일 및 아이콘
 */
const ICON_CONFIG: Record<IconType, { bgColor: string; textColor: string; icon: string }> = {
  info: {
    bgColor: "bg-blue-100",
    textColor: "text-blue-600",
    icon: "ℹ",
  },
  warning: {
    bgColor: "bg-yellow-100",
    textColor: "text-yellow-600",
    icon: "⚠",
  },
  error: {
    bgColor: "bg-red-100",
    textColor: "text-red-600",
    icon: "✕",
  },
  success: {
    bgColor: "bg-green-100",
    textColor: "text-green-600",
    icon: "✓",
  },
  question: {
    bgColor: "bg-brand-soft",
    textColor: "text-brand-purple",
    icon: "?",
  },
};

/**
 * 커스텀 확인 모달
 * - 프로젝트 테마에 맞는 디자인
 * - confirm/alert 모드 지원
 * - ESC 키로 닫기
 * - 배경 클릭으로 닫기
 */
export function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "확인",
  cancelText = "취소",
  iconType = "question",
  alertOnly = false,
}: ConfirmModalProps) {
  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  const handleConfirm = useCallback(() => {
    onConfirm();
    onClose();
  }, [onConfirm, onClose]);

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

  if (!isOpen) return null;
  if (typeof window === "undefined") return null;

  const iconConfig = ICON_CONFIG[iconType];

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-overlay animate-in fade-in duration-200"
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
    >
      <div
        className="w-full max-w-sm mx-4 rounded-xl bg-base-0 p-6 shadow-elev-strong animate-in zoom-in-95 duration-200"
        onClick={(event) => event.stopPropagation()}
      >
        {/* 아이콘 */}
        <div className="flex justify-center mb-4">
          <div
            className={`flex h-14 w-14 items-center justify-center rounded-full ${iconConfig.bgColor} ${iconConfig.textColor} text-2xl font-bold`}
          >
            {iconConfig.icon}
          </div>
        </div>

        {/* 제목 */}
        <h2
          id="confirm-modal-title"
          className="mb-3 text-center text-lg font-bold text-text-body"
        >
          {title}
        </h2>

        {/* 메시지 */}
        <p className="mb-6 text-center text-sm text-text-muted whitespace-pre-line leading-relaxed">
          {message}
        </p>

        {/* 버튼 */}
        <div className="flex gap-3">
          {!alertOnly && (
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-3 bg-[#1822340D] text-text-body rounded-xl font-semibold hover:bg-[#C8C8C8] transition-colors"
            >
              {cancelText}
            </button>
          )}
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 px-4 py-3 bg-brand-purple text-white rounded-xl font-semibold hover:bg-brand-purple/80 transition-colors"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
