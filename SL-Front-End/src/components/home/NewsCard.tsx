import type { NewsItem } from "@/types/news";

export type NewsCardProps = NewsItem;

export function NewsCard({
  title,
  stock_code,
  stock_name,
  content,
  source,
  date,
}: NewsCardProps) {
  const contentText = content || "";
  const summary =
    contentText && contentText.length > 180
      ? `${contentText.slice(0, 180)}…`
      : contentText;
  const displayDate = date?.display ?? date?.iso ?? "";
  const stockLabel = stock_name;

  return (
    <article className="flex w-full flex-col rounded-sm bg-white px-5 py-5 shadow-card hover:shadow-lg transition">
      <div className="flex items-center justify-between gap-2 text-xs text-text-muted mb-3">
        <span className="rounded-full border border-border-default px-3 py-1 font-medium text-text-strong">
          {stockLabel}
        </span>
        {stock_code && (
          <span className="rounded-full border border-border-default px-3 py-1 font-medium text-text-muted">
            {stock_code}
          </span>
        )}
      </div>

      <h3 className="text-2xl font-semibold mb-3 leading-tight">{title}</h3>

      <p className="line-clamp-3 text-lg font-light text-text-body mb-4">
        {summary}
      </p>

      <div className="flex items-center justify-between text-sm text-text-muted">
        <span>{displayDate}</span>
        <span>{source}</span>
      </div>
    </article>
  );
}
