"use client";

import { memo, useState } from "react";
import { useRouter } from "next/navigation";
import { StockDetailModal } from "@/components/modal/StockDetailModal";
import { Title } from "@/components/common/Title";
import type {
  MarketNews,
  MarketStock,
} from "@/types";

interface MarketInsightSectionProps {
  stocks: MarketStock[];
  news: MarketNews[];
}

const MarketInsightSectionComponent = ({
  stocks,
  news,
}: MarketInsightSectionProps) => {
  const router = useRouter();
  const [selectedStock, setSelectedStock] = useState<{
    name: string;
    code: string;
  } | null>(null);

  const handleStockClick = (stock: MarketStock) => {
    setSelectedStock({ name: stock.name, code: stock.id });
  };

  const handleNewsClick = (item: MarketNews) => {
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
          <div className="flex flex-col">
            {stocks.map((stock) => (
              <div
                key={stock.id}
                role="button"
                tabIndex={0}
                className="flex cursor-pointer items-center justify-between border-t border-[#18223433] px-1 py-3 first:border-t-0 hover:bg-white/5"
                onClick={() => handleStockClick(stock)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    handleStockClick(stock);
                  }
                }}
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
                <span className="inline-flex h-6 items-center justify-center rounded-full bg-brand-purple px-3 text-[0.75rem] font-semibold text-white leading-[1.25rem]">
                  {item.badge}
                </span>
              </div>
            ))}
          </div>
        </article>
      </div>
      <StockDetailModal
        isOpen={!!selectedStock}
        onClose={() => setSelectedStock(null)}
        stockName={selectedStock?.name || ""}
        stockCode={selectedStock?.code || ""}
      />
    </section>
  );
};

/**
 * MarketInsightSection with React.memo
 * - Prevents re-renders when stocks and news arrays haven't changed
 */
export const MarketInsightSection = memo(MarketInsightSectionComponent);
