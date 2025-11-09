import type { NextPage } from "next";

import { Icon } from "@/components/common/Icon";

export default function NewsPage() {
  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-[1.8rem] font-semibold text-text-strong">테마별 뉴스 요약</h1>
      <div className="flex flex-col gap-4 md:grid md:grid-cols-[2fr_auto_auto]">
        <input
          type="search"
          placeholder="뉴스 검색"
          className="w-full rounded-[8px] px-[1rem] py-[0.75rem] text-text-body font-semibold placeholder:text-tag-neutral shadow-card-muted focus:border focus:border-brand-primary"
        />
            <button
              type="button"
              className="flex items-center justify-center rounded-[8px] bg-brand-primary px-[0.75rem] py-[0.75rem]"
              aria-label="뉴스 검색"
            >
              <Icon src="/icons/search.svg" alt="검색" size={28} color="#FFFFFF" />
              검색
            </button>
        <select
          className="rounded-[8px] border border-border-default bg-white px-4 py-2 text-text-body focus:border-brand-primary focus:outline-none"
        >
          <option value="all">전체</option>
          <option value="stock">종목 뉴스</option>
          <option value="market">시장 동향</option>
        </select>
      </div>
      <p className="text-lg font-medium text-center">
        뉴스 데이터 연동 전입니다. 추후 API 연결 후 실제 기사가 노출될 예정입니다.
      </p>
    </section>
  );
}
