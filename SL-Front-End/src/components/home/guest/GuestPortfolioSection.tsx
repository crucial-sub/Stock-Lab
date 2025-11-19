"use client";

import { Title } from "@/components/common/Title";
import { RankingCard } from "@/components/community";
import { useTopRankingsQuery } from "@/hooks/useCommunityQuery";

export function GuestPortfolioSection() {
  // 커뮤니티 랭킹 API 사용 (백테스팅 세션 랭킹)
  const {
    data: topRankings,
    isLoading: rankingsLoading,
    error: rankingsError,
  } = useTopRankingsQuery();

  // 수익률 포맷팅 함수
  const formatReturn = (value: number): string => {
    const formatted = value.toFixed(2);
    return value > 0 ? `+${formatted}` : formatted;
  };

  return (
    <section className="flex w-full flex-col gap-5">
      <div className="flex flex-col gap-1">
        <Title>인기 전략</Title>
      </div>
      <div className="grid w-full grid-cols-1 gap-5 md:grid-cols-3">
        {rankingsLoading ? (
          <div className="col-span-full text-center py-10">
            <p className="text-text-muted">로딩 중...</p>
          </div>
        ) : rankingsError ? (
          <div className="col-span-full text-center py-10">
            <p className="text-text-muted">
              랭킹 데이터를 불러올 수 없습니다.
            </p>
          </div>
        ) : topRankings?.rankings && topRankings.rankings.length > 0 ? (
          topRankings.rankings.map((item) => (
            <RankingCard
              key={item.rank}
              rank={item.rank as 1 | 2 | 3}
              portfolioName={item.strategyName}
              author={item.authorNickname || "익명"}
              returnRate={formatReturn(item.totalReturn)}
              // 복제 기능 제거 (onCopy prop 전달 안 함)
            />
          ))
        ) : (
          <div className="col-span-full text-center py-10">
            <p className="text-text-muted">아직 랭킹 데이터가 없습니다.</p>
          </div>
        )}
      </div>
    </section>
  );
}
