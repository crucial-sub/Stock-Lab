"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";
import { getBacktestList } from "@/lib/api";

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

interface Strategy {
  id: string;
  strategy_name: string;
  daily_return: number;
  cumulative_return: number;
  max_drawdown: number;
  created_at: string;
}

export default function QuantPage() {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // 전략 목록 조회
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        setLoading(true);
        const response = await getBacktestList({ page, limit: 10 });
        setStrategies(response.data);
        setTotalPages(response.pagination.total_pages);
        setError(null);
      } catch (err) {
        console.error("전략 목록 조회 실패:", err);
        setError("전략 목록을 불러오는데 실패했습니다.");
      } finally {
        setLoading(false);
      }
    };

    fetchStrategies();
  }, [page]);

  const toggleStrategy = (id: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const toggleAllStrategies = () => {
    if (selectedStrategies.length === strategies.length) {
      setSelectedStrategies([]);
    } else {
      setSelectedStrategies(strategies.map((s) => s.id));
    }
  };

  const handlePreviousPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* 페이지 제목 */}
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-strong">
          내가 만든 전략 목록
        </h1>
      </div>

      {/* 탭 메뉴 */}
      <div className="mb-6 flex gap-3">
        <button className="bg-accent-danger text-white px-6 py-2.5 rounded-lg font-medium">
          새 전략 만들기
        </button>
        <button className="bg-bg-surface text-text-body px-6 py-2.5 rounded-lg font-medium hover:bg-bg-surface-hover transition-colors">
          선택 전략 삭제하기
        </button>
      </div>

      {/* 검색창 */}
      <div className="mb-6 flex items-center gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="전략 이름으로 검색하기"
            className="w-full bg-bg-surface border border-border-default rounded-lg px-4 py-2.5 pr-10 text-text-body placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-brand-primary"
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
            <button className="font-normal">
              1
            </button>
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

      {/* 전략 테이블 */}
      <div className="bg-bg-surface rounded-lg border border-border-default overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-text-muted">로딩 중...</p>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-12">
            <p className="text-accent-danger">{error}</p>
          </div>
        ) : strategies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-text-muted mb-4">생성된 전략이 없습니다.</p>
            <p className="text-text-muted text-sm">새 전략을 만들어보세요!</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border-default bg-bg-surface-hover">
                <th className="px-6 py-4 text-left">
                  <input
                    type="checkbox"
                    checked={
                      selectedStrategies.length === strategies.length &&
                      strategies.length > 0
                    }
                    onChange={toggleAllStrategies}
                    className="w-4 h-4 rounded border-border-default"
                  />
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-text-strong">
                  전략 이름
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-text-strong">
                  일평균 수익률
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-text-strong">
                  누적 수익률
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-text-strong">
                  최대 낙폭(MDD)
                </th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-text-strong">
                  생성일
                </th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((strategy) => (
                <tr
                  key={strategy.id}
                  className="border-b border-border-default last:border-0 hover:bg-bg-surface-hover transition-colors"
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedStrategies.includes(strategy.id)}
                      onChange={() => toggleStrategy(strategy.id)}
                      className="w-4 h-4 rounded border-border-default"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      href={`/quant/result?id=${strategy.id}`}
                      className="text-brand-primary hover:underline font-medium"
                    >
                      {strategy.strategy_name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-text-body">
                    {strategy.daily_return}%
                  </td>
                  <td
                    className={`px-6 py-4 text-sm font-medium ${
                      strategy.cumulative_return > 0
                        ? "text-accent-danger"
                        : "text-accent-primary"
                    }`}
                  >
                    {strategy.cumulative_return > 0 ? "+" : ""}
                    {strategy.cumulative_return}%
                  </td>
                  <td
                    className={`px-6 py-4 text-sm font-medium ${
                      strategy.max_drawdown > 0
                        ? "text-accent-danger"
                        : "text-accent-primary"
                    }`}
                  >
                    {strategy.max_drawdown > 0 ? "+" : ""}
                    {strategy.max_drawdown}%
                  </td>
                  <td className="px-6 py-4 text-sm text-text-body">
                    {strategy.created_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 페이지네이션 */}
      {!loading && strategies.length > 0 && (
        <div className="mt-6 flex justify-center items-center gap-3">
          <button
            onClick={handlePreviousPage}
            disabled={page === 1}
            className="p-2 hover:bg-bg-surface-hover rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Image src="/icons/arrow_left.svg" alt="이전" width={20} height={20} />
          </button>
          <button className="px-4 py-2 bg-brand-primary text-white rounded font-medium">
            {page}
          </button>
          {totalPages > 1 && (
            <span className="text-text-muted text-sm">/ {totalPages}</span>
          )}
          <button
            onClick={handleNextPage}
            disabled={page === totalPages}
            className="p-2 hover:bg-bg-surface-hover rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Image
              src="/icons/arrow_right.svg"
              alt="다음"
              width={20}
              height={20}
            />
          </button>
        </div>
      )}

      {/* 하단 가이드 카드 */}
      <div className="mt-5 grid grid-cols-3 gap-6">
        <GuideCard
          icon="📈"
          title="퀀트 투자에 대해 알아보기 #1"
          descriptions={["퀀트 투자가 처음이라면, 왜? 가이드를 읽어보세요!", "개발자가 퀀트 투자에 대해 자세히 설명해드립니다 😊"]}
        />
        <GuideCard
          icon="📊"
          title="퀀트 투자에 대해 알아보기 #2"
          descriptions={["퀀트 투자에 어느 정도 익숙하신가요?", "그렇다면 본격적으로 전략을 짜면 피봇하세요! 😊"]}
        />
        <GuideCard
          icon="🤔"
          title="퀀트 투자에서 수익을 내려면?"
          descriptions={["퀀트 투자에서도 많았던 수익을 내기가 너무 어렵다구요?", "왜? 가이드를 통해 같이 수익을 내어보아요! 😎"]}
        />
      </div>
    </div>
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
      <h3 className="flex text-[1.5rem] font-semibold">{icon} {title}</h3>
      <div className="flex flex-col gap-[18px]">
        {descriptions.map((desc, index) => (
          <div key={`${desc}-${index}`} className="text-[18px] font-normal">{desc}</div>
        ))}
      </div>
    </div>
  );
}
