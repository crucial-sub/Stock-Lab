
// 랭킹 뱃지 색상 정의
const rankColors = {
  1: {
    bg: "bg-[#FFB330]",
    border: "border-[#FFAA00]",
    shadow: "shadow-[0px_0px_8px_0px_rgba(255,170,0,0.8)]",
  },
  2: {
    bg: "bg-gray-400",
    border: "border-gray-400",
    shadow: "shadow-[0px_0px_8px_0px_rgba(200,200,200,0.8)]",
  },
  3: {
    bg: "bg-[#AF7005]",
    border: "border-[#AF7005]",
    shadow: "shadow-[0px_0px_8px_0px_rgba(175,112,5,0.8)]",
  },
} as const;

export interface RankingCardProps {
  rank: 1 | 2 | 3;
  portfolioName: string;
  author: string;
  returnRate: string;
  onCopy?: () => void;
  className?: string;
}

/**
 * 수익률 랭킹 카드 컴포넌트
 * - 상위 3개 포트폴리오를 랭킹 뱃지와 함께 표시
 * - 포트폴리오 복제 기능 제공
 */
export function RankingCard({
  rank,
  portfolioName,
  author,
  returnRate,
  onCopy,
  className = "",
}: RankingCardProps) {
  const colors = rankColors[rank];

  return (
    <article
      className={`flex w-[320px] flex-col rounded-lg bg-surface border ${colors.border} px-5 py-5 ${className}`}
    >
      {/* 랭킹 뱃지 및 포트폴리오 정보 */}
      <div className="flex items-start gap-4 mb-7">
        <div
          className={`flex items-center justify-center ${colors.bg} ${colors.shadow} rounded-full w-[52px] h-[52px]`}
        >
          <span className="text-white text-xl font-semibold">
            # {rank}
          </span>
        </div>

        <div className="flex flex-col gap-1">
          <h3 className="text-xl font-semibold text-body">
            {portfolioName}
          </h3>
          <p className="text-sm text-muted">
            by. {author}
          </p>
        </div>
      </div>

      <div className="flex justify-between items-end">

        {/* 수익률 정보 */}
        <div className="flex flex-col gap-1">
          <p className="text-2xl font-semibold text-price-up">
            {returnRate}{" "}
            <span className="text-base font-normal">%</span>
          </p>
          <p className="text-sm text-muted">최근 7일 수익률</p>
        </div>

        {/* 복제하기 버튼 */}
        <button
          onClick={onCopy}
          className="inline-flex justify-center items-center h-7 px-4 py-1 text-white bg-brand-purple rounded-[6.25rem]"
        >
          복제하기
        </button>
      </div>
    </article>
  );
}
