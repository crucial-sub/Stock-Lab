"use client";

import { Title } from "@/components/common/Title";
import { Icon } from "@/components/common/Icon";
import type { GuestCommunityPost } from "@/types";

const statIcons = [
  { key: "views", icon: "/icons/visibility.svg", label: "조회수" },
  { key: "likes", icon: "/icons/favorite.svg", label: "좋아요" },
  { key: "comments", icon: "/icons/chat-bubble.svg", label: "댓글" },
] as const;

interface GuestCommunityPreviewSectionProps {
  posts: GuestCommunityPost[];
}

export function GuestCommunityPreviewSection({
  posts,
}: GuestCommunityPreviewSectionProps) {
  return (
    <section className="flex w-full flex-col gap-5">
      <div className="flex flex-col gap-1">
        <Title>커뮤니티</Title>
      </div>

      <div className="flex flex-col gap-4">
        {posts.map((post) => (
          <article
            key={post.id}
            className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] shadow-elev-card p-5"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center justify-center rounded-[4px] border-[0.5px] border-[#007DFC] bg-[#EAF5FF] px-3 pt-0.5 text-[0.75rem] font-semibold text-[#2D62AB]">
                {post.tag}
              </span>
              <h3 className="text-[1.25rem] font-semibold text-text-body">
                {post.title}
              </h3>
              <span className="text-sm text-muted font-normal">
                by. {post.author}
              </span>
              <span className="text-sm text-muted font-normal">{post.date}</span>
            </div>

            <p className="pt-[1rem] pb-[0.75rem] line-clamp-1 text-sm text-muted font-normal">
              {post.preview}
            </p>

            <div className="flex items-center gap-4 text-sm text-muted">
              {statIcons.map((stat) => (
                <div
                  key={stat.key}
                  className="flex items-center gap-2 font-semibold"
                >
                  <Icon
                    src={stat.icon}
                    alt={stat.label}
                    size={20}
                    color="#646464"
                  />
                  <span>
                    {
                      post[
                      stat.key as keyof Pick<
                        GuestCommunityPost,
                        "views" | "likes" | "comments"
                      >
                      ]
                    }
                  </span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
