"use client";

import { useState } from "react";
import type { NextPage } from "next";

import { Icon } from "@/components/common/Icon";
import { NewsCard } from "@/components/news/NewsCard";

const newsThemes = [
  "전체",
  "건설",
  "금속",
  "기계 / 장비",
  "농업 / 어업 / 임업",
  "보험",
  "부동산",
  "비금속",
  "섬유 / 의류",
  "오락 / 문화",
  "운송 / 창고",
  "운송장비 / 부품",
  "유통",
  "은행",
  "음식료 / 담배",
  "의료 / 정밀기기",
  "일반 서비스",
  "전기 / 가스 / 수도",
  "전기 / 전자",
  "제약",
  "종이 / 목재",
  "증권",
  "출판 / 매체 복제",
  "통신",
  "화학",
  "IT 서비스",
  "기타 금융",
  "기타 제조",
  "기타",
];

const NewsPage: NextPage = () => {
  const [selectedThemes, setSelectedThemes] = useState<string[]>(["전체"]);

  const mockNewsItems = [
    {
      title: "제목의 위치는 여기입니다.",
      summary:
        "여기에 간단한 내용이 들어갑니다. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
      tickerLabel: "종목 이름",
      sentiment: "positive" as const,
      publishedAt: "30분 전",
      source: "www.naver.com/example/link",
      link: "https://www.naver.com",
    },
    {
      title: "제목의 위치는 여기입니다.",
      summary:
        "여기에 간단한 내용이 들어갑니다. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
      tickerLabel: "종목 이름",
      sentiment: "neutral" as const,
      publishedAt: "1시간 전",
      source: "www.naver.com/example/link",
      link: "https://www.naver.com",
    },
    {
      title: "제목의 위치는 여기입니다.",
      summary:
        "여기에 간단한 내용이 들어갑니다. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
      tickerLabel: "종목 이름",
      sentiment: "negative" as const,
      publishedAt: "2시간 전",
      source: "www.naver.com/example/link",
      link: "https://www.naver.com",
    },
  ];

  const handleToggleTheme = (theme: string) => {
    if (theme === "전체") {
      setSelectedThemes(["전체"]);
      return;
    }

    setSelectedThemes((prev) => {
      const withoutAll = prev.filter((item) => item !== "전체");
      if (withoutAll.includes(theme)) {
        const next = withoutAll.filter((item) => item !== theme);
        return next.length ? next : ["전체"];
      }
      return [...withoutAll, theme];
    });
  };

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
          className="flex items-center justify-center rounded-[8px] bg-brand-primary px-[0.75rem] py-[0.75rem] text-white shadow-card-muted"
          aria-label="뉴스 검색"
        >
          <Icon src="/icons/search.svg" alt="검색" size={28} color="#FFFFFF" />
          검색
        </button>
        <select
          className="rounded-[8px] shadow-card-muted bg-white px-[1rem] py-[0.5rem] text-text-body focus:border-brand-primary focus:outline-none"
        >
          <option value="all">전체</option>
          <option value="stock">종목 뉴스</option>
          <option value="market">시장 동향</option>
        </select>
      </div>

      <div className="flex flex-wrap gap-3">
        {newsThemes.map((theme) => {
          const isActive = selectedThemes.includes(theme);
          return (
            <button
              key={theme}
              type="button"
              onClick={() => handleToggleTheme(theme)}
              className={`rounded-[4px] border px-[1.25rem] py-[0.5rem] text-[0.9rem] font-normal transition ${isActive
                ? "border-brand-primary bg-[#FFF6F6] text-brand-primary font-semibold"
                : "border-border-default bg-white text-text-body"
                }`}
            >
              {theme}
            </button>
          );
        })}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {mockNewsItems.map((item, index) => (
          <NewsCard key={`${item.title}-${index}`} {...item} />
        ))}
      </div>
    </section>
  );
};

export default NewsPage;
