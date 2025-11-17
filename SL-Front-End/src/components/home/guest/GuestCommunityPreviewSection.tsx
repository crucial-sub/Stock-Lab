"use client";

import { Title } from "@/components/common/Title";

const guestPosts = Array.from({ length: 2 }).map((_, index) => ({
  id: index,
  title: "게시물 이름은 이렇게 들어갑니다.",
  preview:
    "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ...으로 처리할 수 있습니다.",
  author: "FMJS",
  date: "2025.12.31 19:00",
  likes: "999+",
  comments: "999+",
}));

export function GuestCommunityPreviewSection() {
  return (
    <section className="flex w-full flex-col gap-5">
      <div className="flex flex-col gap-1">
        <Title>커뮤니티 인기 글</Title>
        <p className="text-base text-text-muted">
          지금 주목받는 게시글을 미리 둘러보세요.
        </p>
      </div>

      <div className="flex flex-col gap-4">
        {guestPosts.map((post) => (
          <article
            key={post.id}
            className="flex flex-col gap-4 rounded-lg border border-[#18223433] bg-white px-6 py-5 shadow-card"
          >
            <div className="flex items-center gap-2 text-sm text-text-muted">
              <span aria-hidden="true" className="text-lg">
                💬
              </span>
              <span>{post.author}</span>
              <span aria-hidden="true">·</span>
              <span>{post.date}</span>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-text-body">
                {post.title}
              </h3>
              <p className="mt-2 line-clamp-2 text-sm text-text-muted">
                {post.preview}
              </p>
            </div>
            <div className="flex gap-4 text-sm text-text-muted">
              <span>👍 {post.likes}</span>
              <span>💬 {post.comments}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
