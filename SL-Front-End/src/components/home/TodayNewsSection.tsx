import Link from "next/link";
import { Title } from "@/components/common/Title";
import { NewsCard } from "./NewsCard";
import type { NewsItem } from "@/types/news";

interface TodayNewsSectionProps {
  items: NewsItem[];
  className?: string;
}

export function TodayNewsSection({
  items,
  className = "",
}: TodayNewsSectionProps) {
  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <div className="flex items-center justify-between">
        <Title>오늘의 뉴스</Title>
        <Link href="#" className="text-xl font-light transition">
          더보기
        </Link>
      </div>
      <div className="flex flex-nowrap gap-10 w-full">
        {items.map((item, index) => (
          <div
            key={`${item.title}-${index}`}
            className="basis-[calc((100%-5rem)/3)]"
          >
            <NewsCard {...item} />
          </div>
        ))}
      </div>
    </section>
  );
}
