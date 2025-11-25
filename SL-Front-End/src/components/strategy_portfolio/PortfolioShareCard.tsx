import { useRouter } from "next/navigation";

export interface PortfolioShareCardProps {
  portfolioName: string;
  author: string;
  description: string;
  returnRate: string;
  stocks: string[];
  sessionId: string;
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
  sessionId,
  onAdd,
  className = "",
}: PortfolioShareCardProps) {
  const router = useRouter();

  const sanitizeDescription = (text: string) => {
    if (!text) return "";
    return text
      .replace(/\s*전략(?:입니다)?[.!?]?$/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();
  };

  const formattedDescription = sanitizeDescription(description);

  return (
    <article
      className={`flex w-[320px] flex-col rounded-lg bg-surface border border-surface shadow-elev-strong px-5 py-5 ${className}`}
    >
      {/* 헤더: 포트폴리오 이름 및 수익률 */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex flex-col gap-1">
          <span className="text-[1rem] font-semibold text-body">
            {portfolioName}
          </span>
          <p className="text-[0.75rem] text-muted">
            by. {author}
          </p>
        </div>

        {Number(returnRate) >= 0 ? (
          <p className="text-[1.25rem] font-semibold text-price-up">
            {returnRate}{" "}
            <span className="text-base font-normal">%</span>
          </p>
        ) : (
          <p className="text-[1.25rem] font-semibold text-price-down">
            {returnRate}{" "}
            <span className="text-base font-normal">%</span>
          </p>
        )}
      </div>

      {/* 설정 조건 */}
      <div className="my-4">
        <p className="text-[0.875rem] text-muted mb-1">설정 조건</p>
        <p className="text-[0.75rem] text-muted line-clamp-2">
          {formattedDescription || "조건 정보가 없습니다."}
        </p>
      </div>

      <button
        onClick={() => {
          router.push(`/quant/result/${sessionId}`);
        }}
        disabled={!onAdd}
        className={`w-full px-4 py-2 rounded-[12px] text-white transition-colors ${onAdd
          ? "bg-brand-purple hover:opacity-80"
          : "bg-gray-300 cursor-not-allowed"
          }`}
      >
        더보기
      </button>
    </article>
  );
}
