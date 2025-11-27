"use client";

import { use, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Icon } from "@/components/common/Icon";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
import {
  FreeBoardCommentSection,
  FreeBoardDetailCard,
} from "@/components/community";
import {
  useCommentsQuery,
  useCreateCommentMutation,
  usePostDetailQuery,
  useTogglePostLikeMutation,
} from "@/hooks/useCommunityQuery";

export default function CommunityPostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: postId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const source = searchParams.get("source");

  const handleBack = () => {
    if (source === "create") {
      router.push("/community/posts");
    } else {
      router.back();
    }
    router.refresh();
  };

  const { data: post, isLoading: postLoading } = usePostDetailQuery(postId);
  const { data: commentsData, isLoading: commentsLoading } =
    useCommentsQuery(postId);

  const toggleLikeMutation = useTogglePostLikeMutation();
  const createCommentMutation = useCreateCommentMutation();

  // 알림 모달 상태
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    iconType: "info" | "warning" | "error" | "success" | "question";
  }>({ isOpen: false, title: "", message: "", iconType: "info" });

  // 알림 모달 표시 헬퍼
  const showAlert = (
    title: string,
    message: string,
    iconType: "info" | "warning" | "error" | "success" | "question" = "info"
  ) => {
    setAlertModal({ isOpen: true, title, message, iconType });
  };

  const formattedComments = useMemo(() => {
    if (!commentsData?.comments) return [];

    const flatten = (items: typeof commentsData.comments, acc: any[] = []) => {
      items.forEach((item, index) => {
        const commentKey = item.commentId || `temp-${acc.length + index}`;
        acc.push({
          id: commentKey,
          author: item.authorNickname || "익명",
          date: new Date(item.createdAt).toLocaleString("ko-KR", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
          }),
          content: item.content,
        });
        if (item.replies?.length) {
          flatten(item.replies, acc);
        }
      });
      return acc;
    };

    return flatten(commentsData.comments, []);
  }, [commentsData]);

  if (postLoading || commentsLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-[#646464]">
        로딩 중...
      </div>
    );
  }

  if (!post) {
    return (
      <div className="flex min-h-screen items-center justify-center text-[#646464]">
        게시글을 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-[60px]">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-[24px]">
        <button
          type="button"
          onClick={handleBack}
          className="self-start inline-flex items-center gap-1 text-[0.875rem] text-[#646464]"
        >
          <Icon
            src="/icons/arrow_left.svg"
            alt="뒤로가기"
            size={20}
            color="#646464"
          />
          돌아가기
        </button>

        <FreeBoardDetailCard
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
          content={post.content}
          views={post.viewCount}
          likes={post.likeCount}
          comments={post.commentCount}
          isLiked={post.isLiked}
          onLike={() => toggleLikeMutation.mutate(postId)}
        />

        <FreeBoardCommentSection
          comments={formattedComments}
          onSubmitComment={(content) =>
            createCommentMutation.mutate(
              { postId, data: { content } },
              {
                onError: (error) => {
                  showAlert("댓글 작성 실패", error.message, "error");
                },
              },
            )
          }
        />
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
    </section>
  );
}
