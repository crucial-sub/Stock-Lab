export interface NewsItem {
  id: string;
  title: string;
  publishedAt: string;
  source: string;
  summary: string;
  nameTag: string;
  SentimentTag: string;
}

export function NewsCard({
  title,
  publishedAt,
  source,
  summary,
  nameTag,
  SentimentTag
}: NewsItem) {
  return (
    <article className="flex w-full flex-col rounded-sm bg-white px-5 py-5 shadow-[0px_0px_8px_rgba(0,0,0,0.1)]">
      <h3 className="text-2xl font-semibold mb-1">{title}</h3>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <div className="px-3 py-1 rounded-xs inline-flex bg-[#E1E1E1] justify-center items-center gap-1 overflow-hidden">
          <span
            className="text-center justify-center text-xs font-medium font-sans"
          >
            {nameTag}
          </span>
        </div>
        <div className="px-3 py-1 rounded-xs inline-flex bg-[#DDFFE5] justify-center items-center gap-1 overflow-hidden">
          <span
            className="text-center justify-center text-[#00CD00] text-xs font-medium font-sans"
          >
            {SentimentTag}
          </span>
        </div>
        <span className="text-[#A0A0A0] text-sm font-extralight ">{publishedAt}</span>
        <span className="text-[#A0A0A0] text-sm font-extralight">{source}</span>
      </div>
      <p className="line-clamp-3 w-full text-lg font-light">{summary}</p>
    </article>
  );
}
