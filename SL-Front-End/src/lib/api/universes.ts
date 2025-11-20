/**
 * Universe (유니버스) 관련 API 함수
 * - 시가총액 기준 종목 그룹 조회 API
 */

import { axiosInstance } from "../axios";
import type {
  UniversesSummaryResponse,
  UniverseStocksResponse,
  UniverseStockCountResponse,
} from "@/types/universe";

/**
 * 모든 유니버스 요약 정보 조회
 * - GET /universes
 * - 코스피/코스닥별 시가총액 구간별 종목 수 조회
 *
 * @returns 유니버스 요약 정보
 */
export async function getUniversesSummary(): Promise<UniversesSummaryResponse> {
  const response =
    await axiosInstance.get<UniversesSummaryResponse>("/universes");
  return response.data;
}

/**
 * 특정 유니버스의 종목 목록 조회
 * - GET /universes/{universeId}/stocks
 *
 * @param universeId - 유니버스 ID (예: "KOSPI_MEGA", "KOSDAQ_LARGE")
 * @param limit - 최대 조회 종목 수 (선택)
 * @returns 해당 유니버스에 속한 종목 목록
 */
export async function getUniverseStocks(
  universeId: string,
  limit?: number,
): Promise<UniverseStocksResponse> {
  const params = limit ? { limit } : {};
  const response = await axiosInstance.get<UniverseStocksResponse>(
    `/universes/${universeId}/stocks`,
    { params },
  );
  return response.data;
}

/**
 * 선택된 유니버스들의 종목 수 조회
 * - POST /universes/stock-count
 * - 여러 유니버스에 속한 종목 수를 계산 (중복 제거)
 *
 * @param universeIds - 유니버스 ID 배열
 * @returns 총 종목 수
 */
export async function getUniverseStockCount(
  universeIds: string[],
): Promise<UniverseStockCountResponse> {
  const response = await axiosInstance.post<UniverseStockCountResponse>(
    "/universes/stock-count",
    { universeIds },
  );
  return response.data;
}
