/**
 * 유니버스 관련 타입 정의
 */

export interface UniverseInfo {
  id: string;
  name: string;
  market: string;
  stockCount: number;
  minCap: number;
  maxCap: number | null;
}

export interface UniversesSummaryResponse {
  tradeDate: string | null;
  universes: UniverseInfo[];
}

export interface StockInfo {
  stockCode: string;
  stockName: string;
  marketCap: number;
}

export interface UniverseStocksResponse {
  universeId: string;
  universeName: string;
  stockCount: number;
  stocks: StockInfo[];
}

export interface UniverseStockCountResponse {
  stockCount: number;
  universeIds: string[];
}
