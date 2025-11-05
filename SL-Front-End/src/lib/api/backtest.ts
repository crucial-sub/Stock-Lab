/**
 * 백테스트 관련 API 함수
 * - 백테스트 실행, 결과 조회 API를 제공합니다
 */

import { axiosInstance, axiosServerInstance } from "../axios";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  BacktestResult,
  PaginatedResponse,
  PaginationParams,
} from "@/types/api";

/**
 * 백테스트 실행
 * - POST /backtest/run
 * - 조건을 기반으로 백테스트를 시작합니다
 *
 * @param request - 백테스트 실행 요청 데이터
 * @returns 백테스트 실행 응답 (백테스트 ID 포함)
 */
export async function runBacktest(
  request: BacktestRunRequest,
): Promise<BacktestRunResponse> {
  const response = await axiosInstance.post<BacktestRunResponse>(
    "/backtest/run",
    request,
  );
  return response.data;
}

/**
 * 백테스트 결과 조회
 * - GET /backtest/{backtestId}
 * - 완료된 백테스트의 결과를 조회합니다
 *
 * @param backtestId - 백테스트 ID
 * @param isServer - 서버 사이드 요청 여부 (SSR용)
 * @returns 백테스트 결과 상세 정보
 */
export async function getBacktestResult(
  backtestId: string,
  isServer = false,
): Promise<BacktestResult> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<BacktestResult>(
    `/backtest/${backtestId}/result`,
  );
  return response.data;
}

/**
 * 백테스트 목록 조회
 * - GET /backtest
 * - 사용자의 백테스트 목록을 조회합니다
 *
 * @param params - 페이지네이션 파라미터
 * @param isServer - 서버 사이드 요청 여부
 * @returns 백테스트 목록 (페이지네이션 포함)
 */
export async function getBacktestList(
  params?: PaginationParams,
  isServer = false,
): Promise<PaginatedResponse<BacktestResult>> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<PaginatedResponse<BacktestResult>>(
    "/backtest",
    { params },
  );
  return response.data;
}

/**
 * 백테스트 매매 내역 조회 (페이지네이션)
 * - GET /backtest/{backtestId}/trades
 * - 특정 백테스트의 매매 내역을 페이지네이션으로 조회합니다
 * - 대용량 데이터 처리를 위해 사용합니다
 *
 * @param backtestId - 백테스트 ID
 * @param params - 페이지네이션 파라미터
 * @param isServer - 서버 사이드 요청 여부
 * @returns 매매 내역 목록 (페이지네이션 포함)
 */
export async function getBacktestTrades(
  backtestId: string,
  params?: PaginationParams,
  isServer = false,
): Promise<
  PaginatedResponse<BacktestResult["trades"][number]>
> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<
    PaginatedResponse<BacktestResult["trades"][number]>
  >(`/backtest/${backtestId}/trades`, { params });
  return response.data;
}

/**
 * 백테스트 수익률 차트 데이터 조회 (페이지네이션)
 * - GET /backtest/{backtestId}/yield-points
 * - 특정 백테스트의 수익률 차트 데이터를 페이지네이션으로 조회합니다
 * - 5년치 대용량 데이터 처리를 위해 사용합니다
 *
 * @param backtestId - 백테스트 ID
 * @param params - 페이지네이션 파라미터
 * @param isServer - 서버 사이드 요청 여부
 * @returns 수익률 차트 데이터 (페이지네이션 포함)
 */
export async function getBacktestYieldPoints(
  backtestId: string,
  params?: PaginationParams,
  isServer = false,
): Promise<
  PaginatedResponse<BacktestResult["yieldPoints"][number]>
> {
  const axios = isServer ? axiosServerInstance : axiosInstance;

  const response = await axios.get<
    PaginatedResponse<BacktestResult["yieldPoints"][number]>
  >(`/backtest/${backtestId}/yield-points`, { params });
  return response.data;
}

/**
 * 백테스트 상태 확인
 * - GET /backtest/{backtestId}/status
 * - 백테스트 실행 상태를 확인합니다 (폴링용)
 *
 * @param backtestId - 백테스트 ID
 * @returns 백테스트 상태 정보
 */
export async function getBacktestStatus(backtestId: string): Promise<{
  status: BacktestResult["status"];
  progress?: number;
}> {
  const response = await axiosInstance.get<{
    status: BacktestResult["status"];
    progress?: number;
  }>(`/backtest/${backtestId}/status`);
  return response.data;
}

/**
 * 백테스트 삭제
 * - DELETE /backtest/{backtestId}
 *
 * @param backtestId - 백테스트 ID
 */
export async function deleteBacktest(backtestId: string): Promise<void> {
  await axiosInstance.delete(`/backtest/${backtestId}`);
}
