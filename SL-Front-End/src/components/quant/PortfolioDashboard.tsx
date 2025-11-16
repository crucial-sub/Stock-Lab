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
  /** 총 자산 수익률 (%) */
  totalAssetsChange: number;
  /** 이번주 수익 (원) */
  weeklyProfit: number;
  /** 이번주 수익률 (%) */
  weeklyProfitChange: number;
  /** 활성 포트폴리오 개수 */
  activePortfolioCount: number;
}

export function PortfolioDashboard({
  totalAssets,
  totalAssetsChange,
  weeklyProfit,
  weeklyProfitChange,
  activePortfolioCount,
}: PortfolioDashboardProps) {
  // 숫자를 천 단위 콤마로 포맷팅
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("ko-KR").format(num);
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
        {/* 총 모의 자산 */}
        <div className="bg-[#AC64FF0D] border border-[#AC64FF33] rounded-lg px-5 py-5 h-[9.25rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[1.25rem] font-semibold text-black">
              총 모의 자산
            </h2>
            <span
              className={[
                "px-3 py-1 rounded-[100px] bg-[#FF646433] font-semibold text-[0.75rem]",
                isPositive(totalAssetsChange)
                  ? "bg-red-50 text-red-500"
                  : "bg-blue-50 text-blue-500",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {formatPercent(totalAssetsChange)}
            </span>
          </div>
          <div>
            <p className="text-[1.5rem] font-semibold text-black">
              {formatNumber(totalAssets)}
              <span className="text-[1rem] text-normal ml-1">원</span>
            </p>
            <p
              className={[
                "",
                isPositive(totalAssetsChange)
                  ? "text-red-500"
                  : "text-blue-500",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {isPositive(totalAssetsChange) ? "+" : ""}
              {formatNumber(
                Math.floor(totalAssets * (totalAssetsChange / 100)),
              )}
              원
            </p>
          </div>
        </div>

        {/* 이번주 수익 */}
        <div className="bg-[#AC64FF0D] border border-[#AC64FF33] rounded-lg px-5 py-5 h-[9.25rem]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-[1.25rem] font-semibold text-black">
              이번주 수익
            </h2>
            <span
              className={[
                "px-3 py-1 rounded-[100px] bg-[#FF646433] font-semibold text-[0.75rem]",
                isPositive(totalAssetsChange)
                  ? "bg-red-50 text-red-500"
                  : "bg-blue-50 text-blue-500",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {formatPercent(weeklyProfitChange)}
            </span>
          </div>
          <p className="text-[1.5rem] font-semibold text-black">
            {formatNumber(weeklyProfit)}
            <span className="text-[1rem] text-normal ml-1">원</span>
          </p>
          <p
            className={[
              "",
              isPositive(weeklyProfitChange) ? "text-red-500" : "text-blue-500",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {isPositive(weeklyProfitChange) ? "+" : ""}
            {formatNumber(Math.floor(totalAssets * (weeklyProfitChange / 100)))}
            원
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
