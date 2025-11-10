/**
 * Industry (산업) 관련 API 함수
 * - 매매 대상 설정에서 사용할 산업 및 종목 조회 API
 */

import { axiosInstance } from "../axios";

/**
 * 산업 정보 타입
 */
export interface IndustryInfo {
  industry_name: string;
  stock_count: number;
}

/**
 * 종목 정보 타입
 */
export interface StockInfo {
  stock_code: string;
  stock_name: string;
  company_name: string;
  industry: string;
  market_type?: string;
  current_price?: number;
  change_rate?: number;
}

/**
 * 모든 산업 목록 조회
 * - GET /industries/list
 * - DB에 실제 존재하는 산업만 반환 (활성 종목 기준)
 *
 * @returns 산업 목록 (종목 수 포함)
 */
export async function getIndustries(): Promise<IndustryInfo[]> {
  const response = await axiosInstance.get<IndustryInfo[]>("/industries/list");
  return response.data;
}

/**
 * 특정 산업의 종목 목록 조회
 * - GET /industries/{industry_name}/stocks
 *
 * @param industryName - 산업명
 * @returns 해당 산업에 속한 종목 목록
 */
export async function getStocksByIndustry(
  industryName: string,
): Promise<StockInfo[]> {
  const response = await axiosInstance.get<StockInfo[]>(
    `/industries/${encodeURIComponent(industryName)}/stocks`,
  );
  return response.data;
}

/**
 * 여러 산업의 종목 목록 일괄 조회
 * - POST /industries/stocks-by-industries
 *
 * @param industryNames - 산업명 배열
 * @returns 선택된 산업들에 속한 종목 목록
 */
export async function getStocksByIndustries(
  industryNames: string[],
): Promise<StockInfo[]> {
  const response = await axiosInstance.post<StockInfo[]>(
    "/industries/stocks-by-industries",
    { industries: industryNames },
  );
  return response.data;
}

/**
 * 종목명 또는 종목코드로 검색
 * - GET /industries/search?query={query}
 *
 * @param query - 검색어 (종목명 또는 종목코드)
 * @returns 검색 결과 종목 목록
 */
export async function searchStocks(query: string): Promise<StockInfo[]> {
  if (!query || query.trim() === "") {
    return [];
  }
  const response = await axiosInstance.get<StockInfo[]>(
    `/industries/search?query=${encodeURIComponent(query)}`,
  );
  return response.data;
}
