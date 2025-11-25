"use client";

import { useRouter } from "next/navigation";
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
  const router = useRouter();

  const handleStockClick = (stock: GuestMarketStock) => {
    const params = new URLSearchParams({
      tab: "volume",
      stockCode: stock.id,
      stockName: stock.name,
    });
    router.push(`/market-price?${params.toString()}`);
  };

  const handleNewsClick = (item: GuestMarketNews) => {
    router.push(`/news?newsId=${item.id}`);
  };

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
                role="button"
                tabIndex={0}
                className="grid cursor-pointer grid-cols-[minmax(0,1.6fr)_0.6fr_0.95fr_1fr] items-center gap-2 border-t border-[#18223433] px-1 py-3 first:border-t-0 hover:bg-white/5"
                onClick={() => handleStockClick(stock)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleStockClick(stock);
                  }
                }}
              >
                <div className="min-w-0">
                  <span className="whitespace-normal break-keep text-[1rem] font-semibold text-text-body">
                    {stock.name}
                  </span>
                </div>
                <span className={parseFloat(stock.change) >= 0 ? "text-price-up" : "text-price-down"}>
                  {stock.change}
                </span>
                <span className="text-right text-[0.95rem] font-normal text-text-muted">
                  {stock.price}
                </span>
                <span className="text-right text-[0.95rem] font-normal text-text-muted">
                  {stock.volume}
                </span>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] shadow-elev-card p-5">
          <div className="flex flex-col">
            {news.map((item) => (
              <div
                key={item.id}
                role="button"
                tabIndex={0}
                className="flex cursor-pointer items-center justify-between border-t border-[#18223433] py-3 first:border-t-0 hover:bg-white/5"
                onClick={() => handleNewsClick(item)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleNewsClick(item);
                  }
                }}
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
