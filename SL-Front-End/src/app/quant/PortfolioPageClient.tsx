"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CreatePortfolioCard } from "@/components/quant/CreatePortfolioCard";
import { PortfolioCard } from "@/components/quant/PortfolioCard";
import { PortfolioDashboard } from "@/components/quant/PortfolioDashboard";
import { strategyApi } from "@/lib/api/strategy";

import { CommunityPostCard } from "@/components/community";
import {
  RankingCard,
  PortfolioShareCard,
} from "@/components/strategy_portfolio";

import {
  useTopRankingsQuery,
  usePostsQuery,
  useCloneStrategyMutation,
} from "@/hooks/useCommunityQuery";

/**
 * 포트폴리오 페이지 클라이언트 컴포넌트
 *
 * @description 포트폴리오 목록과 대시보드를 표시하는 클라이언트 컴포넌트
 * 인터랙션과 상태 관리를 담당합니다.
 */

interface Portfolio {
  id: string;
  strategyId: string;
  title: string;
  profitRate: number;
  isActive: boolean;
  lastModified: string;
  createdAt: string;
}

interface PortfolioPageClientProps {
  /** 총 모의 자산 */
  totalAssets: number;
  /** 총 자산 수익률 */
  totalAssetsChange: number;
  /** 이번주 수익 */
  weeklyProfit: number;
  /** 이번주 수익률 */
  weeklyProfitChange: number;
  /** 활성 포트폴리오 개수 */
  activePortfolioCount: number;
  /** 포트폴리오 목록 */
  portfolios: Portfolio[];
}

