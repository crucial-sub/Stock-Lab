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

const sentimentColors: Record<"positive" | "neutral" | "negative", { bg: string; text: string }> = {
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
  const tone = sentimentColors[sentiment] || sentimentColors["neutral"];

  return (
    <article
      className={`rounded-lg border-[0.5px] border-[rgba(24,34,52,0.2)] bg-[rgba(24,34,52,0.05)] p-5 transition ${
        onClick ? "cursor-pointer hover:shadow-[0px_0px_9px_0px_rgba(0,0,0,0.1)]" : ""
      }`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <h2 className="text-[1.5rem] font-semibold text-black">{title}</h2>
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <span className="rounded-[4px] bg-[#E1E1E1] px-2 py-1 text-[0.8rem] font-normal text-black">{tickerLabel}</span>
        <span className={`rounded-[4px] px-2 py-1 text-[0.8rem] font-normal ${tone.bg} ${tone.text}`}>
          {sentiment === "positive" ? "긍정" : sentiment === "neutral" ? "중립" : "부정"}
        </span>
        <span className="text-[0.8rem] font-normal text-gray-600">{publishedAt}</span>
        {link && (
          <a
            className="flex max-w-[200px] items-center gap-1 text-[0.8rem] font-normal text-gray-600 hover:text-black"
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
        className="mt-2 text-[1.125rem] font-light text-black leading-relaxed"
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