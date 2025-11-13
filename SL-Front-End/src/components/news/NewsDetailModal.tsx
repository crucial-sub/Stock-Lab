import { Icon } from "@/components/common/Icon";
import type { NewsItem } from "@/types/news";

interface NewsDetailModalProps {
  news: NewsItem;
  onClose: () => void;
}

export function NewsDetailModal({ news, onClose }: NewsDetailModalProps) {
  const displayDate = news.date?.display ?? news.date?.iso ?? "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="relative w-full max-w-3xl rounded-[8px] bg-white p-[1rem] shadow-card max-h-[90vh] overflow-y-auto"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between rounded-t-[8px] border-b border-border-default bg-white px-3 py-2">
          <div className="flex flex-col gap-0.5 text-sm text-text-muted">
            <span>{news.stock_name ?? news.stock_code ?? "종목"}</span>
            <span className="text-text-body font-semibold">{displayDate}</span>
          </div>
          <button
            type="button"
            aria-label="닫기"
            className="h-9 w-9 rounded-full bg-[#FF6464] text-white"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="p-4">
          <h2 className="text-[1.75rem] font-semibold text-text-strong">{news.title}</h2>
          <p className="mt-2 text-sm text-text-muted">{news.source}</p>

          {news.content && (
            <p className="mt-4 text-base leading-relaxed text-text-body whitespace-pre-line">{news.content}</p>
          )}

          {news.link && (
            <a
              href={news.link}
              target="_blank"
              rel="noreferrer"
              className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-brand-primary"
            >
              <Icon src="/icons/link.svg" alt="원문 링크 아이콘" size={20} color="currentColor" />
              원문에서 보기
            </a>
          )}

          {news.original_link && news.original_link !== news.link && (
            <a
              href={news.original_link}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-text-muted"
            >
              <Icon src="/icons/link.svg" alt="원문 링크 아이콘" size={20} color="currentColor" />
              멀티 링크 열기
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
