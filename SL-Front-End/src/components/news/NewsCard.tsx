export interface NewsCardProps {
  id?: string;
  title: string;
  subtitle?: string;
  summary?: string;
  content?: string;
  tickerLabel: string;
  themeName?: string;
  pressName?: string;
  sentiment?: "positive" | "neutral" | "negative";
  publishedAt?: string;
  source?: string;
  link?: string;
  onClick?: () => void;
}

const sentimentColors: Record<
  "positive" | "neutral" | "negative",
  { bg: string; text: string }
> = {
  positive: { bg: "bg-[#DDFFE5]", text: "text-[#00CE00]" },
  neutral: { bg: "bg-[#FFF1D6]", text: "text-[#FFAA00]" },
  negative: { bg: "bg-[#FFE5E5]", text: "text-[#FF6464]" },
};

export function NewsCard({
  title,
  summary,
  tickerLabel,
  themeName,
  pressName,
  sentiment = "neutral",
  publishedAt,
  source,
  link,
  onClick,
}: NewsCardProps) {
  const tone = sentimentColors[sentiment] || sentimentColors.neutral;

  return (
    <article
      className={`group rounded-[12px] border-[0.5px] border-[#18223414] bg-[#1822340D] p-5 transition shadow-elev-card-soft ${
        onClick
          ? "cursor-pointer hover:bg-[#FFFFFF14]"
          : ""
      }`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <span className="text-[1.25rem] font-semibold text-black">{title}</span>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="rounded-[4px] bg-[#969696] px-3 pt-1 pb-0.5 text-[0.75rem] font-normal text-white">
          {tickerLabel}
        </span>
        <span
          className={`rounded-[4px] px-3 pt-1 pb-0.5 text-[0.75rem] font-normal ${tone.bg} ${tone.text}`}
        >
          {sentiment === "positive"
            ? "긍정"
            : sentiment === "neutral"
              ? "중립"
              : "부정"}
        </span>
        <span className="text-[0.75rem] font-normal text-muted">
          {publishedAt}
        </span>
        {link && (
          <a
            className="flex max-w-[180px] items-center text-[0.75rem] font-normal text-muted hover:text-brand"
            href={link}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            <span className="truncate">{link}</span>
          </a>
        )}
      </div>
      <p
        className="mt-2 text-[1rem] font-normal text-muted transition-colors group-hover:text-black"
        style={{
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {summary}
      </p>
    </article>
  );
}
