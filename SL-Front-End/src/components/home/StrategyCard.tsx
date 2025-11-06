import { Button } from "../common";

interface StrategyMetric {
  label: string;
  value: string;
  tone?: "default" | "positive" | "muted";
}

export interface StrategyCardProps {
  title: string;
  author: string;
  tags: string[];
  description: string;
  metrics: StrategyMetric[];
  ctaLabel: string;
  className?: string;
}

const toneClass: Record<NonNullable<StrategyMetric["tone"]>, string> = {
  default: "text-[#505050]",
  positive: "text-[#FF6464]",
  muted: "text-[#4B5563]",
};

export function StrategyCard({
  title,
  author,
  tags,
  description,
  metrics,
  ctaLabel,
  className = "",
}: StrategyCardProps) {
  return (
    <article
      className={`flex w-full flex-col rounded-sm bg-white px-6 py-6 shadow-[0px_0px_8px_rgba(0,0,0,0.1)] ${className}`}
    >
      <header className="flex flex-col gap-1 mb-2">
        <div className="flex items-end gap-1">
          <h3 className="text-2xl font-semibold">
            {title}
          </h3>
          <span className="whitespace-nowrap text-xs font-extralight font-sans">
            made by. {author}
          </span>
        </div>
        <div className="flex flex-wrap gap-1">
          {tags.map((tag, index) => (
            <div key={`${tag}-${index}`} className="px-1 py-0.5 rounded-[2px] inline-flex bg-[#FFEFEF] justify-center items-center gap-1 overflow-hidden">
              <span
                className="text-center justify-center text-sm font-normal font-sans"
              >
                {tag}
              </span>
            </div>
          ))}
        </div>
      </header>

      <p className="line-clamp-2 w-full justify-start text-base font-extralight font-sans mb-6">
        {description}
      </p>

      <div className="flex justify-between mb-7">
        {metrics.map((metric) => (
          <div key={`${metric.label}-${metric.value}`} className="flex flex-col gap-1">
            <span className="text-sm font-extralight font-sans">{metric.label}</span>
            <span
              className={`text-xl font-semibold font-sans ${toneClass[metric.tone ?? "positive"]}`}
            >
              {metric.value}
            </span>
          </div>
        ))}
      </div>

      <Button variant="tertiary" className="w-full text-xl font-semibold">
        {ctaLabel}
      </Button>
    </article>
  );
}
