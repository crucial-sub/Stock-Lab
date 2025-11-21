"use client";

import { useRouter } from "next/navigation";
import { CommunityPostCard } from "@/components/community";
import { usePostsQuery } from "@/hooks/useCommunityQuery";

interface DiscussionPreviewSectionProps {
  title?: string;
  limit?: number;
  showMoreHref?: string;
  className?: string;
}

/**
 * 자유게시판 미리보기 섹션
 * - 기본: 최신 자유게시판 글을 limit만큼 노출
 * - showMoreHref 제공 시 더보기 버튼 표시
 */
export function DiscussionPreviewSection({
  title = "자유게시판",
  limit,
  showMoreHref = "/community/posts",
  className = "",
}: DiscussionPreviewSectionProps) {
  const router = useRouter();

  const {
    data: discussionPosts,
    isLoading,
    error,
  } = usePostsQuery({ postType: "DISCUSSION", limit : limit});

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

  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-body">{title}</h2>
        {showMoreHref && (
          <button
            onClick={() => router.push(showMoreHref)}
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </button>
        )}
      </div>

      <div className="flex flex-col gap-5">
        {isLoading ? (
          <div className="text-center py-10">
            <p className="text-muted">로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <p className="text-muted">게시글 데이터를 불러올 수 없습니다.</p>
          </div>
        ) : discussionPosts?.posts && discussionPosts.posts.length > 0 ? (
          discussionPosts.posts.map((post) => (
            <CommunityPostCard
              key={post.postId}
              tag={post.tags?.[0] || "일반"}
              title={post.title}
              author={post.authorNickname || "익명"}
              date={formatDate(post.createdAt)}
              preview={post.contentPreview}
              views={post.viewCount}
              likes={post.likeCount}
              comments={post.commentCount}
              onClick={() => router.push(`/community/${post.postId}`)}
            />
          ))
        ) : (
          <div className="text-center py-10">
            <p className="text-muted">아직 게시글이 없습니다.</p>
          </div>
        )}
      </div>
    </section>
  );
}
