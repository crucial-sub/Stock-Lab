"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

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
          {tagOptions.map((tag) => {
            const selected = selectedTags.includes(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => handleTagToggle(tag)}
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
