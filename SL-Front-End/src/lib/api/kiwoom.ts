/**
 * 키움증권 API 클라이언트
 */

import type {
  AccountBalance,
  AccountPerformanceChart,
  KiwoomCredentials,
  KiwoomCredentialsResponse,
  KiwoomStatusResponse,
  StockOrder,
  StockOrderResponse,
} from "@/types/kiwoom";
import { axiosInstance } from "../axios";

export const kiwoomApi = {
  /**
   * 키움증권 API KEY 등록
   */
  registerCredentials: async (
    credentials: KiwoomCredentials,
  ): Promise<KiwoomCredentialsResponse> => {
    const { data } = await axiosInstance.post<KiwoomCredentialsResponse>(
      "/kiwoom/credentials",
      credentials,
    );
    return data;
  },

  /**
   * 키움증권 연동 상태 조회
   */
  getStatus: async (): Promise<KiwoomStatusResponse> => {
    const { data } = await axiosInstance.get<KiwoomStatusResponse>(
      "/kiwoom/credentials/status",
    );
    return data;
  },

  /**
   * 키움증권 연동 해제
   */
  deleteCredentials: async (): Promise<{ message: string }> => {
    const { data } = await axiosInstance.delete<{ message: string }>(
      "/kiwoom/credentials",
    );
    return data;
  },

  /**
   * 계좌 잔고 조회
   */
  getAccountBalance: async (): Promise<AccountBalance> => {
    const { data } = await axiosInstance.get<AccountBalance>(
      "/kiwoom/account/balance",
    );
    return data;
  },

  /**
   * 주식 매수 주문
   */
  buyStock: async (order: StockOrder): Promise<StockOrderResponse> => {
    const { data } = await axiosInstance.post<StockOrderResponse>(
      "/kiwoom/order/buy",
      order,
    );
    return data;
  },

  /**
   * 주식 매도 주문
   */
  sellStock: async (order: StockOrder): Promise<StockOrderResponse> => {
    const { data } = await axiosInstance.post<StockOrderResponse>(
      "/kiwoom/order/sell",
      order,
    );
    return data;
  },

  /**
   * 키움증권 연동 상태 조회 (서버 사이드)
   */
  getStatusServer: async (token: string): Promise<KiwoomStatusResponse> => {
    const axios = (await import("axios")).default;
    const baseURL = process.env.API_BASE_URL?.replace('/api/v1', '') || "http://backend:8000";
    const { data } = await axios.get<KiwoomStatusResponse>(
      `${baseURL}/api/v1/kiwoom/credentials/status`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return data;
  },

  /**
   * 계좌 잔고 조회 (서버 사이드)
   */
  getAccountBalanceServer: async (token: string): Promise<AccountBalance> => {
    const axios = (await import("axios")).default;
    const baseURL = process.env.API_BASE_URL?.replace('/api/v1', '') || "http://backend:8000";
    const { data } = await axios.get<AccountBalance>(
      `${baseURL}/api/v1/kiwoom/account/balance`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return data;
  },

  /**
   * 계좌 성과 차트 데이터 조회
   */
  getPerformanceChart: async (days: number = 30): Promise<AccountPerformanceChart> => {
    const { data } = await axiosInstance.get<AccountPerformanceChart>(
      `/kiwoom/account/performance-chart?days=${days}`,
    );
    return data;
  },

  /**
   * 계좌 성과 차트 데이터 조회 (서버 사이드)
   */
  getPerformanceChartServer: async (
    token: string,
    days: number = 30
  ): Promise<AccountPerformanceChart> => {
    const axios = (await import("axios")).default;
    const baseURL = process.env.API_BASE_URL?.replace('/api/v1', '') || "http://backend:8000";
    const { data } = await axios.get<AccountPerformanceChart>(
      `${baseURL}/api/v1/kiwoom/account/performance-chart?days=${days}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      },
    );
    return data;
  },
};
