import { cookies } from "next/headers";
import { HomePageClient, type KiwoomAccountData } from "./HomePageClient";
import { authApi } from "@/lib/api/auth";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { kiwoomApi } from "@/lib/api/kiwoom";
import type { MarketNews, MarketStock } from "@/types";
import type { AxiosResponse } from "axios";
import type { AccountPerformanceChart } from "@/types/kiwoom";

/**
 * 홈 페이지 (서버 컴포넌트)
 *
 * @description 메인 홈 화면의 진입점입니다.
 * 서버에서 로그인 상태를 확인하고 클라이언트 컴포넌트에 전달합니다.
 */

interface DashboardData {
  total_assets: number;
  total_return: number;
  total_profit: number;
  active_strategy_count: number;
  total_positions: number;
  total_trades_today: number;
  total_allocated_capital: number;
}

interface NewsItem {
  id: string;
  title: string;
  tickerLabel?: string;
  stockCode?: string;
}

interface NewsApiResponse {
  news: NewsItem[];
}

interface MarketQuoteItem {
  code?: string;
  name?: string;
  stockCode?: string;
  stockName?: string;
  theme?: string;
  changeRate?: number;
  currentPrice?: number;
  price?: number;
  volume?: number;
}

interface MarketQuotesApiResponse {
  items: MarketQuoteItem[];
}

