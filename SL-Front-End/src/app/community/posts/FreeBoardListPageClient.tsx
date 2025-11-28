"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Icon } from "@/components/common/Icon";
import {
  FreeBoardPostCard,
} from "@/components/community";
import { usePostsQuery } from "@/hooks/useCommunityQuery";
import { useDebounce } from "@/hooks";

const DEFAULT_TAG_OPTIONS = ["전체", "질문", "토론", "정보 공유"];
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

  const [searchInput, setSearchInput] = useState("");
  const [tagOptions, setTagOptions] = useState<string[]>(DEFAULT_TAG_OPTIONS);
  const [selectedTags, setSelectedTags] = useState<string[]>(["전체"]);
  const [sortOption, setSortOption] = useState(SORT_OPTIONS[0].value);
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounce(searchInput, 300);
  const tagFilter = selectedTags.filter((t) => t !== "전체");

  const queryParams = useMemo(
    () => ({
      postType: "DISCUSSION",
      search: debouncedSearch || undefined,
      page,
      limit: 10,
      orderBy: sortOption,
    }),
    [debouncedSearch, page, sortOption],
  );

  const { data, isLoading, isError } = usePostsQuery(queryParams);

  // 태그 옵션을 데이터에서 수집
  useEffect(() => {
    if (!data?.posts) return;
    const collected = new Set<string>(DEFAULT_TAG_OPTIONS);
    data.posts.forEach((post) => post.tags?.forEach((t) => collected.add(t)));
    const next = Array.from(collected);
    if (next.join(",") !== tagOptions.join(",")) {
      setTagOptions(next);
    }
    // 선택된 태그가 옵션에 없으면 전체로 리셋
    const invalidSelected = selectedTags.filter(
      (t) => t !== "전체" && !collected.has(t),
    );
    if (invalidSelected.length) {
      setSelectedTags(["전체"]);
      setPage(1);
    }
  }, [data?.posts, tagOptions, selectedTags]);

  const filteredPosts = useMemo(() => {
    if (!data?.posts) return [];
    if (!tagFilter.length || selectedTags.includes("전체")) return data.posts;
    return data.posts.filter((post) =>
      post.tags?.some((t) => tagFilter.includes(t)),
    );
  }, [data?.posts, tagFilter, selectedTags]);

  const handleSearch = () => {
    setPage(1);
    // 실제 API 요청은 상태 변경으로 트리거됨
  };

  const handleTagToggle = (tag: string) => {
    if (tag === "전체") {
      setSelectedTags(["전체"]);
      setPage(1);
      return;
    }
    setSelectedTags((prev) => {
      const withoutAll = prev.filter((t) => t !== "전체");
      const next = withoutAll.includes(tag)
        ? withoutAll.filter((t) => t !== tag)
        : [...withoutAll, tag];
      const final = next.length ? next : ["전체"];
      setPage(1);
      return final;
    });
  };

  const handleSortChange = (value: string) => {
    setSortOption(value);
    setPage(1);
  };

  const handlePageChange = (nextPage: number) => {
    if (nextPage < 1 || (data && !data.hasNext && nextPage > data.page)) return;
    setPage(nextPage);
  };

  return (
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-[60px]">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col">
        <button
          type="button"
          onClick={() => router.back()}
          className="self-start inline-flex items-center gap-1 text-[0.875rem] text-[#646464]"
        >
          <Icon
            src="/icons/arrow_left.svg"
            alt="뒤로가기"
            size={20}
            color="#646464"
          />
          돌아가기
        </button>

        <header className="flex items-center justify-between">
          <span className="my-[40px] text-[1.5rem] font-semibold text-black">
            자유게시판
          </span>
        </header>

        <div className="flex flex-wrap gap-5">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="게시글 검색"
            className="flex-1 rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] px-5 py-3 text-[1rem] text-black placeholder:text-muted focus:outline-none"
          />
          <button
            type="button"
            onClick={handleSearch}
            className="inline-flex items-center gap-2 rounded-[12px] bg-brand-purple px-5 py-2 text-[0.875rem] font-semibold text-white hover:bg-brand-purple/80"
          >
            <Icon
              src="/icons/search.svg"
              alt="검색"
              size={20}
              color="#FFFFFF"
            />
            검색
          </button>
          <select
            value={sortOption}
            onChange={(e) => handleSortChange(e.target.value)}
            className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] px-4 py-2 text-[0.875rem] text-[#646464] focus:outline-none"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="my-[20px] flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {tagOptions.map((tag) => {
              const selected = selectedTags.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagToggle(tag)}
                  className={`rounded-full px-4 pt-1.5 pb-1 text-[0.875rem] ${
                    selected
                      ? "bg-brand-purple text-white font-semibold"
                      : "text-[#646464] font-normal border-[1px] border-[#1822340D]"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
          <button
            type="button"
            onClick={() => router.push("/community/posts/new")}
            className="rounded-full bg-brand-purple px-4 pt-1.5 pb-1 text-[0.875rem] font-semibold text-white hover:bg-brand-purple/80"
          >
            새 글 작성하기
          </button>
        </div>

        <div className="flex flex-col gap-5">
          {isLoading && (
            <p className="py-10 text-center text-[#646464]">로딩 중...</p>
          )}
          {isError && (
            <p className="py-10 text-center text-[#646464]">
              게시글을 불러오지 못했습니다.
            </p>
          )}
          {!isLoading && !isError && filteredPosts.length === 0 && (
            <p className="py-10 text-center text-[#646464]">
              게시글이 없습니다.
            </p>
          )}
          {filteredPosts.map((post) => (
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
              onClick={() => router.push(`/community/${post.postId}`)}
            />
          ))}
        </div>

        {data && (
          <div className="mt-[20px] flex items-center justify-center gap-6 text-sm text-[#646464]">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => handlePageChange(page - 1)}
              className={`flex h-10 w-10 items-center justify-center ${
                page <= 1
                  ? "cursor-not-allowed"
                  : ""
              }`}
            >
              <Icon
                src="/icons/arrow_left.svg"
                alt="이전 페이지"
                size={24}
                color="#646464"
              />
            </button>
            <span>
              {page} / {Math.max(1, Math.ceil(data.total / data.limit))}
            </span>
            <button
              type="button"
              disabled={!data.hasNext}
              onClick={() => handlePageChange(page + 1)}
              className={`flex h-10 w-10 items-center justify-center ${
                !data.hasNext
                  ? "cursor-not-allowed"
                  : ""
              }`}
            >
              <Icon
                src="/icons/arrow_right.svg"
                alt="다음 페이지"
                size={24}
                color="#646464"
              />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
