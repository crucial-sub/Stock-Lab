"use client";

import type { NextPage } from "next";
import { useEffect, useState } from "react";

import { Icon } from "@/components/common/Icon";
import { NewsCard } from "@/components/news/NewsCard";
import { NewsDetailModal } from "@/components/news/NewsDetailModal";
import { useAvailableThemesQuery, useDebounce, useNewsDetailQuery, useNewsListQuery } from "@/hooks";
import type { NewsListParams } from "@/types/news";

const NewsPage: NextPage = () => {
  const [selectedThemes, setSelectedThemes] = useState<string[]>(["전체"]);
  const [keyword, setKeyword] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedNewsId, setSelectedNewsId] = useState<string | null>(null);
  const [displayThemes, setDisplayThemes] = useState<string[]>([]);

  const debouncedKeyword = useDebounce(keyword, 300);

  // React Compiler가 자동으로 메모이제이션 처리
  const themes = selectedThemes.includes("전체") ? [] : selectedThemes;
  const newsParams: NewsListParams = {
    keyword: debouncedKeyword || undefined,
    themes: themes.length ? themes : undefined,
    filter,
  };
  // Fetch available themes from database
  const { data: availableThemes = [] } = useAvailableThemesQuery();

  // Update display themes when available themes change
  useEffect(() => {
    if (availableThemes.length > 0) {
      setDisplayThemes(["전체", ...availableThemes]);
    }
  }, [availableThemes]);

  const {
    data: newsList = [],
    isLoading,
    isError,
  } = useNewsListQuery(newsParams);

  const { data: selectedNews } = useNewsDetailQuery(selectedNewsId ?? undefined);

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
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
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
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          className="rounded-[8px] shadow-card-muted bg-white px-[1rem] pr-[2.5rem] py-[0.5rem] text-text-body focus:border-brand-primary focus:outline-none"
        >
          <option value="all">전체</option>
          <option value="latest">최신순</option>
          <option value="popular">인기순</option>
        </select>
      </div>

      <div className="flex flex-wrap gap-3">
        {displayThemes.map((theme: string) => {
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

      {isLoading && (
        <p className="text-center text-text-muted">뉴스를 불러오는 중입니다...</p>
      )}
      {isError && (
        <p className="text-center text-accent-primary">뉴스 데이터를 불러오지 못했습니다.</p>
      )}

      {!isLoading && !isError && (
        <div className="grid gap-4 md:grid-cols-3">
          {newsList.map((item, index: number) => (
            <NewsCard
              key={`${item.id}-${index}`}
              id={item.id}
              title={item.title}
              summary={item.content || item.title}
              tickerLabel={item.stock_name || item.stock_code || "종목"}
              themeName={item.themeName}
              sentiment="neutral"
              publishedAt={typeof item.date === 'string' ? item.date : item.date?.display || ''}
              source={item.source}
              link={item.link}
              onClick={() => setSelectedNewsId(item.id)}
            />
          ))}
          {!newsList.length && (
            <p className="col-span-full text-center text-text-muted">
              조건에 해당하는 뉴스가 없습니다.
            </p>
          )}
        </div>
      )}

      {selectedNewsId && selectedNews && (
        <NewsDetailModal news={selectedNews} onClose={() => setSelectedNewsId(null)} />
      )}
    </section>
  );
};

export default NewsPage;