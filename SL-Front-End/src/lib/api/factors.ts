/**
 * 팩터 관련 API 함수
 * - 팩터 목록 조회 API를 제공합니다
 */

import type { Factor } from "@/types/api";
import { axiosInstance, axiosServerInstance } from "../axios";

/**
 * 팩터 목록 조회
 * - GET /api/factors/list
 * - 사용 가능한 모든 팩터 목록을 반환합니다
 *
 * @param isServer - 서버 사이드 요청 여부 (SSR용)
 * @returns 팩터 목록
 */
export async function getFactors(isServer = false): Promise<Factor[]> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<Factor[]>("/api/factors/list");
  return response.data;
}

/**
 * 특정 카테고리의 팩터 조회
 * - GET /api/factors?category={category}
 *
 * @param category - 팩터 카테고리
 * @param isServer - 서버 사이드 요청 여부
 * @returns 해당 카테고리의 팩터 목록
 */
export async function getFactorsByCategory(
  category: string,
  isServer = false,
): Promise<Factor[]> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<Factor[]>("/api/factors", {
    params: { category },
  });
  return response.data;
}

/**
 * 특정 팩터 상세 조회
 * - GET /api/factors/{factorId}
 *
 * @param factorId - 팩터 ID
 * @param isServer - 서버 사이드 요청 여부
 * @returns 팩터 상세 정보
 */
export async function getFactorById(
  factorId: string,
  isServer = false,
): Promise<Factor> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<Factor>(`/api/factors/${factorId}`);
  return response.data;
}
