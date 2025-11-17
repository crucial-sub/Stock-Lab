"use client";

import { Title } from "@/components/common/Title";
import type { GuestPortfolioCardData } from "@/types";

const rankColors: Record<
  NonNullable<GuestPortfolioCardData["highlight"]>,
  { badge: string; text: string; shadow: string }
> = {
  gold: {
    badge: "bg-[#FFB330]",
    text: "text-[#FFB330]",
    shadow: "shadow-[0_0_8px_0_rgba(255,179,48,0.8)]",
  },
  silver: {
    badge: "bg-[#C8C8C8]",
    text: "text-[#C8C8C8]",
    shadow: "shadow-[0_0_8px_0_rgba(200,200,200,0.8)]",
  },
  bronze: {
    badge: "bg-[#AF7005]",
    text: "text-[#AF7005]",
    shadow: "shadow-[0_0_8px_0_rgba(175,112,5,0.8)]",
  },
};

interface GuestPortfolioCardProps {
  portfolio: GuestPortfolioCardData;
}

function GuestPortfolioCard({ portfolio }: GuestPortfolioCardProps) {
  const highlightStyle = portfolio.highlight
    ? rankColors[portfolio.highlight]
    : null;

  return (
    <article className="rounded-[12px] border-[1/2px] border-[#18223433] bg-[#1822340D] shadow-elev-card">
      <div className="flex h-full flex-col justify-between rounded-[12px] border border-[#18223433] px-5 py-5 text-text-body">
        <div className="flex items-center gap-3">
          <div
            className={[
              "flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full text-[1.25rem] font-semibold text-white",
              highlightStyle?.badge ?? "bg-[#182234]",
              highlightStyle?.shadow ?? "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            #{portfolio.rank}
          </div>
          <div className="flex flex-col">
            <span className="text-[1.25rem] font-semibold text-black">
              {portfolio.name}
            </span>
            <span className="text-sm font-normal text-text-muted">
              by. {portfolio.organization}
            </span>
          </div>
        </div>
        <div className="flex flex-col pt-[1.5rem]">
          <div className="font-semibold text-[#FF7C7C]">
            <span className="text-[1.5rem]">
              +{portfolio.returnRate.toLocaleString()}
            </span>
            <span className="ml-1 text-[0.75rem]">%</span>
          </div>
          <span className="text-[0.75rem] font-normal text-text-muted">
            최근 7일 수익률
          </span>
        </div>
      </div>
    </article>
  );
}

interface GuestPortfolioSectionProps {
  portfolios: GuestPortfolioCardData[];
}

export function GuestPortfolioSection({
  portfolios,
}: GuestPortfolioSectionProps) {
  return (
    <section className="flex w-full flex-col gap-5">
      <div className="flex flex-col gap-1">
        <Title>인기 포트폴리오</Title>
      </div>
      <div className="grid w-full grid-cols-1 gap-5 md:grid-cols-3">
        {portfolios.slice(0, 3).map((item) => (
          <GuestPortfolioCard key={item.rank} portfolio={item} />
        ))}
      </div>
      <div className="grid w-full grid-cols-1 gap-5 md:grid-cols-2">
        {portfolios.slice(3).map((item) => (
          <GuestPortfolioCard key={item.rank} portfolio={item} />
        ))}
      </div>
    </section>
  );
}
