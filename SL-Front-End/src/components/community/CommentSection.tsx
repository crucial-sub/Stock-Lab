"use client";

import { useState } from "react";
import { CommentItem } from "./CommentItem";

export interface Comment {
  id: number;
  author: string;
  date: string;
  content: string;
}

export interface CommentSectionProps {
  comments: Comment[];
  onSubmitComment?: (content: string) => void;
  className?: string;
}

/**
 * 댓글 섹션 컴포넌트
 * - 댓글 개수, 입력창, 댓글 목록 표시
 */
export function CommentSection({
  comments,
  onSubmitComment,
  className = "",
}: CommentSectionProps) {
  const [commentText, setCommentText] = useState("");

  // 댓글 개수 포맷팅 (999+ 처리)
  const formatCount = (count: number): string => {
    return count > 999 ? "999+" : count.toString();
  };

  const handleSubmit = () => {
    if (commentText.trim() && onSubmitComment) {
      onSubmitComment(commentText);
      setCommentText("");
    }
  };

  return (
    <div className={`flex flex-col w-full ${className}`}>
      {/* 댓글 개수 헤더 */}
      <h2 className="text-2xl font-semibold text-body mb-5">
        댓글 {formatCount(comments.length)}개
      </h2>

      {/* 댓글 입력 영역 */}
      <div className="flex flex-col gap-3 mb-6">
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="댓글을 입력하세요"
          className="w-full min-h-[2rem] px-4 py-3 text-base text-body bg-surface border border-surface rounded-[12px] resize-none focus:outline-none focus:border-brand-purple"
        />
        <button
          onClick={handleSubmit}
          className="self-end px-6 py-2 text-base font-semibold text-white bg-brand-purple rounded-[12px] hover:opacity-80 transition"
        >
          댓글 작성
        </button>
      </div>

      {/* 댓글 목록 */}
      <div className="flex flex-col divide-y divide-surface">
        {comments.map((comment) => (
          <CommentItem
            key={comment.id}
            author={comment.author}
            date={comment.date}
            content={comment.content}
          />
        ))}
      </div>
    </div>
  );
}
