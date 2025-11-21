import { Icon } from "@/components/common/Icon";
import type { NewsItem } from "@/types/news";

interface NewsDetailModalProps {
  news: NewsItem;
  onClose: () => void;
}

const sentimentBadge: Record<
  NonNullable<NewsItem["sentiment"]>,
  { label: string; className: string }
> = {
  positive: {
    label: "긍정",
    className: "bg-[#DDFFE5] text-[#00CE00] border-[0.5px] border-[#00CE00]",
  },
  neutral: {
    label: "중립",
    className: "bg-[#FFF1D6] text-[#FFAA00] border-[0.5px] border-[#FFAA00]",
  },
  negative: {
    label: "부정",
    className: "bg-[#FFE5E5] text-[#FF6464] border-[0.5px] border-[#FF6464]",
  },
};

export function NewsDetailModal({ news, onClose }: NewsDetailModalProps) {
  // 상단(링크 위) 요약: llm_summary가 있으면 우선 표시
  const llmSummary = news.llm_summary || (news as any)?.llmSummary || "";
  const subtitle = news.llm_summary;
  // 하단 본문: llm_summary 우선, 없으면 원문/summary
  const bodyContent = llmSummary || news.content || news.summary || "";
  const sentiment = sentimentBadge[news.sentiment] || sentimentBadge.neutral;
  const pressLabel = news.pressName || (news as any)?.media_name || news.source || "";
  const tickerLabel = news.tickerLabel || news.stockCode || "종목 이름";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-0 py-10"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-[800px] rounded-[12px] bg-white shadow-[0_30px_80px_rgba(0,0,0,0.25)] max-h-[90vh] overflow-y-auto"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="relative flex items-center shadow-header bg-white px-[0.5rem] py-[0.75rem] shadow-elev-card-soft">
          <h2
            className="absolute left-1/2 -translate-x-1/2 text-[0.875rem] font-normal text-strong"
          >
            {news.title}
          </h2>
          <button
            type="button"
            aria-label="닫기"
            onClick={onClose}
            className="mr-[0.25rem] ml-auto flex h-3 w-3 rounded-full bg-[#FF6464]"
          >
          </button>
        </div>

        <div className="px-5 py-5">
          <div className="text-[1.5rem] font-semibold text-black">
            {news.title}
          </div>
          {subtitle && (
            <div className="mt-1 text-[1rem] font-normal text-[#4A4A4A]">
              {subtitle}
            </div>
          )}
          
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[1rem] text-[#A0A0A0]">
            {news.publishedAt && <span>{news.publishedAt}</span>}
            {news.link && (
              <a
                href={news.link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex max-w-full items-center gap-1 text-[#A0A0A0] hover:text-brand"
              >
                <Icon
                  src="/icons/link.svg"
                  alt="원문 링크"
                  size={16}
                  color="currentColor"
                />
                <span
                  className="max-w-[280px] truncate"
                  title={news.link}
                >
                  {news.link}
                </span>
              </a>
            )}
          </div>

          <div className="mt-2 flex flex-wrap gap-2 text-sm font-medium">
            <span className="rounded-[4px] bg-[#E1E1E1] px-3 py-1 text-[#000000] border-[0.5px] border-[#000000]">
              {tickerLabel}
            </span>
            {news.themeName && (
              <span className="rounded-[4px] bg-[#F4E2FF] px-3 py-1 text-brand-purple border-[0.5px] border-brand-purple">
                {news.themeName}
              </span>
            )}
            <span
              className={`rounded-[4px] px-3 py-1 ${sentiment.className}`}
            >
              {sentiment.label}
            </span>
            {pressLabel && (
              <span className="rounded-[4px] bg-[#EAF5FF] px-3 py-1 text-[#007DFC] border-[0.5px] border-[#007DFC]">
                {pressLabel}
              </span>
            )}
          </div>

          {bodyContent && (
            <p className="mt-6 text-[1rem] font-normal text-[#000000] whitespace-pre-line">
              {bodyContent}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
