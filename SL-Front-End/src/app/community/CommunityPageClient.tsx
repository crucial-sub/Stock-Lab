"use client";

import { useRouter } from "next/navigation";
import { DiscussionPreviewSection } from "@/components/community";
import {
  RankingCard,
  PortfolioShareCard,
} from "@/components/strategy_portfolio";
import {
  useCloneStrategyMutation,
  usePublicStrategiesQuery,
  useTopRankingsQuery,
} from "@/hooks/useCommunityQuery";

/**
 * 커뮤니티 페이지 클라이언트 컴포넌트
 * - 수익률 랭킹
 * - 공유된 포트폴리오
 * - 자유게시판
 */
export default function CommunityPageClient() {
  const router = useRouter();

  // API 연동
  const {
    data: topRankings,
    isLoading: rankingsLoading,
    error: rankingsError,
  } = useTopRankingsQuery();
  const {
    data: publicStrategies,
    isLoading: strategiesLoading,
    error: strategiesError,
  } = usePublicStrategiesQuery({ page: 1, limit: 3 });
  const cloneStrategyMutation = useCloneStrategyMutation();

  // 수익률 포맷팅 함수
  const formatReturn = (value: number): string => {
    const formatted = value.toFixed(2);
    return value > 0 ? `+${formatted}` : formatted;
  };

  // 전략 복제 핸들러
  const handleCloneStrategy = (sessionId: string, strategyName: string) => {
    if (
      confirm(`"${strategyName}" 전략을 내 포트폴리오에 복제하시겠습니까?`)
    ) {
      cloneStrategyMutation.mutate(sessionId, {
        onSuccess: () => {
          alert("전략이 성공적으로 복제되었습니다.");
        },
        onError: (error) => {
          alert(`복제 실패: ${error.message}`);
        },
      });
    }
  };

  return (
    <div className="flex flex-col max-w-[1000px] mx-auto px-5 py-10 space-y-12">
      {/* 수익률 랭킹 */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <span className="text-[1.5rem] font-semibold text-body">수익률 랭킹</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rankingsLoading ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">로딩 중...</p>
            </div>
          ) : rankingsError ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">랭킹 데이터를 불러올 수 없습니다.</p>
            </div>
          ) : topRankings?.rankings && topRankings.rankings.length > 0 ? (
            topRankings.rankings.map((item) => (
              <RankingCard
                key={item.rank}
                rank={item.rank as 1 | 2 | 3}
                portfolioName={item.strategyName}
                author={item.authorNickname || "익명"}
                returnRate={formatReturn(item.totalReturn)}
                onCopy={() =>
                  handleCloneStrategy(item.sessionId, item.strategyName)
                }
              />
            ))
          ) : (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">아직 랭킹 데이터가 없습니다.</p>
            </div>
          )}
        </div>
      </section>

      {/* 공유된 포트폴리오 */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <span className="text-[1.5rem] font-semibold text-body">포트폴리오 공유하기</span>
          <button
            onClick={() => router.push("/community/public-strategies")}
            className="text-[1rem] text-brand-purple font-normal hover:underline"
          >
            더보기
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {strategiesLoading ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">로딩 중...</p>
            </div>
          ) : strategiesError ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">
                공개 포트폴리오 데이터를 불러올 수 없습니다.
              </p>
            </div>
          ) : publicStrategies?.strategies &&
            publicStrategies.strategies.length > 0 ? (
            publicStrategies.strategies.map((item) => {
              const returnRate =
                typeof item.totalReturn === "number"
                  ? item.totalReturn.toFixed(2)
                  : "-";

              return (
                <PortfolioShareCard
                  key={item.strategyId}
                  sessionId={item.sessionId || ""}
                  portfolioName={item.strategyName}
                  author={item.ownerName || "익명"}
                  description={item.description || "설명이 없습니다."}
                  returnRate={returnRate}
                  stocks={[]}
                  onAdd={
                    item.sessionId
                      ? () =>
                        handleCloneStrategy(item.sessionId!, item.strategyName)
                      : undefined
                  }
                />
              );
            })
          ) : (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">아직 공유된 포트폴리오가 없습니다.</p>
            </div>
          )}
        </div>
      </section>

      {/* 자유게시판 */}
      <DiscussionPreviewSection limit={5} />
    </div>
  );
}
