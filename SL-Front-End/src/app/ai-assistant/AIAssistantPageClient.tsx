"use client";

import { SecondarySidebar } from "@/components/ai-assistant/SecondarySidebar";
import { StrategyCard } from "@/components/ai-assistant/StrategyCard";
import { AISearchInput } from "@/components/home/ui";

/**
 * AI 어시스턴트 페이지 클라이언트 컴포넌트
 *
 * @description 인터랙티브한 AI 어시스턴트 화면 UI를 담당합니다.
 * 이벤트 핸들러와 상태 관리가 필요한 부분만 클라이언트 컴포넌트로 분리.
 */

interface Strategy {
  id: string;
  title: string;
  description: string;
}

interface AIAssistantPageClientProps {
  /** 큰 카드 정보 */
  largeStrategy: {
    title: string;
    description: string;
  };
  /** 작은 카드 목록 */
  smallStrategies: Strategy[];
}

export function AIAssistantPageClient({
  largeStrategy,
  smallStrategies,
}: AIAssistantPageClientProps) {
  const handleLargeCardClick = () => {
    // TODO: 큰 카드 클릭 처리 로직 구현
    console.log("Large card clicked");
  };

  const handleStrategyClick = (strategyId: string) => {
    // TODO: 전략 카드 클릭 처리 로직 구현
    console.log(`Strategy ${strategyId} clicked`);
  };

  const handleAISubmit = (value: string) => {
    // TODO: AI 요청 처리 로직 구현
    console.log("AI request:", value);
  };

  return (
    <div className="flex h-full">
      {/* 2차 사이드바 */}
      <SecondarySidebar />

      {/* 메인 콘텐츠 */}
      <main className="flex-1 flex flex-col items-center px-10 pt-[120px] pb-20 overflow-auto">
        {/* 타이틀 */}
        <h1 className="text-[32px] font-bold text-black text-center mb-[80px]">
          궁금한 내용을 AI에게 확인해보세요!
        </h1>

        {/* 큰 카드 */}
        <div className="w-full max-w-[1000px] mb-[112px]">
          <StrategyCard
            title={largeStrategy.title}
            description={largeStrategy.description}
            size="large"
            onClick={handleLargeCardClick}
          />
        </div>

        {/* 작은 카드 그리드 (2x2) */}
        <div className="grid grid-cols-2 gap-x-[40px] gap-y-[32px] mb-[114px]">
          {smallStrategies.map((strategy) => (
            <StrategyCard
              key={strategy.id}
              title={strategy.title}
              description={strategy.description}
              onClick={() => handleStrategyClick(strategy.id)}
            />
          ))}
        </div>

        {/* AI 입력창 */}
        <div className="w-full max-w-[1000px]">
          <AISearchInput
            placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
            onSubmit={handleAISubmit}
          />
        </div>
      </main>
    </div>
  );
}
