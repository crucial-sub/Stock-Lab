"use client";

import type { NextPage } from "next";
import { useEffect, useState } from "react";

import { Icon } from "@/components/common/Icon";
import { NewsCard } from "@/components/news/NewsCard";
import { NewsDetailModal } from "@/components/news/NewsDetailModal";
import {
  useAvailableThemesQuery,
  useDebounce,
  useNewsListQuery,
} from "@/hooks";
import type { NewsItem, NewsListParams } from "@/types/news";

const NewsPage: NextPage = () => {
  const [selectedThemes, setSelectedThemes] = useState<string[]>(["전체"]);
  const [keyword, setKeyword] = useState<string>("");
  const [filter, setFilter] = useState<string>("all");
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

  // 목록 데이터에서 직접 상세 뉴스 찾기 (이미 전체 데이터가 포함되어 있음)
  const selectedNews: NewsItem | undefined = selectedNewsId
    ? newsList.find((item: NewsItem) => item.id === selectedNewsId)
    : undefined;

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
    <section className="flex flex-col gap-[1.875rem] px-[18.75rem] py-[3.75rem]">
      <h1 className="text-[1.75rem] font-semibold text-black ml-[1.875rem]">
        테마별 요약 뉴스
      </h1>

      <div className="flex flex-col gap-4">
        {/* 검색 및 정렬 영역 */}
        <div className="flex items-center gap-3 justify-between">
          {/* 검색 입력과 버튼 */}
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1 max-w-[500px]">
              <input
                type="search"
                placeholder="뉴스 검색"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                className="w-full h-9 rounded-lg bg-surface border-[0.5px] border-surface py-[0.5rem] px-[0.813rem] text-[0.75rem] text-gray-600 placeholder:text-gray-600 focus:border-brand-purple focus:outline-none"
              />
            </div>
            <button
              type="button"
              className="flex size-9 items-center justify-center rounded-lg bg-brand-purple hover:bg-brand-purple/90 transition"
              aria-label="검색"
            >
              <Icon
                src="/icons/search.svg"
                alt="검색"
                size={20}
                color="white"
              />
            </button>
          </div>

          {/* 정렬 드롭다운 */}
          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            className="h-9 rounded-lg bg-white border-[0.5px] border-surface px-3 text-[0.75rem] text-gray-600 focus:border-brand-purple focus:outline-none"
          >
            <option value="all">날짜 순 정렬</option>
            <option value="latest">최신순</option>
            <option value="popular">인기순</option>
          </select>
        </div>

        {/* 필터 버튼 영역 */}
        <div className="flex flex-wrap gap-1">
          {displayThemes.map((theme: string) => {
            const isActive = selectedThemes.includes(theme);
            return (
              <button
                key={theme}
                type="button"
                onClick={() => handleToggleTheme(theme)}
                className={`rounded-full px-3 py-2 text-[1rem] tracking-[-0.02em] transition ${
                  isActive
                    ? "bg-brand-purple text-white font-semibold"
                    : "text-black font-normal"
                }`}
              >
                {theme}
              </button>
            );
          })}
        </div>
      </div>

      {isLoading && (
        <p className="text-center text-text-body">
          뉴스를 불러오는 중입니다...
        </p>
      )}
      {isError && (
        <p className="text-center text-accent-primary">
          뉴스 데이터를 불러오지 못했습니다.
        </p>
      )}

      {!isLoading && !isError && (
        <div className="grid gap-4 md:grid-cols-2">
          {newsList.map((item, index: number) => (
            <NewsCard
              key={`${item.id}-${index}`}
              id={item.id}
              title={item.title}
              summary={item.summary || ""}
              tickerLabel={item.tickerLabel || item.stockCode || "종목"}
              themeName={item.themeName}
              pressName={item.pressName}
              sentiment={
                (item.sentiment as "positive" | "negative" | "neutral") ||
                "neutral"
              }
              publishedAt={item.publishedAt || ""}
              source={item.source || ""}
              link={item.link || ""}
              onClick={() => setSelectedNewsId(item.id)}
            />
          ))}
          {!newsList.length && (
            <p className="col-span-full text-center text-text-body">
              조건에 해당하는 뉴스가 없습니다.
            </p>
          )}
        </div>
      )}

      {selectedNewsId && selectedNews && (
        <NewsDetailModal
          news={selectedNews}
          onClose={() => setSelectedNewsId(null)}
        />
      )}
    </section>
  );
};

export default NewsPage;
