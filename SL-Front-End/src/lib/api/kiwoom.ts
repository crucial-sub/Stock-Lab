/**
 * 키움증권 API 클라이언트
 */

import type {
  AccountBalance,
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
};
