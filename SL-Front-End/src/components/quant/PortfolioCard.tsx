"use client";

import Image from "next/image";

/**
 * 포트폴리오 카드
 *
 * @description 개별 포트폴리오 정보를 표시하는 카드 컴포넌트
 * 활성화 상태에 따라 다른 스타일과 태그를 표시합니다.
 */

interface PortfolioCardProps {
  /** 포트폴리오 ID */
  id: string;
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
}

export function PortfolioCard({
  id,
  title,
  profitRate,
  isActive,
  lastModified,
  createdAt,
  isSelected,
  onSelect,
  onClick,
}: PortfolioCardProps) {
  // 수익률 포맷팅
  const formatProfitRate = (rate: number) => {
    const sign = rate >= 0 ? "+" : "";
    return `${sign}${rate.toFixed(2)}%`;
  };

  // 수익률이 양수인지 판단
  const isPositive = profitRate >= 0;

  return (
    <div
      className="bg-surface border border-surface rounded-lg h-[12.5rem] flex flex-col cursor-pointer transition-all duration-200 hover:border-brand-soft hover:shadow-elev-sm p-5"
      onClick={() => onClick(id)}
    >
      {/* 헤더: 제목과 체크박스 */}
      <div className="flex items-start justify-between">
        <h3 className="text-[1.25rem] font-semibold text-black">{title}</h3>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
            onSelect(id);
          }}
          className="w-5 h-5 shrink-0"
          aria-label={isSelected ? "선택 해제" : "선택"}
        >
          <div className="relative w-full h-full">
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

      {/* 수익률 */}
      <p
        className={[
          "text-[1.25rem] font-semibold mb-3",
          isPositive ? "text-red-500" : "text-blue-500",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {formatProfitRate(profitRate)}
      </p>

      {/* 상태 태그 */}
      <div className="mb-auto">
        {isActive ? (
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
      <div className="flex items-center justify-between text-sm text-muted">
        <span>최종 수정일 : {lastModified}</span>
        <span>생성일자 : {createdAt}</span>
      </div>
    </div>
  );
}
