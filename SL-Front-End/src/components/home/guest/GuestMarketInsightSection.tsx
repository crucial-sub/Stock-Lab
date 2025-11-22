"use client";

import { Title } from "@/components/common/Title";
import type {
  GuestMarketIndex,
  GuestMarketNews,
  GuestMarketStock,
} from "@/types";

interface GuestMarketInsightSectionProps {
  indexes: GuestMarketIndex[];
  stocks: GuestMarketStock[];
  news: GuestMarketNews[];
}

export function GuestMarketInsightSection({
  indexes,
  stocks,
  news,
}: GuestMarketInsightSectionProps) {
  return (
    <section className="flex w-full flex-col gap-5">
      <div className="flex flex-col gap-1">
        <div className="flex items-baseline gap-3">
          <span className="text-[1.5rem] font-semibold">주요 시황</span>
          <span className="text-[0.75rem] font-normal text-muted">
            {new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10)}, 체결량 순
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <article className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] shadow-elev-card p-5">
          <div className="grid md:grid-cols-2">
            {indexes.map((item) => (
              <div key={item.label} className="flex flex-col gap-4">
                <span className="text-[1rem] text-text-muted">{item.label}</span>
                <div className="flex items-end gap-3">
                  <span className="text-[1.25rem] font-semibold text-text-body">
                    {item.value}
                  </span>
                  <span className="text-[1rem] font-semibold text-price-up">
                    {item.change}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col">
            {stocks.map((stock) => (
              <div
                key={stock.id}
                className="flex items-center justify-between border-t border-[#18223433] px-1 py-3 first:border-t-0"
              >
                <div className="flex items-center gap-3">
                  <span className="text-[1rem] font-semibold text-text-body">
                    {stock.name}
                  </span>
                  <span className="rounded-full bg-brand-purple px-3 pt-0.5 text-[0.75rem] font-semibold text-white">
                    {stock.tag}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-[1rem] font-normal text-text-muted">
                  <span className="text-price-up">{stock.change}</span>
                  <span>{stock.price}</span>
                  <span>{stock.volume}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] shadow-elev-card p-5">
          <div className="flex flex-col">
            {news.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between border-t border-[#18223433] py-3 first:border-t-0"
              >
                <span className="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-base font-normal text-text-body">
                  {item.title}
                </span>
                <span className="rounded-full bg-brand-purple px-3 pt-0.5 text-[0.75rem] font-semibold text-white">
                  {item.badge}
                </span>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
