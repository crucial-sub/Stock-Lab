import { Icon } from "@/components/common/Icon";
import { NewsCardProps } from "./NewsCard";

interface NewsDetailModalProps {
  news: NewsCardProps;
  onClose: () => void;
}

export function NewsDetailModal({ news, onClose }: NewsDetailModalProps) {
  const sentimentLabel = news.sentiment === "positive" ? "긍정" : news.sentiment === "neutral" ? "중립" : "부정";
  const sentimentClasses: Record<NewsCardProps["sentiment"], string> = {
    positive: "bg-[#DDFFE5] text-[#00CE00] border border-[#00CE00]",
    neutral: "bg-[#FFF1D6] text-[#FFAA00] border border-[#FFAA00]",
    negative: "bg-[#FFE5E5] text-[#FF6464] border border-[#FF6464]",
  };

  const tagItems = [
    { label: news.tickerLabel, className: "bg-[#E1E1E1] text-text-strong border border-text-strong" },
    news.themeName ? { label: news.themeName, className: "bg-[#F4E2FF] text-[#8A3FFC] border border-[#8A3FFC]" } : null,
    { label: sentimentLabel, className: sentimentClasses[news.sentiment] },
    news.pressName ? { label: news.pressName, className: "bg-[#EAF5FF] text-[#007DFC] border border-[#007DFC]" } : null,
  ].filter(Boolean) as { label: string; className: string }[];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl rounded-[8px] bg-white p-[0.75rem] shadow-card max-h-[90vh] overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center bg-white pb-2 shadow-header">
          <p className="absolute left-1/2 -translate-x-1/2 text-sm text-text-muted">
            {news.tickerLabel} : {news.title}
          </p>
          <button
            type="button"
            aria-label="닫기"
            className="ml-auto flex h-3 w-3 items-center justify-center rounded-full bg-[#FF6464]"
            onClick={onClose}
          />
        </div>

        <div className="m-3 pt-[1rem] flex flex-col gap-4">
          <div>
            <h2 className="text-[1.5rem] font-semibold text-text-strong">{news.title}</h2>
            {news.subtitle && (
              <p className="mt-[0.25rem] text-[1.25rem] text-text-body">{news.subtitle}</p>
            )}
          </div>
          <div className="mt-[-0.5rem] flex flex-wrap items-center gap-2 text-sm text-text-muted">
            <span>{news.publishedAt}</span>
            {news.link && (
              <a
                href={news.link}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-text-muted"
              >
                <Icon src="/icons/link.svg" alt="링크" size={20} color="var(--color-text-muted)" />
                {news.source}
              </a>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            {tagItems.map((tag) => (
              <span key={tag.label} className={`rounded-[4px] px-[0.5rem] py-[0.25rem] text-[0.8rem] font-normal ${tag.className}`}>
                {tag.label}
              </span>
            ))}
          </div>

          <p className="leading-relaxed text-text-body">
            {news.content ?? news.summary}
          </p>
        </div>
      </div>
    </div>
  );
}
