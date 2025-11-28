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
import { Icon } from "@/components/common/Icon";
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
    if (score >= 80) return "text-price-up";
    if (score >= 60) return "text-brand-purple";
    if (score >= 40) return "text-price-down";
    return "text-muted";
  };

  // 순위 배지 색상
  const getRankBadgeColor = (rank: number): string => {
    if (rank === 1) return "bg-[#FFB330]";
    if (rank === 2) return "bg-gray-400";
    if (rank === 3) return "bg-[#AF7005]";
    return "bg-brand-purple/10";
  };

  return (
    <div className="border-[0.5px] border-[#18233433] rounded-[12px] overflow-hidden mb-4 bg-[#1822340D] shadow-elev-card-soft">
      {/* 전략 헤더 (클릭 가능) */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-5 flex items-center justify-between hover:bg-white/40 transition-colors text-left"
      >
        <div className="flex items-center gap-4">
          {/* 순위 배지 */}
          <div
            className={`${getRankBadgeColor(rank)} text-white rounded-[12px] w-8 h-8 flex items-center justify-center font-semibold text-[1rem]`}
          >
            {rank}
          </div>

          <div className="">
            {/* 전략 이름 */}
            <h3 className="font-semibold text-[1.25rem] text-black">
              {strategy.name}
            </h3>

            {/* 전략 요약 */}
            <p className="text-[0.875rem] text-muted">
              {strategy.summary}
            </p>
          </div>
        </div>

        {/* 매칭 점수 및 확장 아이콘 */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {/* 매칭 점수 */}
          <div className="text-right">
            <p className={`text-[1.25rem] font-semibold ${getScoreColor(matchScore)}`}>
              {matchScore}%
            </p>
            <p className="text-[0.875rem] text-muted">
              적합률
            </p>
          </div>

          {/* 확장/축소 아이콘 */}
          <Icon
            src={isExpanded ? "/icons/arrow_up.svg" : "/icons/arrow_down.svg"}
            alt={isExpanded ? "접기" : "펼치기"}
            size={28}
            className="text-muted transition-transform"
          />
        </div>
      </button>

      {/* 전략 상세 (확장 시 표시) */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-5 bg-white/40">
          {/* 매칭된 태그 */}
          {matchedTags.length > 0 && (
            <div className="mb-5">
              <p className="text-[1.125rem] font-semibold text-black mb-2">
                ✔︎ 투자 성향
              </p>
              <div className="flex flex-wrap gap-2">
                {matchedTags.map(tag => (
                  <span
                    key={tag}
                    className="px-3 py-1 text-[0.75rem] font-semibold bg-brand-purple/20 text-brand-purple rounded-full"
                  >
                    {getTagLabel(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 전략 상세 설명 */}
          <div className="mb-4">
            <p className="text-[1rem] font-semibold text-body mb-1">
              📋 전략 설명
            </p>
            <p className="text-[0.85rem] text-body">
              {strategy.description}
            </p>
          </div>

          {/* 전략 조건 */}
          {strategy.conditions.length > 0 && (
            <div>
              <p className="text-[1rem] font-semibold text-body mb-1">
                ⚙️ 필요 조건 ({strategy.conditions.length}개)
              </p>
              <div className="space-y-1">
                {strategy.conditions.map((condition, index) => (
                  <div
                    key={index}
                    className="border-[1px] border-brand-purple/30 rounded-[12px] overflow-hidden bg-white/20"
                  >
                    {/* 조건 헤더 */}
                    <button
                      onClick={() => toggleCondition(index)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-white transition-colors text-left"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="text-[0.875rem] text-body font-normal">
                          #{index + 1}
                        </span>
                        <span className="text-[0.875rem] text-body">
                          {condition.condition}
                        </span>
                      </div>

                      {/* 확장/축소 아이콘 */}
                      {condition.condition_info.length > 0 && (
                        <Icon
                          src={expandedConditions.has(index) ? "/icons/arrow_up.svg" : "/icons/arrow_down.svg"}
                          alt={expandedConditions.has(index) ? "조건 접기" : "조건 펼치기"}
                          className="ml-2 text-muted"
                          size={20}
                        />
                      )}
                    </button>

                    {/* 조건 설명 (확장 시) */}
                    {expandedConditions.has(index) && condition.condition_info.length > 0 && (
                      <div className="px-4 py-3 bg-white/20">
                        {condition.condition_info.map((info, infoIndex) => (
                          <p key={infoIndex} className="text-[0.875rem] text-black">
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
              className="w-full py-3 bg-brand-purple text-[1.125rem] text-white rounded-[12px] font-semibold hover:opacity-80 transition-colors"
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
      <div className="w-full max-w-[1000px] mx-auto p-6 text-center">
        <p className="text-muted">추천 가능한 전략이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1000px] mx-auto mb-5">
      {/* 제목 */}
      <div className="mb-5">
        <span className="text-[1.5rem] font-semibold text-black">
          🎯 맞춤형 투자 전략 추천
        </span>
        <p className="text-[1rem] text-muted mt-1">
          입력하신 투자 성향에 가장 적합한 전략을 추천해드립니다.
        </p>
      </div>

      {/* 전략 카드 리스트 */}
      <div className="space-y-5">
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
      <div className="mt-10 p-5 bg-brand-purple/10 border border-brand-purple rounded-[12px]">
        <p className="text-[1rem] font-semibold text-brand-purple">
          <strong>TIP:</strong> 각 전략을 클릭하면 상세 설명과 조건을 확인할 수 있습니다. 조건을 다시 클릭하면 더 자세한 설명을 볼 수 있습니다.
        </p>
      </div>
    </div>
  );
}
