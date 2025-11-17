"use client";

import { use } from "react";
import { PostDetailCard } from "@/components/community/PostDetailCard";
import { CommentSection } from "@/components/community/CommentSection";
import {
  usePostDetailQuery,
  useCommentsQuery,
  useTogglePostLikeMutation,
  useCreateCommentMutation,
} from "@/hooks/useCommunityQuery";

/**
 * 게시글 상세 페이지
 * - PostDetailCard와 CommentSection 결합
 */
export default function PostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: postId } = use(params);

  // API 연동
  const { data: post, isLoading: postLoading } = usePostDetailQuery(postId);
  const { data: commentsData, isLoading: commentsLoading } =
    useCommentsQuery(postId);

  const toggleLikeMutation = useTogglePostLikeMutation();
  const createCommentMutation = useCreateCommentMutation();

  // 날짜 포맷팅 함수
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date
      .toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
      .replace(/\. /g, ".")
      .replace(/\.$/, "");
  };

  // 좋아요 토글 핸들러
  const handleLike = () => {
    toggleLikeMutation.mutate(postId);
  };

  // 댓글 작성 핸들러
  const handleSubmitComment = (content: string) => {
    createCommentMutation.mutate(
      { postId, data: { content } },
      {
        onError: (error) => {
          alert(`댓글 작성 실패: ${error.message}`);
        },
      }
    );
  };

  // 댓글을 flat 구조로 변환 (재귀적으로 replies 포함)
  const flattenComments = (
    comments: typeof commentsData.comments
  ): Array<{
    id: number;
    author: string;
    date: string;
    content: string;
  }> => {
    const result: Array<{
      id: number;
      author: string;
      date: string;
      content: string;
    }> = [];
    let idCounter = 1;

    const flatten = (commentList: typeof comments, depth = 0) => {
      for (const comment of commentList) {
        result.push({
          id: idCounter++,
          author: comment.authorNickname || "익명",
          date: formatDate(comment.createdAt),
          content: comment.content,
        });
        if (comment.replies && comment.replies.length > 0) {
          flatten(comment.replies, depth + 1);
        }
      }
    };

    flatten(comments);
    return result;
  };

  // 로딩 상태
  if (postLoading || commentsLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-lg text-muted">로딩 중...</p>
      </div>
    );
  }

  // 데이터 없음
  if (!post) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-lg text-muted">게시글을 찾을 수 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1200px] mx-auto">
      <PostDetailCard
        tag={post.tags?.[0] || "일반"}
        title={post.title}
        author={post.authorNickname || "익명"}
        date={formatDate(post.createdAt)}
        content={post.content}
        views={post.viewCount}
        likes={post.likeCount}
        comments={post.commentCount}
        isLiked={post.isLiked}
        onLike={handleLike}
      />

      <CommentSection
        comments={flattenComments(commentsData?.comments || [])}
        onSubmitComment={handleSubmitComment}
      />
    </div>
  );
}
