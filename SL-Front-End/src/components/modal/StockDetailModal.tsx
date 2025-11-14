"use client";

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { StockInfoCard } from "@/components/market-price/StockInfoCard";

interface StockDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  stockName: string;
  stockCode: string;
}

/**
 * 주식 상세 정보 모달
 * - Portal을 사용하여 document.body에 렌더링
 * - ESC 키로 닫기
 * - 배경 클릭 시 닫기
 * - 스크롤 가능한 세부 정보 표시
 * - 모달 열림 시 배경 스크롤 차단
 */
export function StockDetailModal({
  isOpen,
  onClose,
  stockName,
  stockCode,
}: StockDetailModalProps) {
  // 모달 열릴 때 배경 스크롤 차단
  useEffect(() => {
    if (!isOpen) return;

    // 현재 스크롤 위치 저장
    const scrollY = window.scrollY;

    // body 스크롤 차단
    document.body.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = "100%";

    // 클린업: 모달 닫힐 때 스크롤 복원
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
        onClose();
      }
    };

    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [isOpen, onClose]);

  // 모달이 열려있지 않으면 렌더링하지 않음
  if (!isOpen) return null;

  // SSR 환경 체크
  if (typeof window === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center"
      style={{ zIndex: 99999 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="stock-detail-modal-title"
    >
      <div
        className="relative rounded-[8px] max-h-[70vh] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        style={{ zIndex: 100000 }}
        onClick={(event) => event.stopPropagation()}
      >
        {/* 모달 헤더 */}
        <div className="relative flex items-center shadow-header bg-white px-[0.5rem] py-[0.8rem]">
          <h2
            id="stock-detail-modal-title"
            className="absolute left-1/2 -translate-x-1/2 text-[0.9rem] font-normal text-text-strong"
          >
            {stockName} 종목 정보
          </h2>
          <button
            type="button"
            className="mr-[0.25rem] ml-auto flex h-3 w-3 rounded-full bg-[#FF6464]"
            aria-label="닫기"
            onClick={onClose}
          />
        </div>

        {/* 모달 컨텐츠 */}
        <StockInfoCard name={stockName} code={stockCode} />
      </div>
    </div>,
    document.body
  );
}
