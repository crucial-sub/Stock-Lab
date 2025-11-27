"use client";

import Image from "next/image";
import { memo, type MouseEvent } from "react";

/**
 * 포트폴리오 카드
 *
 * @description 개별 포트폴리오 정보를 표시하는 카드 컴포넌트
 * 활성화 상태에 따라 다른 스타일과 태그를 표시합니다.
 */

interface PortfolioCardProps {
  /** 포트폴리오 ID */
  id: string;
  /** 포트폴리오 전략 ID */
  strategyId: string;
  /** 포트폴리오 제목 */
  title: string;
  /** 수익률 (%) */
  profitRate: number;
  /** 활성화 상태 (가상 매매 중) */
  isActive: boolean;
  /** 최종 수정일 (YYYY.MM.DD) */
  lastModified: string;
  /** 생성일 (YYYY.MM.DD) */
  createdAt: string;
  /** 선택 상태 */
  isSelected: boolean;
  /** 선택 핸들러 */
  onSelect: (id: string) => void;
  /** 클릭 핸들러 */
  onClick: (id: string) => void;
  /** 공유 액션 핸들러 */
  onShare: (portfolio: { id: string; strategyId: string; title: string }) => void;
  /** 전략 이름 수정 핸들러 */
  onRename: (portfolio: { id: string; strategyId: string; title: string }) => void;
  /** 이름 수정 활성 상태 */
  isEditing?: boolean;
  /** 수정 중인 값 */
  editValue?: string;
  /** 이름 수정 값 변경 콜백 */
  onEditChange?: (value: string) => void;
  /** 이름 수정 저장 */
  onEditSubmit?: () => void;
  /** 이름 수정 취소 */
  onEditCancel?: () => void;
  /** 이름 수정 로딩 상태 */
  isRenaming?: boolean;
}

const PortfolioCardComponent = ({
  id,
  strategyId,
  title,
  profitRate,
  isActive,
  lastModified,
  createdAt,
  isSelected,
  onSelect,
  onClick,
  onShare,
  onRename,
  isEditing = false,
  editValue = "",
  onEditChange,
  onEditSubmit,
  onEditCancel,
  isRenaming = false,
}: PortfolioCardProps) => {
  // 수익률 포맷팅
  const formatProfitRate = (rate: number) => {
    const sign = rate >= 0 ? "+" : "";
    return `${sign}${rate.toFixed(2)}%`;
  };

  // 수익률이 양수인지 판단
  const isPositive = profitRate >= 0;

  // 키움증권 연동 카드인지 판단
  const isAutoTrading = id.startsWith("auto-");

  const handleRename = (event: MouseEvent) => {
    event.stopPropagation();
    onRename({ id, strategyId, title });
  };

  return (
    <div
      className={`bg-surface border border-surface rounded-lg h-[12.5rem] flex flex-col cursor-pointer transition-all duration-200 hover:border-brand-soft hover:shadow-elev-sm p-5 ${!isActive && isAutoTrading ? "opacity-60" : ""
        }`}
      onClick={() => onClick(id)}
    >
      {/* 헤더: 제목과 아이콘들 */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          {isEditing ? (
            <input
              value={editValue}
              onChange={(e) => onEditChange?.(e.target.value)}
              onClick={(e) => e.stopPropagation()}
              onBlur={(e) => {
                e.stopPropagation();
                onEditCancel?.();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") onEditSubmit?.();
                if (e.key === "Escape") onEditCancel?.();
              }}
              className="w-full rounded-md border border-[#dbe3f5] px-2 py-1 text-[1rem] text-black focus:outline-none focus:border-brand-soft"
              autoFocus
            />
          ) : (
            <h3 className="text-[1.25rem] font-semibold text-black">{title}</h3>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* 전략 이름 수정 버튼 */}
          <button
            type="button"
            onClick={handleRename}
            className="relative shrink-0 w-8 h-8 flex items-center justify-center rounded hover:bg-[#e5e9ff] transition focus:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white"
            aria-label="전략 이름 수정"
          >
            <div className="relative w-5 h-5 pointer-events-none">
              <Image
                src="/icons/edit_square.svg"
                alt=""
                fill
                className="object-contain"
                aria-hidden="true"
              />
            </div>
          </button>
          {/* 선택 체크박스 */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
              onSelect(id);
            }}
            className="relative shrink-0 w-8 h-8 flex items-center justify-center rounded focus:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white"
            aria-label={isSelected ? "선택 해제" : "선택"}
          >
            <div className="relative w-5 h-5 pointer-events-none">
              <Image
                src={
                  isSelected
                    ? "/icons/check-box_brand.svg"
                    : "/icons/check-box_blank.svg"
                }
                alt=""
                fill
                className="object-contain"
                aria-hidden="true"
              />
            </div>
          </button>
        </div>
      </div>

      {/* 수익률 */}
      <div className="mb-3">
        <p
          className={[
            "text-[1.25rem] font-semibold",
            isPositive ? "text-red-500" : "text-blue-500",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {formatProfitRate(profitRate)}
        </p>
      </div>

      {/* 상태 태그 */}
      <div className="mb-auto">
        {isAutoTrading ? (
          isActive ? (
            <span className="inline-block bg-green-500 font-semibold px-4 py-1 rounded-full text-white">
              키움증권 연동 가상매매 중
            </span>
          ) : (
            <span className="inline-block bg-gray-400 font-semibold px-4 py-1 rounded-full text-white">
              키움증권 연동 가상매매 종료
            </span>
          )
        ) : isActive ? (
          <span className="inline-block bg-tag-portfolio-active font-semibold px-4 py-1 rounded-full text-white">
            가상 매매
          </span>
        ) : (
          <span className="inline-block bg-[#c8c8c8] font-semibold px-4 py-1 rounded-full text-white">
            백테스팅
          </span>
        )}
      </div>

      {/* 푸터: 날짜 정보 */}
      <div className="flex items-center justify-between text-xs sm:text-sm text-muted gap-2 flex-wrap">
        <span className="whitespace-nowrap truncate">수정: {lastModified}</span>
        <span className="whitespace-nowrap truncate">생성: {createdAt}</span>
      </div>
    </div>
  );
};

/**
 * PortfolioCard with React.memo for performance optimization
 * - Prevents unnecessary re-renders when parent re-renders but props haven't changed
 * - Especially important in lists where multiple cards are rendered
 */
export const PortfolioCard = memo(PortfolioCardComponent);
