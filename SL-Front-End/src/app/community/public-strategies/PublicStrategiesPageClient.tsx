"use client";

import { useRouter } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import { PortfolioShareCard } from "@/components/strategy_portfolio";
import { communityQueryKey } from "@/hooks/useCommunityQuery";
import { strategyApi, type PublicStrategyListItem } from "@/lib/api/strategy";

const PAGE_SIZE = 12;

export function PublicStrategiesPageClient() {
  const router = useRouter();

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: communityQueryKey.publicStrategies({ limit: PAGE_SIZE }),
    queryFn: ({ pageParam = 1 }) =>
      strategyApi.getPublicStrategies({
        page: pageParam as number,
        limit: PAGE_SIZE,
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.hasNext ? pages.length + 1 : undefined,
    initialPageParam: 1,
    staleTime: 1000 * 60 * 5,
  });

  const strategies: PublicStrategyListItem[] =
    data?.pages.flatMap((page) => page.strategies) || [];

  return (
    <div className="max-w-[1100px] mx-auto px-5 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-body">공개 포트폴리오</h1>
        <button
          type="button"
          onClick={() => router.push("/community")}
          className="text-base text-gray-700 underline hover:text-gray-600"
        >
          커뮤니티 홈으로
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-muted">로딩 중...</div>
      ) : error ? (
        <div className="text-center py-20 text-muted">
          공개 포트폴리오 데이터를 불러올 수 없습니다.
        </div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-20 text-muted">
          아직 공개된 포트폴리오가 없습니다.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {strategies.map((item) => {
              const returnRate =
                typeof item.totalReturn === "number"
                  ? item.totalReturn.toFixed(2)
                  : "-";

              return (
                <PortfolioShareCard
                  key={item.strategyId}
                  portfolioName={item.strategyName}
                  author={item.ownerName || "익명"}
                  description={item.description || "설명이 없습니다."}
                  returnRate={returnRate}
                  stocks={[]}
                />
              );
            })}
          </div>

          {hasNextPage && (
            <div className="flex justify-center pt-6">
              <button
                type="button"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="rounded-[12px] border border-[#dbe3f5] px-6 py-3 text-sm font-semibold text-gray-800 hover:bg-[#f3f5ff] transition disabled:opacity-60"
              >
                {isFetchingNextPage ? "불러오는 중..." : "더 보기"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
