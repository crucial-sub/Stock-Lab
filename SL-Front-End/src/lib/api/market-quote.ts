import { axiosInstance } from "../axios";

export interface MarketQuoteItem {
  rank: number;
  name: string;
  code: string;
  price: number;
  changeAmount: number;
  changeRate: number;
  trend: "up" | "down" | "flat";
  volume: number;
  tradingValue: number;
  marketCap: number | null;
  isFavorite: boolean;
}

export interface MarketQuoteListResponse {
  items: MarketQuoteItem[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

export type SortBy = "volume" | "change_rate" | "trading_value" | "market_cap" | "name";
export type SortOrder = "asc" | "desc";

export const marketQuoteApi = {
  /**
   * 시세 페이지 데이터 조회
   */
  getMarketQuotes: async (params: {
    sortBy?: SortBy;
    sortOrder?: SortOrder;
    page?: number;
    pageSize?: number;
    userId?: string;
  }): Promise<MarketQuoteListResponse> => {
    const { data } = await axiosInstance.get<MarketQuoteListResponse>("/market/quotes", {
      params: {
        sort_by: params.sortBy || "market_cap",
        sort_order: params.sortOrder || "desc",
        page: params.page || 1,
        page_size: params.pageSize || 50,
        user_id: params.userId,
      },
    });
    return data;
  },
};
