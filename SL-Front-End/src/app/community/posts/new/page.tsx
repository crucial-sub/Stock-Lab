"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Icon } from "@/components/common/Icon";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
import { FreeBoardPostForm } from "@/components/community";
import { useCreatePostMutation } from "@/hooks/useCommunityQuery";

export default function FreeBoardNewPostPage() {
  const router = useRouter();
  const createPostMutation = useCreatePostMutation();

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

  const handleSubmit = (values: {
    title: string;
    content: string;
    tag?: string;
  }) => {
    createPostMutation.mutate(
      {
        title: values.title,
        content: values.content,
        tags: values.tag ? [values.tag] : undefined,
        postType: "DISCUSSION",
      },
      {
        onSuccess: (post) => {
          router.push(`/community/${post.postId}?source=create`);
        },
        onError: (error) => {
          showAlert("게시 실패", error.message, "error");
        },
      },
    );
  };

  return (
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-[60px]">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-[24px]">
        <button
          type="button"
          onClick={() => router.back()}
          className="self-start inline-flex items-center gap-1 text-[0.875rem] text-[#646464] hover:text-black"
        >
          <Icon
            src="/icons/arrow_left.svg"
            alt="뒤로가기"
            size={20}
            color="#646464"
          />
          돌아가기
        </button>

        <header className="flex items-center justify-between">
          <h1 className="py-[20px] text-[1.5rem] font-semibold text-black">새 글 작성</h1>
        </header>

        <FreeBoardPostForm
          isSubmitting={createPostMutation.isPending}
          onSubmit={handleSubmit}
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
