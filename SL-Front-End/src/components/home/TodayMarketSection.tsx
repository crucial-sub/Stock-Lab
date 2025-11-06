"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

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

  const duplicatedItems = useMemo(
    () => (items.length ? [...items, ...items] : []),
    [items],
  );

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
        <h2 className="text-3xl font-semibold">오늘의 주식 시장</h2>
        <Link href={'/market'} className="text-xl font-light transition">
          더보기
        </Link>
      </div>

      <div className="rounded-lg bg-white px-5 py-[1.125rem] shadow-[0px_0px_8px_rgba(0,0,0,0.08)]">
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
                <MarketTickerCard {...item} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
