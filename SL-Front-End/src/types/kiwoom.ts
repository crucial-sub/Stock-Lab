/**
 * 키움증권 API 타입 정의
 */

export interface KiwoomCredentials {
  app_key: string;
  app_secret: string;
}

export interface KiwoomCredentialsResponse {
  message: string;
  access_token: string;
  expires_at: string;
}

export interface KiwoomStatusResponse {
  is_connected: boolean;
  expires_at: string | null;
}

export interface AccountBalance {
  data: any;
  message: string;
}

export interface StockOrder {
  stock_code: string;
  quantity: string;
  price?: string;
  trade_type?: string;
  dmst_stex_tp?: string;
}

export interface StockOrderResponse {
  data: any;
  message: string;
}
