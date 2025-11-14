"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";

import { getBacktestList } from "@/lib/api";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Title } from "@/components/common/Title";
import { SearchBar } from "@/components/quant/list/SearchBar";
import { StrategyActions } from "@/components/quant/list/StrategyActions";
import { StrategyList } from "@/components/quant/list/StrategyList";
import { useStrategyList } from "@/hooks/useStrategyList";
import type { Strategy } from "@/types/strategy";

/**
 * 퀀트 전략 목록 페이지 (메인)
 * Figma 디자인: 01.quant_page.png
 *
 * 컴포넌트 구조:
 * - StrategyActions: 새 전략 만들기, 선택 전략 삭제 버튼
 * - SearchBar: 전략 검색 기능
 * - StrategyList: 전략 목록 테이블
 * - GuideCard: 하단 가이드 카드 섹션
 */
export default function QuantPage() {
  // 더미 데이터 (향후 서버 API로 교체)
  const initialStrategies: Strategy[] = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    name: "전략 이름은 이렇게 표시",
    dailyAverageReturn: i % 3 === 0 ? 99.9 : -99.9,
    cumulativeReturn: i % 3 === 0 ? 99.9 : -99.9,
    maxDrawdown: i % 3 === 0 ? 99.99 : -99.99,
    createdAt: "2025.12.31",
  }));

  // 전략 목록 관리 훅
  const {
    strategies,
    selectedIds,
    searchKeyword,
    isLoading,
    toggleStrategy,
    toggleAllStrategies,
    updateSearchKeyword,
    executeSearch,
    deleteSelectedStrategies,
  } = useStrategyList(initialStrategies);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background pb-[3.25rem]">
        <Title className="mb-5">내가 만든 전략 목록</Title>
        <div className="bg-bg-surface rounded-md p-5">
          {/* 액션 버튼 (새 전략 만들기, 선택 전략 삭제) */}
          <div className="flex mb-6 justify-between">
            <StrategyActions
              selectedCount={selectedIds.length}
              onDelete={deleteSelectedStrategies}
            />
            <SearchBar
              value={searchKeyword}
              onChange={updateSearchKeyword}
              onSearch={executeSearch}
            />
          </div>

          {/* 전략 테이블 */}
          <StrategyList
            strategies={strategies}
            selectedIds={selectedIds}
            onToggleAll={toggleAllStrategies}
            onToggleItem={toggleStrategy}
          />

          {/* 페이지네이션 */}
          <div className="h-8 py-1 flex justify-center items-center gap-[22px]">
            <button className="hover:bg-bg-surface-hover rounded transition-colors">
              <Image src="/icons/arrow_left.svg" alt="이전" width={24} height={24} />
            </button>
            <div>
              <button className="font-normal">1</button>
            </div>
            <button className="hover:bg-bg-surface-hover rounded transition-colors">
              <Image
                src="/icons/arrow_right.svg"
                alt="다음"
                width={24}
                height={24}
              />
            </button>
          </div>
        </div>

        {/* 하단 가이드 카드 */}
        <div className="mt-5 grid grid-cols-3 gap-6">
          <GuideCard
            icon="📈"
            title="퀀트 투자에 대해 알아보기 #1"
            descriptions={[
              "퀀트 투자가 처음이라면, 왜? 가이드를 읽어보세요!",
              "개발자가 퀀트 투자에 대해 자세히 설명해드립니다 😊",
            ]}
          />
          <GuideCard
            icon="📊"
            title="퀀트 투자에 대해 알아보기 #2"
            descriptions={[
              "퀀트 투자에 어느 정도 익숙하신가요?",
              "그렇다면 본격적으로 전략을 짜면 피봇하세요! 😊",
            ]}
          />
          <GuideCard
            icon="🤔"
            title="퀀트 투자에서 수익을 내려면?"
            descriptions={[
              "퀀트 투자에서도 많았던 수익을 내기가 너무 어렵다구요?",
              "왜? 가이드를 통해 같이 수익을 내어보아요! 😎",
            ]}
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}

/**
 * 가이드 카드 컴포넌트
 */
interface GuideCardProps {
  icon: string;
  title: string;
  descriptions: string[];
}

function GuideCard({ icon, title, descriptions }: GuideCardProps) {
  return (
    <div className="flex flex-col gap-3 bg-bg-surface rounded-md p-6 shadow-card">
      <h3 className="flex text-[1.5rem] font-semibold">
        {icon} {title}
      </h3>
      <div className="flex flex-col gap-[18px]">
        {descriptions.map((desc, index) => (
          <div key={`${desc}-${index}`} className="text-[18px] font-normal">
            {desc}
          </div>
        ))}
      </div>
    </div>
  );
}
