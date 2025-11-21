/**
 * 투자 전략 추천 API 함수
 * - AI 어시스턴트에서 사용자 설문 결과 기반 전략 추천
 * - 전략 상세 정보 조회 (백테스트 실행용)
 */

import type {
  StrategyRecommendationRequest,
  StrategyMatch,
  StrategyDetail,
} from "@/types/investment-strategy";
import { axiosInstance } from "../axios";

/**
 * 전략 추천
 * - POST /api/v1/strategies/recommend
 * - 사용자 설문 결과 태그를 기반으로 매칭되는 전략 추천
 *
 * @param request - 추천 요청 (user_tags, top_n)
 * @returns 추천된 전략 목록 (매칭 점수 포함)
 *
 * @example
 * ```ts
 * const recommendations = await recommendStrategies({
 *   user_tags: ['long_term', 'style_value', 'risk_low'],
 *   top_n: 3
 * });
 * ```
 */
export async function recommendStrategies(
  request: StrategyRecommendationRequest,
): Promise<StrategyMatch[]> {
  const response = await axiosInstance.post<StrategyMatch[]>(
    "/strategies/recommend",
    request,
  );
  return response.data;
}

/**
 * 전략 상세 정보 조회
 * - GET /api/v1/strategies/{strategyId}
 * - 백테스트 실행에 필요한 전체 설정 포함
 * - 조회 시 인기도 점수 자동 증가
 *
 * @param strategyId - 전략 ID
 * @returns 전략 상세 정보 (backtest_config 포함)
 *
 * @example
 * ```ts
 * const strategy = await getStrategyDetail('warren_buffett');
 * const backtestRequest = {
 *   ...strategy.backtest_config,
 *   user_id: currentUser.id,
 *   initial_investment: 5000,
 *   start_date: '20220101',
 *   end_date: '20250101',
 * };
 * ```
 */
export async function getStrategyDetail(
  strategyId: string,
): Promise<StrategyDetail> {
  const response = await axiosInstance.get<StrategyDetail>(
    `/strategies/${strategyId}`,
  );
  return response.data;
}
