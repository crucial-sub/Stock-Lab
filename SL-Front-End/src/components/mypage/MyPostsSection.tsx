"use client";

import { useState, useEffect } from "react";
import { communityApi, PostSummary } from "@/lib/api/community";
import { PostCard } from "./PostCard";

interface MyPostsSectionProps {
  userId: string;
}

export function MyPostsSection({ userId }: MyPostsSectionProps) {
  const [posts, setPosts] = useState<PostSummary[]>([]);
  const [filteredPosts, setFilteredPosts] = useState<PostSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<"latest" | "views" | "likes">("latest");
  const [selectedPostIds, setSelectedPostIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);

  // 게시물 불러오기
  useEffect(() => {
    const fetchMyPosts = async () => {
      setIsLoading(true);
      try {
        // 백엔드 user_id 필터 사용
        const response = await communityApi.getPosts({
          userId: userId,
          limit: 100
        });

        setPosts(response.posts);
        setFilteredPosts(response.posts);
      } catch (error) {
        console.error("게시물 로딩 실패:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (userId) {
      fetchMyPosts();
    }
  }, [userId]);

  // 검색, 태그, 정렬 필터링
  useEffect(() => {
    let result = [...posts];

    // 검색 필터
    if (searchQuery) {
      result = result.filter((post) =>
        post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.contentPreview.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // 태그 필터
    if (selectedTags.length > 0) {
      result = result.filter((post) =>
        post.tags?.some((tag) => selectedTags.includes(tag))
      );
    }

    // 정렬
    switch (sortBy) {
      case "latest":
        result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
        break;
      case "views":
        result.sort((a, b) => b.viewCount - a.viewCount);
        break;
      case "likes":
        result.sort((a, b) => b.likeCount - a.likeCount);
        break;
    }

    setFilteredPosts(result);
  }, [posts, searchQuery, selectedTags, sortBy]);

  const handleToggleSelect = (postId: string) => {
    const newSelected = new Set(selectedPostIds);
    if (newSelected.has(postId)) {
      newSelected.delete(postId);
    } else {
      newSelected.add(postId);
    }
    setSelectedPostIds(newSelected);
  };

  const handleDeleteSelected = async () => {
    if (selectedPostIds.size === 0) {
      alert("삭제할 게시물을 선택해주세요");
      return;
    }

    if (!confirm(`선택한 ${selectedPostIds.size}개의 게시물을 삭제하시겠습니까?`)) {
      return;
    }

    try {
      // 선택된 게시물 삭제
      await Promise.all(
        Array.from(selectedPostIds).map((postId) =>
          communityApi.deletePost(postId)
        )
      );

      // 삭제된 게시물 제거
      setPosts((prev) => prev.filter((post) => !selectedPostIds.has(post.postId)));
      setSelectedPostIds(new Set());
      alert("게시물이 삭제되었습니다");
    } catch (error) {
      console.error("게시물 삭제 실패:", error);
      alert("게시물 삭제에 실패했습니다");
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      await communityApi.deletePost(postId);
      setPosts((prev) => prev.filter((post) => post.postId !== postId));
      alert("게시물이 삭제되었습니다");
    } catch (error) {
      console.error("게시물 삭제 실패:", error);
      alert("게시물 삭제에 실패했습니다");
    }
  };

  const handleTagClick = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  // 사용 가능한 모든 태그 추출
  const allTags = Array.from(
    new Set(posts.flatMap((post) => post.tags || []))
  );

  return (
    <div className="quant-shell">
      <h2 className="text-2xl font-bold text-text-body mb-6">내 게시물 모아보기</h2>

      {/* 검색 및 정렬 */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="게시글 검색"
          className="flex-1 px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
        />
        <button
          onClick={() => setSearchQuery(searchQuery)}
          className="px-6 py-3 bg-button-primary-soft text-brand rounded-lg hover:bg-brand hover:text-base-0 transition-colors"
        >
          검색
        </button>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "latest" | "views" | "likes")}
          className="px-4 py-3 bg-surface border border-surface rounded-lg text-text-body focus:border-brand-soft focus:shadow-elev-brand transition-all"
        >
          <option value="latest">최신순</option>
          <option value="views">조회수순</option>
          <option value="likes">좋아요순</option>
        </select>
      </div>

      {/* 태그 필터 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {allTags.length === 0 ? (
            <span className="text-sm text-text-muted">태그 없음</span>
          ) : (
            <>
              {allTags.slice(0, 10).map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleTagClick(tag)}
                  className={`px-3 py-1 rounded-sm text-sm transition-colors ${
                    selectedTags.includes(tag)
                      ? "bg-brand text-base-0"
                      : "bg-brand-soft text-brand hover:bg-brand hover:text-base-0"
                  }`}
                >
                  {tag}
                </button>
              ))}
            </>
          )}
        </div>
        <button
          onClick={handleDeleteSelected}
          disabled={selectedPostIds.size === 0}
          className="px-4 py-2 bg-surface text-price-down rounded-lg hover:bg-price-up transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          선택 항목 삭제하기 ({selectedPostIds.size})
        </button>
      </div>

      {/* 게시물 리스트 */}
      {isLoading ? (
        <div className="py-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto" />
          <p className="mt-4 text-text-muted">게시물을 불러오는 중...</p>
        </div>
      ) : filteredPosts.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-text-muted text-lg">게시물이 없습니다</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredPosts.map((post) => (
            <PostCard
              key={post.postId}
              post={post}
              isSelected={selectedPostIds.has(post.postId)}
              onToggleSelect={() => handleToggleSelect(post.postId)}
              onDelete={() => handleDeletePost(post.postId)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
