"use client";

import Image from "next/image";
import Link from "next/link";

/**
 * 새로 만들기 카드
 *
 * @description 새로운 포트폴리오를 생성하기 위한 카드 컴포넌트
 * 클릭하면 전략 생성 페이지로 이동합니다.
 */

export function CreatePortfolioCard() {
  return (
    <Link
      href="/quant/new" // TODO: 전략 생성 페이지 경로로 변경
      className="bg-surface border border-surface rounded-lg p-5 h-[12.5rem] flex flex-col items-center justify-center gap-4 transition-all duration-200 hover:border-brand-soft hover:shadow-elev-card"
    >
      {/* 플러스 아이콘 */}
      <div className="relative w-[80px] h-[80px]">
        <Image
          src="/icons/circle-plus.svg"
          alt=""
          fill
          className="object-contain"
          aria-hidden="true"
        />
      </div>

      {/* 텍스트 */}
      <span className="text-[1.5rem] font-bold text-[#c8c8c8]">새로 만들기</span>
    </Link>
  );
}