export default async function HomePage() {
  // 쿠키에서 토큰 확인하여 로그인 여부 판단
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const isLoggedIn = !!token;

  let userName = "게스트";
  let hasKiwoomAccount = false;
  let aiRecommendationBlock = false;
  let kiwoomAccountData: KiwoomAccountData | null = null;
  let performanceChartData: AccountPerformanceChart | null = null;
  let marketStocks: MarketStock[] = [];
  let marketNews: MarketNews[] = [];
  let dashboardData: DashboardData = {
    total_assets: 0,
    total_return: 0,
    total_profit: 0,
    active_strategy_count: 0,
    total_positions: 0,
    total_trades_today: 0,
    total_allocated_capital: 0,
  };

  if (isLoggedIn && token) {
    try {
      // 1. 사용자 정보 먼저 가져오기 (다른 요청들이 이 정보에 의존)
      const userInfo = await authApi.getCurrentUserServer(token);
      userName = userInfo.nickname || "사용자";
      hasKiwoomAccount = userInfo.has_kiwoom_account || false;
      aiRecommendationBlock = userInfo.ai_recommendation_block || false;

      // 2. 독립적인 요청들을 병렬로 처리
      const axios = (await import("axios")).default;
      const baseURL = process.env.API_BASE_URL || "http://backend:8000/api/v1";

      // 병렬 요청 배열 구성
      const parallelRequests: Array<
        | Promise<DashboardData>
        | Promise<NewsItem[]>
        | Promise<KiwoomAccountData | null>
        | Promise<AccountPerformanceChart | null>
        | Promise<MarketStock[]>
      > = [];

      // 항상 실행: 대시보드 데이터
      const dashboardPromise: Promise<DashboardData> = autoTradingApi
        .getPortfolioDashboardServer(token)
        .catch((): DashboardData => {
          console.warn("대시보드 데이터 조회 실패");
          return {
            total_assets: 0,
            total_return: 0,
            total_profit: 0,
            active_strategy_count: 0,
            total_positions: 0,
            total_trades_today: 0,
            total_allocated_capital: 0,
          };
        });
      parallelRequests.push(dashboardPromise);

      // 항상 실행: 뉴스
      const newsPromise: Promise<NewsItem[]> = axios
        .get<NewsApiResponse>(`${baseURL}/news/db/latest`, {
          params: { limit: 5 },
        })
        .then((response): NewsItem[] => response.data?.news || [])
        .catch((): NewsItem[] => {
          console.warn("뉴스 데이터 조회 실패");
          return [];
        });
      parallelRequests.push(newsPromise);

      // Kiwoom 계좌 연동된 경우에만 추가
      if (hasKiwoomAccount) {
        // Kiwoom 계좌 데이터 (상태 확인 후 잔고 조회)
        const kiwoomPromise: Promise<KiwoomAccountData | null> = kiwoomApi
          .getStatusServer(token)
          .then(async (kiwoomStatus): Promise<KiwoomAccountData | null> => {
            if (kiwoomStatus.is_connected) {
              const accountResponse = await kiwoomApi.getAccountBalanceServer(token);
              const data = (accountResponse as { data?: KiwoomAccountData }).data;
              return data ?? (accountResponse as KiwoomAccountData);
            }
            return null;
          })
          .catch((): KiwoomAccountData | null => {
            console.warn("키움 계좌 데이터 조회 실패");
            return null;
          });
        parallelRequests.push(kiwoomPromise);

        // 성과 차트 데이터
        const chartPromise: Promise<AccountPerformanceChart | null> = kiwoomApi
          .getPerformanceChartServer(token, 30)
          .catch((): AccountPerformanceChart | null => {
            console.warn("성과 차트 데이터 조회 실패");
            return null;
          });
        parallelRequests.push(chartPromise);
      }

      // 관심종목 시황 (실패 시 전체 시황으로 폴백)
      const stocksPromise: Promise<MarketStock[]> = axios
        .get<MarketQuotesApiResponse>(`${baseURL}/market/favorites`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((favorites): MarketStock[] => {
          const sorted = (favorites.data?.items || [])
            .filter((item: MarketQuoteItem) => item.volume !== null && item.volume !== undefined)
            .sort((a: MarketQuoteItem, b: MarketQuoteItem) => (b.volume || 0) - (a.volume || 0))
            .slice(0, 5);

          if (sorted.length > 0) {
            return sorted.map((item: MarketQuoteItem): MarketStock => ({
              id: item.stockCode || "",
              name: item.stockName || "",
              tag: item.theme ?? item.stockCode ?? "테마 정보 없음",
              change: `${item.changeRate && item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
              changeRate: item.changeRate ?? 0,
              price: item.currentPrice ? `${item.currentPrice.toLocaleString()}원` : "-",
              volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
            }));
          }
          return []; // 관심종목 없음
        })
        .catch((): MarketStock[] => {
          console.warn("관심종목 시황 조회 실패");
          return [];
        })
        .then(async (favoriteStocks: MarketStock[]): Promise<MarketStock[]> => {
          // 관심종목이 없으면 전체 상위로 조회
          if (favoriteStocks.length === 0) {
            try {
              const quotes = await axios.get<MarketQuotesApiResponse>(`${baseURL}/market/quotes`, {
                params: {
                  sort_by: "volume",
                  sort_order: "desc",
                  page: 1,
                  page_size: 5,
                },
                headers: { Authorization: `Bearer ${token}` },
              });
              return (quotes.data?.items || []).map((item: MarketQuoteItem): MarketStock => ({
                id: item.code || "",
                name: item.name || "",
                tag: item.theme ?? item.code ?? "테마 정보 없음",
                change: `${(item.changeRate ?? 0) > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
                changeRate: item.changeRate ?? 0,
                price: item.price ? `${item.price.toLocaleString()}원` : "-",
                volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
              }));
            } catch (error) {
              console.warn("전체 시황 조회 실패:", error);
              return [];
            }
          }
          return favoriteStocks;
        });
      parallelRequests.push(stocksPromise);

      // 모든 요청 병렬 실행
      const results = await Promise.allSettled(parallelRequests);

      // 결과 파싱
      let resultIndex = 0;

      // 대시보드 데이터
      const dashboardResult = results[resultIndex];
      if (dashboardResult.status === 'fulfilled') {
        dashboardData = dashboardResult.value as DashboardData;
      }
      resultIndex++;

      // 뉴스 데이터
      const newsResult = results[resultIndex];
      if (newsResult.status === 'fulfilled') {
        const newsItems = newsResult.value as NewsItem[];
        marketNews = newsItems.map((item: NewsItem): MarketNews => ({
          id: item.id,
          title: item.title,
          badge: item.tickerLabel || item.stockCode || "뉴스",
        }));
      }
      resultIndex++;

      // Kiwoom 계좌 데이터 (있는 경우)
      if (hasKiwoomAccount && results[resultIndex]) {
        const kiwoomResult = results[resultIndex];
        if (kiwoomResult.status === 'fulfilled') {
          kiwoomAccountData = kiwoomResult.value as KiwoomAccountData | null;
        }
        resultIndex++;

        // 성과 차트 데이터
        if (results[resultIndex]) {
          const chartResult = results[resultIndex];
          if (chartResult.status === 'fulfilled') {
            performanceChartData = chartResult.value as AccountPerformanceChart | null;
          }
          resultIndex++;
        }
      }

      // 시황 데이터
      if (results[resultIndex]) {
        const stocksResult = results[resultIndex];
        if (stocksResult.status === 'fulfilled') {
          marketStocks = stocksResult.value as MarketStock[];
        }
      }

    } catch (error) {
      console.error("Failed to fetch user info:", error);
    }
  } else {
    // 게스트 사용자를 위해 서버에서 기본 시황/뉴스 가져오기 (병렬)
    try {
      const axios = (await import("axios")).default;
      const baseURL = process.env.API_BASE_URL || "http://backend:8000/api/v1";

      const guestStocksPromise: Promise<MarketStock[]> = axios
        .get<MarketQuotesApiResponse>(`${baseURL}/market/quotes`, {
          params: { sort_by: "volume", sort_order: "desc", page: 1, page_size: 5 },
        })
        .then((response): MarketStock[] => {
          return (response.data?.items || []).map((item: MarketQuoteItem): MarketStock => ({
            id: item.code || "",
            name: item.name || "",
            tag: item.theme ?? item.code ?? "테마 정보 없음",
            change: `${(item.changeRate ?? 0) > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
            changeRate: item.changeRate ?? 0,
            price: item.price ? `${item.price.toLocaleString()}원` : "-",
            volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
          }));
        })
        .catch((): MarketStock[] => {
          console.warn("게스트 시황 조회 실패");
          return [];
        });

      const guestNewsPromise: Promise<NewsItem[]> = axios
        .get<NewsApiResponse>(`${baseURL}/news/db/latest`, {
          params: { limit: 5 },
        })
        .then((response): NewsItem[] => response.data?.news || [])
        .catch((): NewsItem[] => {
          console.warn("게스트 뉴스 조회 실패");
          return [];
        });

      const guestResults = await Promise.allSettled([
        guestStocksPromise,
        guestNewsPromise,
      ]);

      // 시황 데이터
      const quotesResult = guestResults[0];
      if (quotesResult.status === 'fulfilled') {
        marketStocks = quotesResult.value as MarketStock[];
      }

      // 뉴스 데이터
      const newsResult = guestResults[1];
      if (newsResult.status === 'fulfilled') {
        const newsItems = newsResult.value as NewsItem[];
        marketNews = newsItems.map((item: NewsItem): MarketNews => ({
          id: item.id,
          title: item.title,
          badge: item.tickerLabel || item.stockCode || "뉴스",
        }));
      }
    } catch (error) {
      console.warn("게스트 시황/뉴스 조회 실패:", error);
    }
  }

  return (
    <HomePageClient
      userName={userName}
      isLoggedIn={isLoggedIn}
      hasKiwoomAccount={hasKiwoomAccount}
      aiRecommendationBlock={aiRecommendationBlock}
      kiwoomAccountData={kiwoomAccountData}
      performanceChartData={performanceChartData}
      dashboardData={dashboardData}
      marketStocksInitial={marketStocks}
      marketNewsInitial={marketNews}
    />
  );
}
