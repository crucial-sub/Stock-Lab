"use client";

import type { NextPage } from "next";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

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
  const searchParams = useSearchParams();

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

  const sortedNewsList = useMemo(() => {
    return [...newsList].sort((a, b) => {
      const aTime = new Date(a.publishedAt || "").getTime();
      const bTime = new Date(b.publishedAt || "").getTime();
      return bTime - aTime;
    });
  }, [newsList]);

  // 목록 데이터에서 직접 상세 뉴스 찾기 (이미 전체 데이터가 포함되어 있음)
  const selectedNews: NewsItem | undefined = selectedNewsId
    ? newsList.find((item: NewsItem) => item.id === selectedNewsId)
    : undefined;

  useEffect(() => {
    const newsIdParam = searchParams.get("newsId");
    if (newsIdParam) {
      setSelectedNewsId(newsIdParam);
    }
  }, [searchParams]);

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
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-[60px]">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-[40px]">
        <span className="text-[1.5rem] font-semibold text-black ml-[0rem]">
          테마별 요약 뉴스
        </span>

        <div className="flex flex-col gap-5">
        {/* 검색 및 정렬 영역 */}
        <div className="flex items-center">
          {/* 검색 입력과 버튼 */}
          <div className="flex items-center gap-3 flex-1">
            <div className="relative flex-1">
              <input
                type="search"
                placeholder="뉴스 검색"
                value={keyword}
                onChange={(event) => setKeyword(event.target.value)}
                className="w-full rounded-[12px] bg-surface border-[0.5px] border-surface py-[0.7rem] px-[1rem] text-[1rem] text-gray-600 placeholder:text-gray-600 focus:border-brand-purple focus:outline-none"
              />
            </div>
            <button
              type="button"
              className="flex items-center gap-1 rounded-[12px] bg-brand-purple px-3 py-3 text-white hover:bg-brand-purple/90 transition"
            >
              <Icon
                src="/icons/search.svg"
                alt="검색"
                size={24}
                color="white"
              />
              <span className="text-[16px] font-semibold">검색</span>
            </button>
          </div>
          <div className="pr-[12px]"></div>

          {/* 정렬 드롭다운 */}
          <select
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            className="rounded-lg bg-[#1822340D] border-[0.5px] border-surface px-3 py-3.5 text-[14px] text-muted focus:border-brand-purple focus:outline-none"
          >
            <option value="all">날짜 순 정렬</option>
            <option value="latest">최신순</option>
            <option value="popular">인기순</option>
          </select>
        </div>

        {/* 필터 버튼 영역 */}
        <div className="flex flex-wrap gap-2">
          {displayThemes.map((theme: string) => {
            const isActive = selectedThemes.includes(theme);
            return (
              <button
                key={theme}
                type="button"
                onClick={() => handleToggleTheme(theme)}
                className={`rounded-full px-5 py-1.5 text-[1rem] transition ${
                  isActive
                    ? "bg-brand-purple text-white font-semibold"
                    : "border-[1px] border-[#18223414] text-muted font-normal"
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
            {sortedNewsList.map((item, index: number) => (
              <NewsCard
                key={`${item.id}-${index}`}
                id={item.id}
                title={item.title}
                summary={item.summary || ""}
                tickerLabel={item.tickerLabel || item.stockCode || "종목"}
                themeName={item.themeName}
                pressName={item.pressName || item.source || undefined}
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
      </div>
    </section>
  );
};

export default NewsPage;
