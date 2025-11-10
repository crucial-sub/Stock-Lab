export interface NewsCardProps {
  title: string;
  summary: string;
  tickerLabel: string;
  sentiment: "positive" | "neutral" | "negative";
  publishedAt: string;
  source: string;
  link?: string;
  subtitle?: string;
  content?: string;
  themeName?: string;
  pressName?: string;
  onClick?: () => void;
}

const sentimentColors: Record<NewsCardProps["sentiment"], { bg: string; text: string }> = {
  positive: { bg: "bg-[#DDFFE5]", text: "text-[#00CE00]" },
  neutral: { bg: "bg-[#FFF1D6]", text: "text-[#FFAA00]" },
  negative: { bg: "bg-[#FFE5E5]", text: "text-[#FF6464]" },
};

export function NewsCard({
  title,
  summary,
  tickerLabel,
  sentiment,
  publishedAt,
  source,
  link,
  onClick,
}: NewsCardProps) {
  const tone = sentimentColors[sentiment];

  return (
    <article
      className={`rounded-[8px] border border-border-subtle bg-white p-[1.25rem] shadow-card transition ${
        onClick ? "cursor-pointer hover:shadow-card-muted" : ""
      }`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <h2 className="text-[1.5rem] font-semibold text-text-strong">{title}</h2>
      <div className="mt-[0.5rem] flex flex-wrap items-center gap-2 text-[0.8rem]">
        <span className="rounded-[4px] bg-[#E1E1E1] px-[0.5rem] py-[0.25rem] text-[0.8rem] font-normal text-text-strong">{tickerLabel}</span>
        <span className={`rounded-[4px] px-[0.5rem] py-[0.25rem] text-[0.8rem] font-normal ${tone.bg} ${tone.text}`}>
          {sentiment === "positive" ? "긍정" : sentiment === "neutral" ? "중립" : "부정"}
        </span>
        <span className="text-[0.8rem] font-normal text-text-muted">{publishedAt}</span>
        <a
          className="text-[0.8rem] font-normal text-text-muted underline-offset-4 hover:text-text-body"
          href={link ?? "#"}
          target="_blank"
          rel="noreferrer"
        >
          {source}
        </a>
      </div>
      <p className="mt-[0.5rem] text-[1rem] text-text-body">{summary}</p>
    </article>
  );
}
