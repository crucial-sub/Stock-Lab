import Link from "next/link";
import { NewsCard, type NewsItem } from "./NewsCard";

interface TodayNewsSectionProps {
  items: NewsItem[];
  className?: string;
}

export function TodayNewsSection({ items, className = "" }: TodayNewsSectionProps) {
  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-semibold">오늘의 뉴스</h2>
        <Link
          href='#'
          className="text-xl font-light transition"
        >
          더보기
        </Link>
      </div>
      <div className="flex flex-nowrap gap-10 w-full">
        {items.map((item, index) => (
          <div key={`${item.title}-${index}`} className="basis-[calc((100%-5rem)/3)]">
            <NewsCard {...item} />
          </div>
        ))}
      </div>
    </section>
  );
}
