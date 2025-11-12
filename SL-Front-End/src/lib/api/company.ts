import { axiosInstance } from "../axios";

export interface CompanyBasicInfo {
  companyName: string;
  stockCode: string;
  stockName?: string;
  marketType?: string;
  currentPrice?: number;
  tradeDate?: string;
  previousClose?: number;
  changevs1d?: number;
  changevs1w?: number;
  changevs1m?: number;
  changevs2m?: number;
  fluctuationRate?: number;
  changeRate1d?: number;
  changeRate1w?: number;
  changeRate1m?: number;
  changeRate2m?: number;
  marketCap?: number;
  listedShares?: number;
  ceoName?: string;
  listedDate?: string;
  industry?: string;
  isFavorite: boolean;
}

export interface InvestmentIndicators {
  per?: number;
  psr?: number;
  pbr?: number;
  pcr?: number;
}

export interface ProfitabilityIndicators {
  eps?: number;
  bps?: number;
  roe?: number;
  roa?: number;
}

export interface FinancialRatios {
  debtRatio?: number;
  currentRatio?: number;
}

export interface QuarterlyPerformance {
  period: string;
  revenue?: number;
  operatingIncome?: number;
  netIncome?: number;
  netProfitMargin?: number;
  netIncomeGrowth?: number;
  operatingMargin?: number;
  operatingIncomeGrowth?: number;
}

export interface IncomeStatementData {
  period: string;
  revenue?: number;
  operatingIncome?: number;
  netIncome?: number;
  operatingMargin?: number;
  netProfitMargin?: number;
}

export interface BalanceSheetData {
  period: string;
  totalAssets?: number;
  totalLiabilities?: number;
  totalEquity?: number;
  currentAssets?: number;
  currentLiabilities?: number;
}

export interface PriceHistoryPoint {
  date: string;
  closePrice?: number;
  openPrice?: number;
  highPrice?: number;
  lowPrice?: number;
  volume?: number;
}

export interface CompanyInfoResponse {
  basicInfo: CompanyBasicInfo;
  investmentIndicators: InvestmentIndicators;
  profitabilityIndicators: ProfitabilityIndicators;
  financialRatios: FinancialRatios;
  quarterlyPerformance: QuarterlyPerformance[];
  incomeStatements: IncomeStatementData[];
  balanceSheets: BalanceSheetData[];
  priceHistory: PriceHistoryPoint[];
}

export const companyApi = {
  /**
   * 종목 상세 정보 조회
   */
  getCompanyInfo: async (
    stockCode: string,
    userId?: string
  ): Promise<CompanyInfoResponse> => {
    const { data } = await axiosInstance.get<CompanyInfoResponse>(
      `/company/${stockCode}/info`,
      {
        params: {
          user_id: userId,
        },
      }
    );
    return data;
  },

  /**
   * 종목 검색
   */
  searchCompanies: async (
    query: string,
    limit: number = 10
  ): Promise<any[]> => {
    const { data } = await axiosInstance.get("/company/search", {
      params: {
        query,
        limit,
      },
    });
    return data;
  },
};
