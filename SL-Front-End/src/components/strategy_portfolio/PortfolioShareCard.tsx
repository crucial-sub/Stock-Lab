
export interface PortfolioShareCardProps {
  portfolioName: string;
  author: string;
  description: string;
  returnRate: string;
  stocks: string[];
  onAdd?: () => void;
  className?: string;
}

/**
 * 포트폴리오 공유 카드 컴포넌트
 * - 포트폴리오 상세 정보 표시
 * - 보유 종목 태그 표시
 * - 포트폴리오 추가 기능 제공
 */
export function PortfolioShareCard({
  portfolioName,
  author,
  description,
  returnRate,
  stocks,
  onAdd,
  className = "",
}: PortfolioShareCardProps) {
  return (
    <article
      className={`flex w-[320px] flex-col rounded-lg bg-surface border border-surface shadow-elev-strong px-5 py-5 ${className}`}
    >
      {/* 헤더: 포트폴리오 이름 및 수익률 */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex flex-col gap-1">
          <h3 className="text-xl font-semibold text-body">
            {portfolioName}
          </h3>
          <p className="text-sm text-muted">
            by. {author}
          </p>
        </div>

        <p className="text-xl font-semibold text-price-up">
          {returnRate}{" "}
          <span className="text-base font-normal">%</span>
        </p>
      </div>

      {/* 설명 */}
      <p className="text-sm text-muted mb-6 line-clamp-2">
        {description}
      </p>

      {/* 보유 종목 */}
      <div className="mb-4">
        <p className="text-sm text-muted mb-2">보유 종목</p>
        <div className="flex flex-wrap gap-2">
          {stocks.map((stock, index) => (
            <span
              key={`${stock}-${index}`}
              className="px-3 py-1 text-[0.75rem] text-muted border border-gray-400 rounded"
            >
              {stock}
            </span>
          ))}
        </div>
      </div>

      {/* 포트폴리오 추가하기 버튼 */}
      <button
        onClick={() => {
          console.log("PortfolioShareCard: Add button clicked", { portfolioName, hasOnAdd: !!onAdd });
          if (onAdd) onAdd();
        }}
        disabled={!onAdd}
        className={`w-full px-4 py-2 rounded-[6.25rem] text-white transition-colors ${onAdd
            ? "bg-brand-purple hover:bg-brand-purple-dark"
            : "bg-gray-300 cursor-not-allowed"
          }`}
      >
        {onAdd ? "포트폴리오 추가하기" : "추가 불가 (세션 없음)"}
      </button>
    </article>
  );
}
