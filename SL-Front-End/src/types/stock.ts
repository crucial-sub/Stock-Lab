export interface Stock {
  id: number;
  name: string;
  code?: string;
  currentPrice: number;
  changeRate: number;
  tradingVolume: number;
  rank: number;
  symbol?: string;
  isFavorite: boolean;
}

export interface StockFilters {
  sortOrder: "asc" | "desc";
  period: "1d" | "1w" | "1m" | "3m" | "6m" | "1y";
}
