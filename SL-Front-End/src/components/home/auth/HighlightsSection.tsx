"use client";

import { Icon } from "@/components/common/Icon";
import { Title } from "@/components/common/Title";
import type {
  HomeCommunityHighlight,
  HomePortfolioHighlight,
} from "@/types";

interface HighlightsSectionProps {
  portfolios: HomePortfolioHighlight[];
  posts: HomeCommunityHighlight[];
}

export function HighlightsSection({ portfolios, posts }: HighlightsSectionProps) {
  const pairs = portfolios.map((portfolio, index) => ({
    portfolio,
    post: posts[index],
  }));

  return (
    <section className="flex w-full flex-col gap-5">
      <Title>지금 뜨는 포트폴리오 & 커뮤니티</Title>
      <div className="flex flex-col gap-5">
        {pairs.map(({ portfolio, post }) => (
          <div key={portfolio.rank} className="grid gap-5 md:grid-cols-2">
            <article className="flex items-center justify-between rounded-[12px] border-[0.5px] border-[#18223433] p-5 bg-[#1822340D] shadow-elev-card">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-[12px] bg-[#182234] text-[1.25rem] font-semibold text-white">
                  #{portfolio.rank}
                </div>
                <div className="flex flex-col">
                  <span className="text-[1.25rem] font-semibold text-text-body">
                    {portfolio.name}
                  </span>
                  <span className="text-[0.875rem] font-normal text-muted">by. {portfolio.id}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[1.25rem] font-semibold text-[#FF7C7C]">
                  +{portfolio.returnRate.toLocaleString()} %
                </div>
                <p className="text-[0.875rem] font-normal text-muted">최근 7일 수익률</p>
              </div>
            </article>
            {post ? (
              <article className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-6 items-center justify-center rounded-[4px] border border-[#007DFC] bg-[#E8F1FF] px-2 pt-1 text-[0.75rem] font-semibold text-[#007DFC]">
                    {post.tag}
                  </span>
                  <span className="text-[1rem] font-semibold text-text-body">
                    {post.title}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-3 text-sm text-muted">
                  <span className="flex items-center gap-1">
                    <Icon src="/icons/visibility.svg" size={20} color="#646464" />
                    {post.views}
                  </span>
                  <span className="flex items-center gap-1">
                    <Icon src="/icons/favorite.svg" size={20} color="#646464" />
                    {post.likes}
                  </span>
                  <span className="flex items-center gap-1">
                    <Icon
                      src="/icons/chat-bubble.svg"
                      size={20}
                      color="#646464"
                    />
                    {post.comments}
                  </span>
                </div>
              </article>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
