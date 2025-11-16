"use client";

import { useState } from "react";
import { PostDetailCard } from "@/components/community/PostDetailCard";
import { CommentSection, Comment } from "@/components/community/CommentSection";

/**
 * 게시글 상세 페이지
 * - PostDetailCard와 CommentSection 결합
 */
export default function PostDetailPage() {
  const [isLiked, setIsLiked] = useState(false);
  const [likes, setLikes] = useState(24);
  const [comments, setComments] = useState<Comment[]>([
    {
      id: 1,
      author: "투자왕김씨",
      date: "2024.01.15",
      content: "좋은 정보 감사합니다! 저도 비슷한 전략으로 수익을 내고 있어요.",
    },
    {
      id: 2,
      author: "주식초보",
      date: "2024.01.15",
      content: "초보자인데 이해하기 쉽게 설명해주셔서 감사합니다.",
    },
    {
      id: 3,
      author: "매매고수",
      date: "2024.01.15",
      content: "시장 상황에 따라 조금씩 조정이 필요할 것 같아요.",
    },
  ]);

  const handleLike = () => {
    if (isLiked) {
      setLikes(likes - 1);
    } else {
      setLikes(likes + 1);
    }
    setIsLiked(!isLiked);
  };

  const handleSubmitComment = (content: string) => {
    const newComment: Comment = {
      id: comments.length + 1,
      author: "현재사용자",
      date: new Date().toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).replace(/\. /g, ".").replace(/\.$/, ""),
      content,
    };
    setComments([...comments, newComment]);
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1200px] mx-auto">
      <PostDetailCard
        tag="질문"
        title="초보자를 위한 주식 투자 전략"
        author="주식러버"
        date="2024.01.15"
        content="안녕하세요, 주식 투자를 시작한 지 얼마 안 된 초보입니다. 여러분들의 투자 전략이 궁금해서 글을 올립니다. 저는 주로 장기 투자를 선호하는데, 단기 매매도 병행하면 좋을까요? 그리고 포트폴리오 구성은 어떻게 하시나요?"
        views={156}
        likes={likes}
        comments={comments.length}
        isLiked={isLiked}
        onLike={handleLike}
      />

      <CommentSection
        comments={comments}
        onSubmitComment={handleSubmitComment}
      />
    </div>
  );
}
