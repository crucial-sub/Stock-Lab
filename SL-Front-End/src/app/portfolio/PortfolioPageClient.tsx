"use client";

import { useState } from "react";
import { PortfolioDashboard } from "@/components/portfolio/PortfolioDashboard";
import { PortfolioCard } from "@/components/portfolio/PortfolioCard";
import { CreatePortfolioCard } from "@/components/portfolio/CreatePortfolioCard";

/**
 * 포트폴리오 페이지 클라이언트 컴포넌트
 *
 * @description 포트폴리오 목록과 대시보드를 표시하는 클라이언트 컴포넌트
 * 인터랙션과 상태 관리를 담당합니다.
 */

interface Portfolio {
  id: string;
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
  portfolios,
}: PortfolioPageClientProps) {
  // 선택된 포트폴리오 ID 목록
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

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

  // 포트폴리오 클릭 핸들러
  const handlePortfolioClick = (id: string) => {
    // TODO: 포트폴리오 상세 페이지로 이동
    console.log("Portfolio clicked:", id);
  };

  // 활성 포트폴리오를 맨 앞으로, 나머지는 그대로 유지
  const activePortfolio = portfolios.find((p) => p.isActive);
  const inactivePortfolios = portfolios.filter((p) => !p.isActive);

  return (
    <main className="flex-1 px-10 pt-[60px] pb-20 overflow-auto">
      {/* 대시보드 */}
      <PortfolioDashboard
        totalAssets={totalAssets}
        totalAssetsChange={totalAssetsChange}
        weeklyProfit={weeklyProfit}
        weeklyProfitChange={weeklyProfitChange}
        activePortfolioCount={activePortfolioCount}
      />

      {/* 내 포트폴리오 섹션 */}
      <section aria-label="내 포트폴리오">
        {/* 섹션 헤더 */}
        <div className="flex items-center justify-between mb-[40px]">
          <h2 className="text-2xl font-bold text-black">내 포트폴리오</h2>
          <button
            type="button"
            className="text-sm font-medium text-muted hover:text-black transition-colors"
          >
            전체삭제
          </button>
        </div>

        {/* 포트폴리오 그리드 */}
        <div className="grid grid-cols-3 gap-[20px]">
          {/* 새로 만들기 카드 */}
          <CreatePortfolioCard />

          {/* 활성 포트폴리오 (새로 만들기 바로 다음) */}
          {activePortfolio && (
            <PortfolioCard
              key={activePortfolio.id}
              {...activePortfolio}
              isSelected={selectedIds.has(activePortfolio.id)}
              onSelect={handleSelect}
              onClick={handlePortfolioClick}
            />
          )}

          {/* 비활성 포트폴리오들 */}
          {inactivePortfolios.map((portfolio) => (
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
