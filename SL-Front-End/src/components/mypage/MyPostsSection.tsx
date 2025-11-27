"use client";

import Image from "next/image";
import { useState, useEffect } from "react";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
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

  // 알림 모달 상태
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    iconType: "info" | "warning" | "error" | "success" | "question";
  }>({ isOpen: false, title: "", message: "", iconType: "info" });

  // 삭제 확인 모달 상태
  const [deleteConfirmModal, setDeleteConfirmModal] = useState(false);

  // 알림 모달 표시 헬퍼
  const showAlert = (
    title: string,
    message: string,
    iconType: "info" | "warning" | "error" | "success" | "question" = "info"
  ) => {
    setAlertModal({ isOpen: true, title, message, iconType });
  };

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

  const handleDeleteSelected = () => {
    if (selectedPostIds.size === 0) {
      showAlert("알림", "삭제할 게시물을 선택해주세요.", "warning");
      return;
    }

    // 삭제 확인 모달 표시
    setDeleteConfirmModal(true);
  };

  // 삭제 확인 후 실제 삭제 수행
  const handleConfirmDelete = async () => {
    setDeleteConfirmModal(false);

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
      showAlert("삭제 완료", "게시물이 삭제되었습니다.", "success");
    } catch (error) {
      console.error("게시물 삭제 실패:", error);
      showAlert("삭제 실패", "게시물 삭제에 실패했습니다.", "error");
    }
  };

  const handleDeletePost = async (postId: string) => {
    try {
      await communityApi.deletePost(postId);
      setPosts((prev) => prev.filter((post) => post.postId !== postId));
      showAlert("삭제 완료", "게시물이 삭제되었습니다.", "success");
    } catch (error) {
      console.error("게시물 삭제 실패:", error);
      showAlert("삭제 실패", "게시물 삭제에 실패했습니다.", "error");
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

  const handleClearTags = () => setSelectedTags([]);

  const renderTagButton = (tag: string, isActive: boolean, onClick: () => void) => (
    <button
      key={tag}
      onClick={onClick}
      className={`rounded-full px-5 py-1.5 text-[0.875rem] font-normal transition ${
        isActive
          ? "bg-brand-purple text-white font-semibold"
          : "border-[1px] border-[#18223414] text-muted font-normal hover:bg-brand-purple/30 hover:text-white hover:border-brand-purple/30"
      }`}
    >
      {tag}
    </button>
  );

  return (
    <section className="rounded-[12px] p-7 shadow-elev-card backdrop-blur bg-[#1822340D]">
      <div className="flex flex-col gap-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[0.75rem] font-normal uppercase tracking-widest text-[#646464]">Community</p>
            <h2 className="text-[1.5rem] font-semibold text-[#000000]">내 게시물 모아보기</h2>
          </div>
          <button
            onClick={handleDeleteSelected}
            disabled={selectedPostIds.size === 0}
            className="rounded-full bg-price-up px-5 py-2 text-[0.875rem] font-semibold text-white transition hover:bg-[#FF6464CC] disabled:cursor-not-allowed disabled:opacity-30"
          >
            선택 항목 삭제 ({selectedPostIds.size})
          </button>
        </div>

        {/* 검색 및 정렬 */}
        <div className="flex flex-col gap-5 md:flex-row">
          <div className="flex flex-1 items-center rounded-[12px] border-[0.5px] border-[#C8C8C8] bg-[#FFFFFF33] px-[1rem] py-[0.75rem]">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="게시글 검색"
              className="flex-1 bg-transparent text-[#000000] placeholder:text-[#C8C8C8] focus:outline-none"
            />
          </div>
          <button
            onClick={() => setSearchQuery(searchQuery.trim())}
            className="flex items-center justify-center gap-2 rounded-[12px] bg-brand-purple px-5 py-2 font-normal text-white shadow-elev-card-soft hover:bg-brand-purple/80"
          >
            <Image
              src="/icons/search.svg"
              alt="검색 아이콘"
              width={20}
              height={20}
              className=""
            />
            검색
          </button>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "latest" | "views" | "likes")}
            className="rounded-[12px] border-[0.5px] border-[#C8C8C8] bg-white px-5 text-[0.875rem] font-normal text-[#000000] focus:outline-none"
          >
            <option value="latest">날짜 순 정렬</option>
            <option value="views">조회수 순 정렬</option>
            <option value="likes">좋아요 순 정렬</option>
          </select>
        </div>

        {/* 태그 필터 */}
        <div className="flex flex-wrap items-center gap-2">
          {renderTagButton("전체", selectedTags.length === 0, handleClearTags)}
          {allTags.length === 0 ? (
            <span className="text-sm text-[#9da5c9]">등록된 태그가 없습니다.</span>
          ) : (
            allTags.slice(0, 8).map((tag, index) =>
              renderTagButton(tag, selectedTags.includes(tag), () => handleTagClick(tag))
            )
          )}
        </div>

      {/* 게시물 리스트 */}
        {isLoading ? (
          <div className="py-12 text-center">
            <div className="mx-auto h-12 w-12 animate-spin rounded-full border-2 border-[#c4cbff] border-t-[#6f7bff]" />
            <p className="mt-4 text-sm text-[#6d749b]">게시물을 불러오는 중...</p>
          </div>
        ) : filteredPosts.length === 0 ? (
          <div className="rounded-[12px] border border-dashed border-[#C8C8C8] bg-[#ffffffCC] py-12 text-center text-muted">
            게시물이 없습니다
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

      {/* 알림 모달 */}
      <ConfirmModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        onConfirm={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        title={alertModal.title}
        message={alertModal.message}
        confirmText="확인"
        iconType={alertModal.iconType}
        alertOnly
      />

      {/* 삭제 확인 모달 */}
      <ConfirmModal
        isOpen={deleteConfirmModal}
        onClose={() => setDeleteConfirmModal(false)}
        onConfirm={handleConfirmDelete}
        title="게시물 삭제"
        message={`선택한 ${selectedPostIds.size}개의 게시물을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`}
        confirmText="삭제"
        cancelText="취소"
        iconType="warning"
      />
    </section>
  );
}
