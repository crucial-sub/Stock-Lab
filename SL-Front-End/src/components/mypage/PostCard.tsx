"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
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

  // 알림 모달 상태
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    iconType: "info" | "warning" | "error" | "success" | "question";
  }>({ isOpen: false, title: "", message: "", iconType: "info" });

  // 삭제 확인 모달 상태
  const [deleteConfirmModal, setDeleteConfirmModal] = useState(false);

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
    setAlertModal({
      isOpen: true,
      title: "알림",
      message: "게시물 수정 기능은 추후 구현 예정입니다.",
      iconType: "info",
    });
    setIsMenuOpen(false);
  };

  const handleDeleteClick = () => {
    setDeleteConfirmModal(true);
    setIsMenuOpen(false);
  };

  const handleConfirmDelete = () => {
    setDeleteConfirmModal(false);
    onDelete();
  };

  return (
    <div className="rounded-[12px] border-[0.5px] border-[#C8C8C8] bg-[#FFFFFF80] p-5 shadow-elev-card-soft transition hover:translate-y-[-2px]">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-start">
          <div className="flex-1">
            {post.tags && post.tags.length > 0 && (
              <div className="flex flex-wrap gap-0">
                {post.tags.map((tag, index) => (
                  <span
                    key={`${tag}-${index}`}
                    className="rounded-full mb-2 bg-brand-purple px-3 py-1 text-[0.75rem] font-normal text-[#FFFFFF]"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <Link href={`/community/${post.postId}`} className="hover:underline">
              <h3 className="text-[1.25rem] font-semibold text-[#000000]">{post.title}</h3>
            </Link>
            <p className="text-[0.75rem] text-muted">{formatDate(post.createdAt)}</p>
          </div>
          <div className="flex items-center gap-2">
            <label className="relative cursor-pointer">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={onToggleSelect}
                className="peer sr-only"
              />
              <Image
                src="/icons/check-box-blank.svg"
                alt="선택 안 됨"
                width={24}
                height={24}
                className="peer-checked:hidden"
              />
              <Image
                src="/icons/check-box_brand.svg"
                alt="선택됨"
                width={24}
                height={24}
                className="hidden peer-checked:block"
              />
            </label>
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-[#000000] transition hover:bg-[#e5e9ff]"
              >
                <Image src="/icons/more_vert.svg" alt="메뉴" width={20} height={20} />
              </button>
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-32 rounded-[12px] border border-[#dbe3f5] bg-white p-1 shadow-elev-card-soft">
                  <button
                    onClick={handleEdit}
                    className="w-full rounded-[8px] px-4 py-2 text-left text-sm text-[#000000] transition hover:bg-[#f3f5ff]"
                  >
                    수정
                  </button>
                  <button
                    onClick={handleDeleteClick}
                    className="w-full rounded-[8px] px-4 py-2 text-left text-sm text-price-up transition hover:bg-[#ff64641A]"
                  >
                    삭제
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        <p className="text-[1rem] text-[#000000]">
          {post.contentPreview}
        </p>

        <div className="flex flex-wrap items-center gap-3 text-[0.875rem] text-muted">
          <div className="flex items-center gap-1">
            <Image src="/icons/visibility.svg" alt="조회수" width={18} height={18} />
            <span>{formatCount(post.viewCount)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/icons/favorite.svg" alt="좋아요" width={18} height={18} />
            <span>{formatCount(post.likeCount)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Image src="/icons/chat-bubble.svg" alt="댓글" width={18} height={18} />
            <span>{formatCount(post.commentCount)}</span>
          </div>
        </div>
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
        message="정말로 이 게시물을 삭제하시겠습니까?"
        confirmText="삭제"
        cancelText="취소"
        iconType="warning"
      />
    </div>
  );
}
