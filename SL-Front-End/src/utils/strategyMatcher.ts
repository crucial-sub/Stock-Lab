/**
 * 투자 전략 매칭 유틸리티
 *
 * @description 유저의 설문 답변 태그와 전략 태그를 비교하여 매칭 점수 계산
 */

import strategiesData from "@/data/investmentStrategies.json";

// ============================================================================
// 타입 정의
// ============================================================================

/**
 * 투자 전략 인터페이스
 */
export interface InvestmentStrategy {
  id: string;
  name: string;
  summary: string;
  description: string;
  tags: string[];
  conditions: StrategyCondition[];
}

/**
 * 전략 조건 인터페이스
 */
export interface StrategyCondition {
  condition: string;
  conditionInfo: string[];
}

/**
 * 매칭 결과 인터페이스
 */
export interface StrategyMatch {
  strategy: InvestmentStrategy;
  matchScore: number;
  matchedTags: string[];
  unmatchedTags: string[];
}

// ============================================================================
// 매칭 알고리즘
// ============================================================================

/**
 * 태그 매칭 점수 계산
 *
 * @param userTags - 유저의 설문 답변 태그 배열
 * @param strategyTags - 전략의 태그 배열
 * @returns 매칭 점수 (0-100)
 *
 * @description
 * matchScore = (일치하는 태그 개수 / 유저 답변 태그 개수) * 100
 */
function calculateMatchScore(userTags: string[], strategyTags: string[]): number {
  if (userTags.length === 0) return 0;

  const matchedCount = userTags.filter(tag => strategyTags.includes(tag)).length;
  const score = (matchedCount / userTags.length) * 100;

  return Math.round(score);
}

/**
 * 매칭된 태그와 매칭되지 않은 태그 추출
 *
 * @param userTags - 유저의 설문 답변 태그 배열
 * @param strategyTags - 전략의 태그 배열
 * @returns 매칭된 태그와 매칭되지 않은 태그 배열
 */
function getMatchedTags(
  userTags: string[],
  strategyTags: string[]
): { matchedTags: string[]; unmatchedTags: string[] } {
  const matchedTags = userTags.filter(tag => strategyTags.includes(tag));
  const unmatchedTags = userTags.filter(tag => !strategyTags.includes(tag));

  return { matchedTags, unmatchedTags };
}

/**
 * 모든 전략에 대한 매칭 점수 계산
 *
 * @param userTags - 유저의 설문 답변 태그 배열
 * @returns 매칭 결과 배열 (점수 내림차순, 동점 시 ID 순 정렬)
 */
export function calculateAllMatches(userTags: string[]): StrategyMatch[] {
  const strategies = strategiesData.strategies as InvestmentStrategy[];

  const matches: StrategyMatch[] = strategies.map(strategy => {
    const matchScore = calculateMatchScore(userTags, strategy.tags);
    const { matchedTags, unmatchedTags } = getMatchedTags(userTags, strategy.tags);

    return {
      strategy,
      matchScore,
      matchedTags,
      unmatchedTags,
    };
  });

  // 정렬: 점수 내림차순, 동점 시 ID 오름차순
  matches.sort((a, b) => {
    if (b.matchScore !== a.matchScore) {
      return b.matchScore - a.matchScore;
    }
    return a.strategy.id.localeCompare(b.strategy.id);
  });

  return matches;
}

/**
 * 상위 N개 전략 추천
 *
 * @param userTags - 유저의 설문 답변 태그 배열
 * @param topN - 추천할 전략 개수 (기본값: 3)
 * @returns 상위 N개 매칭 결과 배열
 *
 * @description
 * - 최소 3개 추천 보장
 * - 점수가 낮아도 최소 topN개는 반환
 */
export function getTopRecommendations(
  userTags: string[],
  topN: number = 3
): StrategyMatch[] {
  const allMatches = calculateAllMatches(userTags);

  // 최소 topN개 보장
  const minRecommendations = Math.max(topN, 3);

  return allMatches.slice(0, minRecommendations);
}

/**
 * 특정 전략의 매칭 점수 조회
 *
 * @param userTags - 유저의 설문 답변 태그 배열
 * @param strategyId - 조회할 전략 ID
 * @returns 매칭 결과 (전략을 찾을 수 없으면 null)
 */
export function getStrategyMatch(
  userTags: string[],
  strategyId: string
): StrategyMatch | null {
  const strategies = strategiesData.strategies as InvestmentStrategy[];
  const strategy = strategies.find(s => s.id === strategyId);

  if (!strategy) return null;

  const matchScore = calculateMatchScore(userTags, strategy.tags);
  const { matchedTags, unmatchedTags } = getMatchedTags(userTags, strategy.tags);

  return {
    strategy,
    matchScore,
    matchedTags,
    unmatchedTags,
  };
}

/**
 * 전략 ID로 전략 조회
 *
 * @param strategyId - 조회할 전략 ID
 * @returns 전략 객체 (찾을 수 없으면 undefined)
 */
export function getStrategyById(strategyId: string): InvestmentStrategy | undefined {
  const strategies = strategiesData.strategies as InvestmentStrategy[];
  return strategies.find(s => s.id === strategyId);
}

/**
 * 모든 전략 조회
 *
 * @returns 모든 전략 배열
 */
export function getAllStrategies(): InvestmentStrategy[] {
  return strategiesData.strategies as InvestmentStrategy[];
}
