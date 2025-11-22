import { axiosInstance } from "../axios";

export interface MarketQuoteItem {
  rank: number;
  name: string;
  code: string;
  theme?: string | null;
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

export type SortBy =
  | "volume"
  | "change_rate"
  | "trading_value"
  | "market_cap"
  | "name";
export type SortOrder = "asc" | "desc";

// 관심 종목 관련 타입
export interface FavoriteStockItem {
  stockCode: string;
  stockName: string;
  theme?: string | null;
  currentPrice: number | null;
  changeRate: number | null;
  previousClose: number | null;
  volume: number | null;
  tradingValue: number | null;
  marketCap: number | null;
  createdAt: string;
}

export interface FavoriteStockListResponse {
  items: FavoriteStockItem[];
  total: number;
}

// 최근 본 종목 관련 타입
export interface RecentStockItem {
  stockCode: string;
  stockName: string;
  currentPrice: number | null;
  changeRate: number | null;
  previousClose: number | null;
  volume: number | null;
  tradingValue: number | null;
  marketCap: number | null;
  viewedAt: string;
}

export interface RecentStockListResponse {
  items: RecentStockItem[];
  total: number;
}

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
    search?: string;
  }): Promise<MarketQuoteListResponse> => {
    const { data } = await axiosInstance.get<MarketQuoteListResponse>(
      "/market/quotes",
      {
        params: {
          sort_by: params.sortBy || "market_cap",
          sort_order: params.sortOrder || "desc",
          page: params.page || 1,
          page_size: params.pageSize || 50,
          user_id: params.userId,
          search: params.search,
        },
      },
    );
    return data;
  },

  /**
   * 관심 종목 목록 조회
   */
  getFavorites: async (): Promise<FavoriteStockListResponse> => {
    const { data } =
      await axiosInstance.get<FavoriteStockListResponse>("/market/favorites");
    return data;
  },

  /**
   * 관심 종목 추가
   */
  addFavorite: async (stockCode: string): Promise<void> => {
    await axiosInstance.post("/market/favorites", { stock_code: stockCode });
  },

  /**
   * 관심 종목 삭제
   */
  removeFavorite: async (stockCode: string): Promise<void> => {
    await axiosInstance.delete(`/market/favorites/${stockCode}`);
  },

  /**
   * 최근 본 종목 목록 조회
   */
  getRecentViewed: async (): Promise<RecentStockListResponse> => {
    const { data } = await axiosInstance.get<RecentStockListResponse>(
      "/market/recent-viewed",
    );
    return data;
  },

  /**
   * 최근 본 종목 추가 (자동 기록)
   */
  addRecentViewed: async (stockCode: string): Promise<void> => {
    await axiosInstance.post(`/market/recent-viewed/${stockCode}`);
  },

  /**
   * 최근 본 종목 삭제 (수동 삭제)
   */
  removeRecentViewed: async (stockCode: string): Promise<void> => {
    await axiosInstance.delete(`/market/recent-viewed/${stockCode}`);
  },
};
