"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import { PostSummary } from "@/lib/api/community";

interface PostCardProps {
  post: PostSummary;
  isSelected: boolean;
  onToggleSelect: () => void;
  onDelete: () => void;
}

export function PostCard({ post, isSelected, onToggleSelect, onDelete }: PostCardProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // 메뉴 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isMenuOpen]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const formatCount = (count: number): string => {
    if (count >= 1000) return "999+";
    return count.toString();
  };

  const handleEdit = () => {
    alert("게시물 수정 기능은 추후 구현 예정입니다.");
    setIsMenuOpen(false);
  };

  const handleDeleteClick = () => {
    if (confirm("정말로 이 게시물을 삭제하시겠습니까?")) {
      onDelete();
    }
    setIsMenuOpen(false);
  };

  return (
    <div className="bg-base-0 border border-surface rounded-lg p-4 hover:shadow-elev-card transition-shadow">
      {/* 첫 번째 줄: 태그, 제목, 날짜, 체크박스 */}
      <div className="flex items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {post.tags && post.tags.length > 0 && (
              <div className="flex gap-1">
                {post.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-brand-soft text-brand text-xs rounded-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          <h3 className="text-lg font-semibold text-text-body mb-1">
            {post.title}
          </h3>
          <p className="text-sm text-text-muted">
            {formatDate(post.createdAt)}
          </p>
        </div>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="w-5 h-5 cursor-pointer"
        />
      </div>

      {/* 두 번째 줄: 내용 미리보기, 케밥 메뉴 */}
      <div className="flex items-start mb-3">
        <p className="flex-1 text-sm text-text-muted line-clamp-2">
          {post.contentPreview}
        </p>
        <div className="relative ml-2" ref={menuRef}>
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="p-1 hover:bg-surface rounded transition-colors"
          >
            <Image
              src="/icons/more_vert.svg"
              alt="메뉴"
              width={20}
              height={20}
            />
          </button>

          {isMenuOpen && (
            <div className="absolute right-0 mt-1 w-32 bg-base-0 border border-surface rounded-lg shadow-elev-strong z-10">
              <button
                onClick={handleEdit}
                className="w-full px-4 py-2 text-left text-sm text-text-body hover:bg-surface transition-colors"
              >
                수정
              </button>
              <button
                onClick={handleDeleteClick}
                className="w-full px-4 py-2 text-left text-sm text-price-down hover:bg-surface transition-colors"
              >
                삭제
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 세 번째 줄: 조회수, 좋아요수, 댓글수 */}
      <div className="flex items-center gap-4 text-sm text-text-muted">
        <div className="flex items-center gap-1">
          <span>👁</span>
          <span>{formatCount(post.viewCount)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>❤</span>
          <span>{formatCount(post.likeCount)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span>💬</span>
          <span>{formatCount(post.commentCount)}</span>
        </div>
      </div>
    </div>
  );
}
