/**
 * 전략 추천 메시지 렌더러
 *
 * 추천받은 전략들을 카드 형태로 렌더링
 * 각 전략의 조건은 아코디언으로 표시
 */

"use client";

import { useState } from "react";
import type { StrategyRecommendationMessage } from "@/types/message";

interface StrategyRecommendationRendererProps {
  message: StrategyRecommendationMessage;
  onSelectStrategy?: (strategyId: string, strategyName: string) => void;
}

/**
 * 전략 추천 메시지를 렌더링하는 컴포넌트
 */
export function StrategyRecommendationRenderer({
  message,
  onSelectStrategy,
}: StrategyRecommendationRendererProps) {
  const [expandedStrategyId, setExpandedStrategyId] = useState<string | null>(null);

  // 전략 선택 핸들러
  function handleSelectStrategy(strategyId: string, strategyName: string) {
    console.log("Selected strategy:", strategyId, strategyName);

    // 상위 컴포넌트의 콜백 호출
    if (onSelectStrategy) {
      onSelectStrategy(strategyId, strategyName);
    }
  }

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[95%] w-full space-y-4">
        {message.strategies.map((strategy) => {
          const isExpanded = expandedStrategyId === strategy.id;

          return (
            <div
              key={strategy.id}
              className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden"
            >
              {/* 전략 헤더 */}
              <div className="px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-base font-bold text-gray-900">
                      {strategy.name}
                    </h3>
                    <p className="mt-1 text-sm text-gray-600">
                      {strategy.summary}
                    </p>
                    {strategy.matchScore !== undefined && (
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-xs font-medium text-purple-600">
                          매칭도: {strategy.matchScore}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* 설명 */}
                <p className="mt-3 text-sm text-gray-700 leading-relaxed">
                  {strategy.description}
                </p>

                {/* 조건 토글 버튼 */}
                <button
                  onClick={() =>
                    setExpandedStrategyId(isExpanded ? null : strategy.id)
                  }
                  className="mt-3 text-sm font-medium text-purple-600 hover:text-purple-700"
                >
                  {isExpanded ? "조건 접기 ▲" : "조건 보기 ▼"}
                </button>

                {/* 조건 아코디언 */}
                {isExpanded && (
                  <div className="mt-4 space-y-3 border-t border-gray-200 pt-4">
                    {strategy.conditions.map((condition, index) => (
                      <div key={index}>
                        <h4 className="text-sm font-semibold text-gray-900">
                          {condition.condition}
                        </h4>
                        <ul className="mt-1 space-y-1">
                          {condition.condition_info.map((info, infoIndex) => (
                            <li
                              key={infoIndex}
                              className="text-xs text-gray-600 ml-4 list-disc"
                            >
                              {info}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 선택 버튼 */}
              <div className="px-5 pb-4">
                <button
                  onClick={() => handleSelectStrategy(strategy.id, strategy.name)}
                  className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
                >
                  이 전략 선택하기
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
