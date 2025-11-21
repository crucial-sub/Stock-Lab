"use client";

import { useState } from "react";

export interface FreeBoardComment {
  id: number;
  author: string;
  date: string;
  content: string;
}

interface FreeBoardCommentSectionProps {
  comments: FreeBoardComment[];
  onSubmitComment?: (content: string) => void;
}

const formatCount = (count: number) => (count > 999 ? "999+" : count.toString());

export function FreeBoardCommentSection({
  comments,
  onSubmitComment,
}: FreeBoardCommentSectionProps) {
  const [commentText, setCommentText] = useState("");

  const handleSubmit = () => {
    if (!commentText.trim() || !onSubmitComment) return;
    onSubmitComment(commentText.trim());
    setCommentText("");
  };

  return (
    <div className="w-full rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card-soft">
      <h2 className="text-lg font-semibold text-black">
        댓글 {formatCount(comments.length)}개
      </h2>

      <div className="mt-4 flex flex-col gap-3">
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="댓글을 입력하세요."
          className="min-h-[2rem] rounded-[12px] border-[0.5px] border-[#18223433] bg-[#FFFFFF80] px-4 py-3 text-sm text-black placeholder:text-muted focus:outline-none"
        />
        <button
          type="button"
          onClick={handleSubmit}
          className="self-start rounded-[12px] bg-brand-purple px-5 py-2 text-sm font-semibold text-white transition hover:bg-brand-purple/90"
        >
          댓글 작성
        </button>
      </div>

      <div className="mt-6 space-y-4">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className="rounded-[12px] border border-transparent bg-white/40 px-4 py-3"
          >
            <p className="text-sm font-semibold text-black">
              {comment.author}{" "}
              <span className="ml-2 text-xs font-normal text-[#646464]">
                {comment.date}
              </span>
            </p>
            <p className="mt-1 text-sm text-[#000000]">{comment.content}</p>
          </div>
        ))}
        {!comments.length && (
          <p className="text-center text-sm text-[#646464]">
            아직 댓글이 없습니다.
          </p>
        )}
      </div>
    </div>
  );
}
