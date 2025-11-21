"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { CreatePortfolioCard } from "@/components/quant/CreatePortfolioCard";
import { PortfolioCard } from "@/components/quant/PortfolioCard";
import { PortfolioDashboard } from "@/components/quant/PortfolioDashboard";
import { strategyApi } from "@/lib/api/strategy";

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
  /** 평가손익 */
  totalProfit: number;
  /** 수익률 */
  totalReturn: number;
  /** 평가금액 */
  evaluationAmount: number;
  /** 활성 포트폴리오 개수 */
  activePortfolioCount: number;
  /** 포트폴리오 목록 */
  portfolios: Portfolio[];
}

export function PortfolioPageClient({
  totalAssets,
  totalProfit,
  totalReturn,
  evaluationAmount,
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

  return (
    <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
      {/* 대시보드 */}
      <PortfolioDashboard
        totalAssets={totalAssets}
        totalProfit={totalProfit}
        totalReturn={totalReturn}
        evaluationAmount={evaluationAmount}
        activePortfolioCount={activePortfolioCount}
      />
      {/* 제거된 커뮤니티 섹션 (랭킹/공유)는 커뮤니티 페이지로 이동 */}
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
