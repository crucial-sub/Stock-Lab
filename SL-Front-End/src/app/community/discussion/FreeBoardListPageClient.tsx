"use client";

import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import {
  FreeBoardPostCard,
} from "@/components/community";
import { usePostsQuery } from "@/hooks/useCommunityQuery";
import { useDebounce } from "@/hooks";

const TAG_FILTERS = ["전체", "질문", "토론", "정보 공유"];
const SORT_OPTIONS = [
  { label: "날짜 순 정렬", value: "createdAt_desc" },
  { label: "공감 순 정렬", value: "like_desc" },
];

interface FreeBoardListPageClientProps {
  searchParams: Record<string, string | undefined>;
}

export function FreeBoardListPageClient({
  searchParams,
}: FreeBoardListPageClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const [searchInput, setSearchInput] = useState(searchParams.q ?? "");
  const [selectedTag, setSelectedTag] = useState(
    searchParams.tag ?? TAG_FILTERS[0],
  );
  const [sortOption, setSortOption] = useState(
    searchParams.sort ?? SORT_OPTIONS[0].value,
  );
  const [page, setPage] = useState(
    Number(searchParams.page) > 0 ? Number(searchParams.page) : 1,
  );

  const debouncedSearch = useDebounce(searchInput, 300);

  const queryParams = useMemo(
    () => ({
      postType: "DISCUSSION",
      search: debouncedSearch || undefined,
      tags:
        selectedTag && selectedTag !== TAG_FILTERS[0]
          ? selectedTag
          : undefined,
      page,
      limit: 10,
      orderBy: sortOption,
    }),
    [debouncedSearch, selectedTag, page, sortOption],
  );

  const { data, isLoading, isError } = usePostsQuery(queryParams);

  const updateSearchParams = (next: Record<string, string | number>) => {
    const newParams = new URLSearchParams(params.toString());
    Object.entries(next).forEach(([key, value]) => {
      if (value === "" || value === undefined || value === null) {
        newParams.delete(key);
      } else {
        newParams.set(key, String(value));
      }
    });
    const queryString = newParams.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname, {
      scroll: false,
    });
  };

  const handleSearch = () => {
    setPage(1);
    updateSearchParams({
      q: searchInput || "",
      tag: selectedTag !== TAG_FILTERS[0] ? selectedTag : "",
      sort: sortOption,
      page: 1,
    });
  };

  const handleTagClick = (tag: string) => {
    setSelectedTag(tag);
    setPage(1);
    updateSearchParams({
      tag: tag !== TAG_FILTERS[0] ? tag : "",
      page: 1,
    });
  };

  const handleSortChange = (value: string) => {
    setSortOption(value);
    setPage(1);
    updateSearchParams({ sort: value, page: 1 });
  };

  const handlePageChange = (nextPage: number) => {
    if (nextPage < 1 || (data && !data.hasNext && nextPage > data.page)) return;
    setPage(nextPage);
    updateSearchParams({ page: nextPage });
  };

  return (
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-10">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-6">
        <button
          type="button"
          onClick={() => router.back()}
          className="text-sm text-[#646464] hover:text-black"
        >
          ← 돌아가기
        </button>

        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold text-black">자유게시판</h1>
          <button
            type="button"
            onClick={() => router.push("/community/discussion/new")}
            className="rounded-[12px] bg-brand-purple px-4 py-2 text-sm font-semibold text-white hover:bg-brand-purple/90"
          >
            새 글 작성하기
          </button>
        </header>

        <div className="flex flex-wrap items-center gap-3 rounded-[12px] border border-[#18223414] bg-[#1822340D] p-4">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="게시글 검색"
            className="flex-1 rounded-[12px] border border-[#18223414] bg-white px-4 py-3 text-sm text-black placeholder:text-[#AC64FF80] focus:border-brand-purple focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSearch}
            className="rounded-[12px] bg-brand-purple px-4 py-3 text-sm font-semibold text-white hover:bg-brand-purple/90"
          >
            검색
          </button>
          <select
            value={sortOption}
            onChange={(e) => handleSortChange(e.target.value)}
            className="rounded-[12px] border border-[#18223414] bg-white px-3 py-3 text-sm text-[#646464] focus:border-brand-purple focus:outline-none"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap gap-2">
          {TAG_FILTERS.map((tag) => {
            const selected = selectedTag === tag;
            return (
              <button
                key={tag}
                type="button"
                onClick={() => handleTagClick(tag)}
                className={`rounded-full px-4 py-1 text-sm font-semibold ${
                  selected
                    ? "bg-brand-purple text-white"
                    : "bg-[#1822340D] text-[#646464]"
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>

        <div className="flex flex-col gap-4">
          {isLoading && (
            <p className="py-10 text-center text-[#646464]">로딩 중...</p>
          )}
          {isError && (
            <p className="py-10 text-center text-[#646464]">
              게시글을 불러오지 못했습니다.
            </p>
          )}
          {!isLoading && !isError && data?.posts.length === 0 && (
            <p className="py-10 text-center text-[#646464]">
              게시글이 없습니다.
            </p>
          )}
          {data?.posts.map((post) => (
            <FreeBoardPostCard
              key={post.postId}
              tag={post.tags?.[0] || "일반"}
              title={post.title}
              author={post.authorNickname || "익명"}
              date={new Date(post.createdAt).toLocaleString("ko-KR", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })}
              preview={post.contentPreview}
              views={post.viewCount}
              likes={post.likeCount}
              comments={post.commentCount}
              onClick={() => router.push(`/community/discussion/${post.postId}`)}
            />
          ))}
        </div>

        {data && (
          <div className="flex items-center justify-between text-sm text-[#646464]">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => handlePageChange(page - 1)}
              className={`rounded-[12px] px-4 py-2 ${
                page <= 1
                  ? "cursor-not-allowed bg-[#AC64FF80] text-white"
                  : "bg-brand-purple text-white hover:bg-brand-purple/90"
              }`}
            >
              이전
            </button>
            <span>
              {page} / {Math.max(1, Math.ceil(data.total / data.limit))}
            </span>
            <button
              type="button"
              disabled={!data.hasNext}
              onClick={() => handlePageChange(page + 1)}
              className={`rounded-[12px] px-4 py-2 ${
                !data.hasNext
                  ? "cursor-not-allowed bg-[#AC64FF80] text-white"
                  : "bg-brand-purple text-white hover:bg-brand-purple/90"
              }`}
            >
              다음
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
