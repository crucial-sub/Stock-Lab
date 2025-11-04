/**
 * 테마 관련 API 테마
 * - 테마 목록 조회 API를 제공합니다
 */

import type { Themes } from "@/types/api";
import { axiosInstance, axiosServerInstance } from "../axios";

/**
 * 테마 목록 조회
 * - GET /themes/list
 * - 사용 가능한 모든 테마 목록을 반환합니다
 *
 * @param isServer - 서버 사이드 요청 여부 (SSR용)
 * @returns 테마 목록
 */
export async function getThemes(isServer = false): Promise<Themes[]> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<{ sectors: Themes[] }>("/themes/list");
  return response.data.sectors;
}

/**
 * 특정 테마 상세 조회
 * - GET /api/themes/{subFactorId}
 *
 * @param themeId - 테마 ID
 * @param isServer - 서버 사이드 요청 여부
 * @returns 테마 상세 정보
 */
export async function getThemesById(
  themeId: string,
  isServer = false,
): Promise<Themes> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<Themes>(`/themes/${themeId}`);
  return response.data;
}
