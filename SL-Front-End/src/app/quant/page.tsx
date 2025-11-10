"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import { Title } from "@/components/common/Title";

/**
 * 퀀트 전략 목록 페이지 (메인)
 * Figma 디자인: 01.quant_page.png
 */
export default function QuantPage() {
  const [selectedStrategies, setSelectedStrategies] = useState<number[]>([1, 2, 3, 7]);

  // 더미 데이터
  const strategies = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    name: "전략 이름은 이렇게 표시",
    cumulativeReturn: i % 3 === 0 ? 99.9 : -99.9,
    maxDrawdown: i % 3 === 0 ? 99.99 : -99.99,
    startDate: "2025.12.31",
    endDate: "2025.12.31",
  }));

  const toggleStrategy = (id: number) => {
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

  return (
    <div className="min-h-screen bg-background p-6">
      {/* 페이지 제목 */}
      <div className="mb-6 flex items-center justify-between">
        <Title>내가 만든 전략 목록</Title>
        <Link
          href="/quant/new"
          className="bg-accent-danger text-white px-6 py-2.5 rounded-lg font-medium hover:bg-accent-danger/90 transition-colors"
        >
          새 전략 만들기
        </Link>
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
          <Image
            src="/icons/search.svg"
            alt="검색"
            width={20}
            height={20}
            className="absolute right-3 top-1/2 -translate-y-1/2 opacity-50"
          />
        </div>
      </div>

      {/* 전략 테이블 */}
      <div className="bg-bg-surface rounded-lg border border-border-default overflow-hidden">
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
                투자 수익률
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
                    href={`/quant/result`}
                    className="text-brand-primary hover:underline font-medium"
                  >
                    {strategy.name}
                  </Link>
                </td>
                <td className="px-6 py-4 text-sm text-text-body">
                  {strategy.cumulativeReturn}%
                </td>
                <td
                  className={`px-6 py-4 text-sm font-medium ${strategy.cumulativeReturn > 0
                      ? "text-accent-danger"
                      : "text-accent-primary"
                    }`}
                >
                  {strategy.cumulativeReturn > 0 ? "+" : ""}
                  {strategy.cumulativeReturn}%
                </td>
                <td
                  className={`px-6 py-4 text-sm font-medium ${strategy.maxDrawdown > 0
                      ? "text-accent-danger"
                      : "text-accent-primary"
                    }`}
                >
                  {strategy.maxDrawdown > 0 ? "+" : ""}
                  {strategy.maxDrawdown}%
                </td>
                <td className="px-6 py-4 text-sm text-text-body">
                  {strategy.startDate}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      <div className="mt-6 flex justify-center items-center gap-3">
        <button className="p-2 hover:bg-bg-surface-hover rounded transition-colors">
          <Image src="/icons/arrow_left.svg" alt="이전" width={20} height={20} />
        </button>
        <button className="px-4 py-2 bg-brand-primary text-white rounded font-medium">
          1
        </button>
        <button className="p-2 hover:bg-bg-surface-hover rounded transition-colors">
          <Image
            src="/icons/arrow_right.svg"
            alt="다음"
            width={20}
            height={20}
          />
        </button>
      </div>

      {/* 하단 가이드 카드 */}
      <div className="mt-12 grid grid-cols-3 gap-6">
        <GuideCard
          icon="📈"
          title="퀀트 투자에 대해 알아보기 #1"
          description="퀀트 투자가 처음이라면, 왜? 가이드를 읽어보세요!"
          footer="개발자가 퀀트 투자에 대해 자세히 설명해드립니다 😊"
        />
        <GuideCard
          icon="📊"
          title="퀀트 투자에 대해 알아보기 #2"
          description="퀀트 투자에 어느 정도 익숙하신가요?"
          footer="그렇다면 본격적으로 전략을 짜면 피봇하세요! 😊"
        />
        <GuideCard
          icon="🤔"
          title="퀀트 투자에서 수익을 내려면?"
          description="퀀트 투자에서도 많았던 수익을 내기가 너무 어렵다구요?"
          footer="왜? 가이드를 통해 같이 수익을 내어보아요! 😎"
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
  description: string;
  footer: string;
}

function GuideCard({ icon, title, description, footer }: GuideCardProps) {
  return (
    <div className="bg-bg-surface rounded-lg border border-border-default p-6 hover:shadow-lg transition-shadow">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-text-strong mb-2">{title}</h3>
      <p className="text-sm text-text-body mb-4">{description}</p>
      <p className="text-xs text-text-muted">{footer}</p>
    </div>
  );
}
