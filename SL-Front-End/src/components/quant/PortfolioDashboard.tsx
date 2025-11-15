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
      <h1 className="text-[32px] font-bold text-black mb-[40px]">
        포트폴리오 대시보드
      </h1>

      {/* 대시보드 카드 그리드 */}
      <div className="grid grid-cols-3 gap-[20px]">
        {/* 총 모의 자산 */}
        <div className="bg-surface border border-surface rounded-lg px-5 py-4 h-[100px]">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-base font-semibold text-black">총 모의 자산</h2>
            <span
              className={[
                "text-xs font-medium px-2 py-0.5 rounded",
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
          <p className="text-[28px] font-bold text-black">
            {formatNumber(totalAssets)}
            <span className="text-xl font-normal ml-1">원</span>
          </p>
          <p
            className={[
              "text-sm font-medium mt-1",
              isPositive(totalAssetsChange)
                ? "text-red-500"
                : "text-blue-500",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {isPositive(totalAssetsChange) ? "+" : ""}
            {formatNumber(
              Math.floor(totalAssets * (totalAssetsChange / 100))
            )}
            원
          </p>
        </div>

        {/* 이번주 수익 */}
        <div className="bg-surface border border-surface rounded-lg px-5 py-4 h-[100px]">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-base font-semibold text-black">이번주 수익</h2>
            <span
              className={[
                "text-xs font-medium px-2 py-0.5 rounded",
                isPositive(weeklyProfitChange)
                  ? "bg-red-50 text-red-500"
                  : "bg-blue-50 text-blue-500",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {formatPercent(weeklyProfitChange)}
            </span>
          </div>
          <p className="text-[28px] font-bold text-black">
            {formatNumber(weeklyProfit)}
            <span className="text-xl font-normal ml-1">원</span>
          </p>
        </div>

        {/* 활성 포트폴리오 */}
        <div className="bg-surface border border-surface rounded-lg px-5 py-4 h-[100px]">
          <h2 className="text-base font-semibold text-black mb-2">
            활성 포트폴리오
          </h2>
          <p className="text-[28px] font-bold text-black">
            {activePortfolioCount}
            <span className="text-xl font-normal ml-1">개</span>
          </p>
          <p className="text-sm font-normal text-muted mt-1">
            현재 활성 중인 포트폴리오 개수
          </p>
        </div>
      </div>
    </section>
  );
}