export function PortfolioPageClient({
  totalAssets,
  totalAssetsChange,
  weeklyProfit,
  weeklyProfitChange,
  activePortfolioCount,
  portfolios: initialPortfolios,
}: PortfolioPageClientProps) {
  const router = useRouter();

  // 포트폴리오 목록 상태 (삭제 후 UI 업데이트를 위해)
  const [portfolios, setPortfolios] = useState<Portfolio[]>(initialPortfolios);

  // 선택된 포트폴리오 ID 목록
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // 삭제 진행 중 상태
  const [isDeleting, setIsDeleting] = useState(false);

  // 포트폴리오 선택/해제 핸들러
  const handleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // 포트폴리오 클릭 핸들러 - 백테스트 결과 상세 페이지로 이동
  const handlePortfolioClick = (id: string) => {
    // 자동매매 전략 카드인 경우 자동매매 상태 페이지로 이동
    if (id.startsWith("auto-")) {
      const portfolio = portfolios.find((p) => p.id === id);
      if (portfolio?.strategyId) {
        router.push(`/quant/auto-trading/${portfolio.strategyId}`);
        return;
      }
    }
    router.push(`/quant/result/${id}`);
  };

  // 선택 항목 삭제 핸들러
  const handleDeleteSelected = async () => {
    // 선택된 항목이 없으면 종료
    if (selectedIds.size === 0) {
      alert("삭제할 포트폴리오를 선택해주세요.");
      return;
    }

    // 사용자 확인
    const confirmed = window.confirm(
      `선택한 ${selectedIds.size}개의 포트폴리오를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsDeleting(true);

      // API 호출 - 선택된 ID 배열로 변환
      const sessionIds = Array.from(selectedIds);
      await strategyApi.deleteBacktestSessions(sessionIds);

      // 성공: 로컬 상태에서 삭제된 항목 제거
      setPortfolios((prev) =>
        prev.filter((portfolio) => !selectedIds.has(portfolio.id)),
      );

      // 선택 상태 초기화
      setSelectedIds(new Set());

      // 성공 메시지
      alert(`${sessionIds.length}개의 포트폴리오가 삭제되었습니다.`);

      // 페이지 새로고침 (대시보드 통계 업데이트를 위해)
      router.refresh();
    } catch (error: unknown) {
      console.error("포트폴리오 삭제 실패:", error);

      // 에러 메시지 표시
      const errorMessage =
        (
          error as {
            response?: { data?: { detail?: string } };
            message?: string;
          }
        )?.response?.data?.detail ||
        (error as { message?: string })?.message ||
        "포트폴리오 삭제 중 오류가 발생했습니다.";
      alert(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  // 활성 포트폴리오를 맨 앞으로, 나머지는 최신순으로 정렬
  const sortedPortfolios = [...portfolios].sort((a, b) => {
    // 1. 활성 상태 우선
    if (a.isActive && !b.isActive) return -1;
    if (!a.isActive && b.isActive) return 1;
    // 2. 같은 활성 상태면 최신순 (createdAt 기준)
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
  });

  const {
      data: topRankings,
      isLoading: rankingsLoading,
      error: rankingsError,
    } = useTopRankingsQuery();
    const {
      data: strategySharePosts,
      isLoading: strategyShareLoading,
      error: strategyShareError,
    } = usePostsQuery({ postType: "STRATEGY_SHARE", limit: 3 });
    const {
      data: discussionPosts,
      isLoading: discussionLoading,
      error: discussionError,
    } = usePostsQuery({ postType: "DISCUSSION", limit: 3 });
  
    const cloneStrategyMutation = useCloneStrategyMutation();

  // 수익률 포맷팅 함수
  const formatReturn = (value: number): string => {
    const formatted = value.toFixed(2);
    return value > 0 ? `+${formatted}` : formatted;
  };

  // 전략 복제 핸들러
  const handleCloneStrategy = (sessionId: string, strategyName: string) => {
    if (
      confirm(
        `"${strategyName}" 전략을 내 포트폴리오에 복제하시겠습니까?`
      )
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

  // 로딩 상태 표시 (모든 데이터가 로딩 중일 때만)
  const isAllLoading =
    rankingsLoading && strategyShareLoading && discussionLoading;

  if (isAllLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <p className="text-lg text-muted">로딩 중...</p>
      </div>
    );
  }

  return (
    <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
      {/* 대시보드 */}
      <PortfolioDashboard
        totalAssets={totalAssets}
        totalAssetsChange={totalAssetsChange}
        weeklyProfit={weeklyProfit}
        weeklyProfitChange={weeklyProfitChange}
        activePortfolioCount={activePortfolioCount}
      />
      {/* 수익률 랭킹 섹션 */}
      <section className="mb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-body">수익률 랭킹</h2>
          <button
            onClick={() => router.push("/community/rankings")}
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rankingsLoading ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">로딩 중...</p>
            </div>
          ) : rankingsError ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">
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

      {/* 포트폴리오 공유하기 섹션 */}
      <section className="mb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-body">포트폴리오 공유하기</h2>
          <button
            onClick={() =>
              router.push("/community/posts?postType=STRATEGY_SHARE")
            }
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {strategyShareLoading ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">로딩 중...</p>
            </div>
          ) : strategyShareError ? (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">
                포트폴리오 공유 데이터를 불러올 수 없습니다.
              </p>
            </div>
          ) : strategySharePosts?.posts && strategySharePosts.posts.length > 0 ? (
            strategySharePosts.posts.map((post) => (
              <PortfolioShareCard
                key={post.postId}
                portfolioName={post.title}
                author={post.authorNickname || "익명"}
                description={post.contentPreview}
                returnRate={formatReturn(0)}
                stocks={post.tags || []}
                onAdd={() => router.push(`/community/${post.postId}`)}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-10">
              <p className="text-muted">
                아직 공유된 포트폴리오가 없습니다.
              </p>
            </div>
          )}
        </div>
      </section>
      {/* 내 포트폴리오 섹션 */}
      <section aria-label="내 포트폴리오">
        {/* 섹션 헤더 */}
        <div className="flex items-center justify-between mb-[40px]">
          <h2 className="text-[2rem] font-bold text-black">내 포트폴리오</h2>
          <button
            type="button"
            onClick={handleDeleteSelected}
            disabled={isDeleting || selectedIds.size === 0}
            className="text-[#c8c8c8] hover:text-black transition-colors underline disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? "삭제 중..." : "선택항목 삭제"}
          </button>
        </div>

        {/* 포트폴리오 그리드 */}
        <div className="grid grid-cols-3 gap-[20px]">
          {/* 새로 만들기 카드 */}
          <CreatePortfolioCard />

          {/* 모든 포트폴리오 (활성 우선, 최신순) */}
          {sortedPortfolios.map((portfolio) => (
            <PortfolioCard
              key={portfolio.id}
              {...portfolio}
              isSelected={selectedIds.has(portfolio.id)}
              onSelect={handleSelect}
              onClick={handlePortfolioClick}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
