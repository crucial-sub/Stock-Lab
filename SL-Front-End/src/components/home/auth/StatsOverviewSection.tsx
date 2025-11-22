"use client";

import type { HomeStatCardData } from "@/types";

interface StatsOverviewSectionProps {
  stats: HomeStatCardData[];
}

export function StatsOverviewSection({ stats }: StatsOverviewSectionProps) {
  const splitValue = (value: string) => {
    const match = value.match(/^([+-]?[0-9,.\s]+)(.*)$/);
    if (!match) {
      return { number: value, suffix: "" };
    }
    return { number: match[1].trim(), suffix: match[2].trim() };
  };

  const extractNumeric = (value: string): number => {
    const match = value.match(/[+-]?\d[\d,]*(?:\.\d+)?/);
    if (!match) return 0;

    const parsed = Number.parseFloat(match[0].replace(/,/g, ""));
    return Number.isNaN(parsed) ? 0 : parsed;
  };

  const getValueColor = (statId: string, value: string): string => {
    if (statId === "return") {
      const numericValue = extractNumeric(value);
      if (Math.abs(numericValue) < 1e-8) {
        return "text-text-body";
      }
      return numericValue > 0 ? "text-price-up" : "text-price-down";
    }
    return "text-text-body";
  };

  const getChangeColor = (statId: string, changeText: string): string => {
    if (statId === "asset") {
      const numericValue = extractNumeric(changeText);
      if (Math.abs(numericValue) < 1e-8) {
        return "text-text-body";
      }
      return numericValue > 0 ? "text-price-up" : "text-price-down";
    }

    if (statId === "return" || statId === "active") {
      return "text-text-body";
    }

    return "text-text-body";
  };

  return (
    <section className="flex w-full flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => {
          const { number, suffix } = splitValue(stat.value);
          const valueColorClass = getValueColor(stat.id, stat.value);
          const changeColorClass = getChangeColor(stat.id, stat.change);

          return (
            <article
              key={stat.id}
              className="rounded-[12px] border border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card"
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
              <div
                className={`text-[0.875rem] font-normal ${changeColorClass}`}
              >
                {stat.change}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
