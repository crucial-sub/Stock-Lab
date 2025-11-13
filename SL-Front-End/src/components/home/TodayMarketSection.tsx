"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Title } from "@/components/common/Title";
import { MarketTickerCard, type MarketTickerCardProps } from "./MarketTickerCard";

interface TodayMarketSectionProps {
  items: MarketTickerCardProps[];
  className?: string;
}

export function TodayMarketSection({
  items,
  className = "",
}: TodayMarketSectionProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pausedRef = useRef(false);
  const [isPaused, setIsPaused] = useState(false);

  // React Compiler가 자동으로 메모이제이션 처리
  const duplicatedItems = items.length ? [...items, ...items] : [];

  useEffect(() => {
    pausedRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !duplicatedItems.length) {
      return;
    }

    let rafId: number;
    let lastTs = performance.now();
    const speed = 100;

    const step = (timestamp: number) => {
      const delta = timestamp - lastTs;
      lastTs = timestamp;

      if (!pausedRef.current) {
        container.scrollLeft += (delta / 1000) * speed;
        const loopWidth = container.scrollWidth / 2;
        if (loopWidth > 0 && container.scrollLeft >= loopWidth) {
          container.scrollLeft -= loopWidth;
        }
      }

      rafId = requestAnimationFrame(step);
    };

    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  }, [duplicatedItems.length]);

  return (
    <section className={`flex flex-col gap-5 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-4">
          <Title>오늘의 주식 시장</Title>
          <span className="text-base font-normal text-text-muted">등락률 상위20 종목</span>
        </div>
        <Link href={'/market-price'} className="text-xl font-light transition">
          더보기
        </Link>
      </div>

      <div className="rounded-lg bg-white px-5 py-[1.125rem] shadow-card-muted">
        <div
          ref={containerRef}
          className="flex flex-nowrap rounded-lg gap-5 overflow-hidden"
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
        >
          <div className="flex gap-5">
            {duplicatedItems.map((item, index) => (
              <div
                key={`${item.id}-${index}`}
                className="w-full max-w-[489px] flex-shrink-0"
              >
                <MarketTickerCard
                  {...item}
                  onDetailClick={item.onDetailClick}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
