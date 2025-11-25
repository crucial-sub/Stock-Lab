"use client";

/**
 * 포트폴리오 대시보드
 *
 * @description 사용자의 전체 자산 현황을 보여주는 대시보드 컴포넌트
 * 총 모의 자산, 이번주 수익, 활성 포트폴리오 수를 표시합니다.
 */

interface PortfolioDashboardProps {
  /** 총 모의 자산 (원) */
  totalAssets: number;
  /** 평가손익 (원) */
  totalProfit: number;
  /** 수익률 (%) */
  totalReturn: number;
  /** 평가금액 (원) */
  evaluationAmount: number;
  /** 활성 포트폴리오 개수 */
  activePortfolioCount: number;
}

export function PortfolioDashboard({
  totalAssets,
  totalProfit,
  totalReturn,
  evaluationAmount,
  activePortfolioCount,
}: PortfolioDashboardProps) {
  // 숫자를 천 단위 콤마로 포맷팅 (원화는 정수로 표시)
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("ko-KR").format(Math.round(num));
  };

  // 수익률 포맷팅 (+/- 부호 포함)
  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? "+" : "";
    return `${sign}${percent.toFixed(2)}%`;
  };

  // 수익률이 양수인지 음수인지 판단
  const isPositive = (value: number) => value >= 0;

  return (
    <section className="mb-[60px]" aria-label="포트폴리오 대시보드">
      {/* 제목 */}
      <h1 className="text-[2rem] font-bold text-black mb-[40px]">
        포트폴리오 대시보드
      </h1>

      {/* 대시보드 카드 그리드 */}
      <div className="grid grid-cols-3 gap-5">
        {/* 총 자산 */}
        <div className="bg-[#AC64FF0D] border border-[#AC64FF33] rounded-lg px-5 py-5 h-[9.25rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[1.25rem] font-semibold text-black">
              총 자산
            </h2>
          </div>
          <div>
            <p className="text-[1.5rem] font-semibold text-black">
              {formatNumber(totalAssets)}
              <span className="text-[1rem] text-normal ml-1">원</span>
            </p>
            <p
              className={[
                "",
                isPositive(totalProfit)
                  ? "text-red-500"
                  : "text-blue-500",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              평가손익 {isPositive(totalProfit) ? "+" : ""}
              {formatNumber(totalProfit)}원
            </p>
          </div>
        </div>

        {/* 수익률 */}
        <div className="bg-[#AC64FF0D] border border-[#AC64FF33] rounded-lg px-5 py-5 h-[9.25rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[1.25rem] font-semibold text-black">
              수익률
            </h2>
          </div>
          <p
            className={[
              "text-[1.5rem] font-semibold",
              totalReturn > 0
                ? "text-red-500"
                : totalReturn < 0
                  ? "text-blue-500"
                  : "text-black",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {formatPercent(totalReturn)}
          </p>
        </div>

        {/* 활성 포트폴리오 */}
        <div className="bg-[#AC64FF0D] border border-[#AC64FF33] rounded-lg px-5 py-5 h-[9.25rem]">
          <h2 className="text-[1.25rem] font-semibold text-black mb-6">
            활성 포트폴리오
          </h2>
          <p className="text-[1.5rem] font-semibold text-black">
            {activePortfolioCount}
            <span className="text-[1rem] text-normal ml-1">개</span>
          </p>
          <p className="">현재 활성 중인 포트폴리오 개수</p>
        </div>
      </div>
    </section>
  );
}
