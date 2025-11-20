"use client";

import { useRouter } from "next/navigation";

import { FreeBoardPostForm } from "@/components/community";
import { useCreatePostMutation } from "@/hooks/useCommunityQuery";

export default function FreeBoardNewPostPage() {
  const router = useRouter();
  const createPostMutation = useCreatePostMutation();

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
          router.push(`/community/${post.postId}`);
        },
        onError: (error) => {
          alert(`게시 실패: ${error.message}`);
        },
      },
    );
  };

  return (
    <section className="px-4 sm:px-8 lg:px-12 xl:px-16 2xl:px-20 py-10">
      <div className="mx-auto flex w-full max-w-[1000px] flex-col gap-6">
        <button
          type="button"
          onClick={() => router.back()}
          className="text-sm text-[#646464] hover:text-black"
        >
          ← 돌아가기
        </button>

        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold text-black">새 글 작성</h1>
        </header>

        <FreeBoardPostForm
          isSubmitting={createPostMutation.isPending}
          onSubmit={handleSubmit}
        />
      </div>
    </section>
  );
}
