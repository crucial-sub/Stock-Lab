"use client";

import type { HomeStatCardData } from "@/types";

interface StatsOverviewSectionProps {
  stats: HomeStatCardData[];
}

export function StatsOverviewSection({ stats }: StatsOverviewSectionProps) {
  const splitValue = (value: string) => {
    const match = value.match(/^([+\-]?[0-9,.\s]+)(.*)$/);
    if (!match) {
      return { number: value, suffix: "" };
    }
    return { number: match[1].trim(), suffix: match[2].trim() };
  };

  // 수익률 값에서 색상 결정
  const getReturnColor = (value: string): string => {
    if (value.startsWith('+')) {
      return 'text-price-up'; // 빨간색
    } else if (value.startsWith('-')) {
      return 'text-blue-500'; // 파란색
    }
    return 'text-text-body'; // 검은색 (0.00%)
  };

  return (
    <section className="flex w-full flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => {
          const { number, suffix } = splitValue(stat.value);
          const isReturn = stat.id === 'return'; // 수익률 카드인지 확인
          const valueColorClass = isReturn ? getReturnColor(stat.value) : 'text-text-body';

          return (
            <article
              key={stat.id}
              className="rounded-[12px] border border-[#18223433] bg-[#18223405] p-5 shadow-elev-card"
            >
              <div className="flex items-center justify-between text-[1.25rem] font-semibold text-text-muted">
                <span>{stat.title}</span>
                {stat.badge ? (
                  <span className="rounded-full bg-[#FF646414] px-3 py-1 text-xs font-semibold text-[#FF6464]">
                    {stat.badge}
                  </span>
                ) : null}
              </div>
              <div className={`mt-2 font-semibold ${valueColorClass}`}>
                <span className="text-[1.5rem]">{number}</span>
                {suffix ? (
                  <span className="ml-1 text-[1rem]">{suffix}</span>
                ) : null}
              </div>
              <div className="text-[0.875rem] font-normal text-price-up">
                {stat.change}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
