/**
 * 함수 관련 API 함수
 * - 함수 목록 조회 API를 제공합니다
 */

import type { SubFactor } from "@/types/api";
import { axiosInstance, axiosServerInstance } from "../axios";

/**
 * 함수 목록 조회
 * - GET /api/sub-factors/list
 * - 사용 가능한 모든 함수 목록을 반환합니다
 *
 * @param isServer - 서버 사이드 요청 여부 (SSR용)
 * @returns 함수 목록
 */
export async function getSubFactors(isServer = false): Promise<SubFactor[]> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<SubFactor[]>("/api/sub-factors/list");
  return response.data;
}

/**
 * 특정 함수 상세 조회
 * - GET /api/sub-factors/{subFactorId}
 *
 * @param subFactorId - 함수 ID
 * @param isServer - 서버 사이드 요청 여부
 * @returns 함수 상세 정보
 */
export async function getSubFactorById(
  subFactorId: string,
  isServer = false,
): Promise<SubFactor> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<SubFactor>(`/api/sub-factors/${subFactorId}`);
  return response.data;
}
