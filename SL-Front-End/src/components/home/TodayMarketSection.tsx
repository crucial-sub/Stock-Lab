import Link from "next/link";

import { MarketTickerCard, type MarketTickerCardProps } from "./MarketTickerCard";

interface TodayMarketSectionProps {
  items: MarketTickerCardProps[];
  seeMoreHref?: string;
  className?: string;
}

export function TodayMarketSection({
  items,
  className = "",
}: TodayMarketSectionProps) {
  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-semibold">오늘의 주식 시장</h2>
        <Link
          href={'#'}
          className="text-xl font-light transition"
        >
          더보기
        </Link>
      </div>
      <div className="rounded-lg bg-white px-5 py-[1.125rem] shadow-[0px_0px_8px_rgba(0,0,0,0.08)]">
        <div className="flex flex-nowrap rounded-lg gap-5 overflow-hidden">
          {items.map((item, index) => (
            <div key={`${item.id}-${index}`} className="w-full max-w-[489px] flex-shrink-0">
              <MarketTickerCard {...item} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
