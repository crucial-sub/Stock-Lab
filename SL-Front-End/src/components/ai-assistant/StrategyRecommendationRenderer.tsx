/**
 * StrategyRecommendationRenderer 컴포넌트
 *
 * @description 추천된 투자 전략을 아코디언 형식으로 표시합니다.
 * - 전략 이름, 요약, 매칭 점수 표시
 * - 아코디언 확장 시 상세 설명 및 조건 표시
 * - 조건 토글 기능 제공
 */

"use client";

import { useState } from "react";
import type { StrategyMatch } from "@/utils/strategyMatcher";
import { getTagLabel } from "@/data/assistantQuestionnaire";

// ============================================================================
// 타입 정의
// ============================================================================

interface StrategyRecommendationRendererProps {
  /** 추천된 전략 매칭 결과 배열 */
  recommendations: StrategyMatch[];
  /** 전략 선택 시 호출되는 콜백 함수 */
  onSelectStrategy?: (strategyId: string, strategyName: string) => void;
}

// ============================================================================
// 전략 카드 컴포넌트
// ============================================================================

interface StrategyCardProps {
  match: StrategyMatch;
  rank: number;
  onSelect?: (strategyId: string, strategyName: string) => void;
}

function StrategyCard({ match, rank, onSelect }: StrategyCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedConditions, setExpandedConditions] = useState<Set<number>>(new Set());

  const { strategy, matchScore, matchedTags } = match;

  // 조건 토글 핸들러
  const toggleCondition = (index: number) => {
    setExpandedConditions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // 매칭 점수에 따른 색상
  const getScoreColor = (score: number): string => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-blue-600";
    if (score >= 40) return "text-yellow-600";
    return "text-gray-600";
  };

  // 순위 배지 색상
  const getRankBadgeColor = (rank: number): string => {
    if (rank === 1) return "bg-yellow-500";
    if (rank === 2) return "bg-gray-400";
    if (rank === 3) return "bg-amber-700";
    return "bg-blue-500";
  };

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white shadow-sm hover:shadow-md transition-shadow">
      {/* 전략 헤더 (클릭 가능) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-4 flex-1">
          {/* 순위 배지 */}
          <div
            className={`${getRankBadgeColor(rank)} text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-sm flex-shrink-0`}
          >
            {rank}
          </div>

          <div className="flex-1 min-w-0">
            {/* 전략 이름 */}
            <h3 className="font-bold text-lg text-gray-900 mb-1">
              {strategy.name}
            </h3>

            {/* 전략 요약 */}
            <p className="text-sm text-gray-600 line-clamp-1">
              {strategy.summary}
            </p>
          </div>
        </div>

        {/* 매칭 점수 및 확장 아이콘 */}
        <div className="flex items-center gap-3 flex-shrink-0 ml-4">
          {/* 매칭 점수 */}
          <div className="text-right">
            <p className={`text-2xl font-bold ${getScoreColor(matchScore)}`}>
              {matchScore}%
            </p>
            <p className="text-xs text-gray-500">
              매칭률
            </p>
          </div>

          {/* 확장/축소 아이콘 */}
          <svg
            className={`w-6 h-6 text-gray-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* 전략 상세 (확장 시 표시) */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          {/* 매칭된 태그 */}
          {matchedTags.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-semibold text-gray-700 mb-2">
                🎯 매칭된 투자 성향:
              </p>
              <div className="flex flex-wrap gap-2">
                {matchedTags.map(tag => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium"
                  >
                    {getTagLabel(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 전략 상세 설명 */}
          <div className="mb-4">
            <p className="text-sm font-semibold text-gray-700 mb-2">
              📋 전략 설명:
            </p>
            <p className="text-sm text-gray-600 whitespace-pre-line">
              {strategy.description}
            </p>
          </div>

          {/* 전략 조건 */}
          {strategy.conditions.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">
                ⚙️ 전략 조건 ({strategy.conditions.length}개):
              </p>
              <div className="space-y-2">
                {strategy.conditions.map((condition, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg overflow-hidden bg-white"
                  >
                    {/* 조건 헤더 */}
                    <button
                      onClick={() => toggleCondition(index)}
                      className="w-full px-3 py-2 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-xs font-mono text-gray-500 flex-shrink-0">
                          #{index + 1}
                        </span>
                        <span className="text-sm text-gray-700 flex-1">
                          {condition.condition}
                        </span>
                      </div>

                      {/* 확장/축소 아이콘 */}
                      {condition.condition_info.length > 0 && (
                        <svg
                          className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ml-2 ${expandedConditions.has(index) ? "rotate-180" : ""}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </button>

                    {/* 조건 설명 (확장 시) */}
                    {expandedConditions.has(index) && condition.condition_info.length > 0 && (
                      <div className="px-3 py-2 border-t border-gray-200 bg-gray-50">
                        {condition.condition_info.map((info, infoIndex) => (
                          <p key={infoIndex} className="text-xs text-gray-600 mb-1 last:mb-0">
                            {info}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 전략 선택 버튼 */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (onSelect) {
                  onSelect(strategy.id, strategy.name);
                }
              }}
              className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
            >
              이 전략 선택하기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 메인 컴포넌트
// ============================================================================

/**
 * StrategyRecommendationRenderer
 *
 * @description 추천된 투자 전략 목록을 렌더링하는 컴포넌트
 */
export function StrategyRecommendationRenderer({
  recommendations,
  onSelectStrategy,
}: StrategyRecommendationRendererProps) {
  if (recommendations.length === 0) {
    return (
      <div className="w-full max-w-[800px] mx-auto p-6 text-center">
        <p className="text-gray-500">추천 가능한 전략이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[800px] mx-auto mb-6">
      {/* 제목 */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">
          🎯 맞춤형 투자 전략 추천
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          입력하신 투자 성향에 가장 적합한 전략을 추천해드립니다.
        </p>
      </div>

      {/* 전략 카드 리스트 */}
      <div className="space-y-0">
        {recommendations.map((match, index) => (
          <StrategyCard
            key={match.strategy.id}
            match={match}
            rank={index + 1}
            onSelect={onSelectStrategy}
          />
        ))}
      </div>

      {/* 안내 문구 */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          💡 <strong>TIP:</strong> 각 전략을 클릭하면 상세 설명과 조건을 확인할 수 있습니다.
          조건을 다시 클릭하면 더 자세한 설명을 볼 수 있습니다.
        </p>
      </div>
    </div>
  );
}
