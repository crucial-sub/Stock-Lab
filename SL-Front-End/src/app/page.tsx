import { cookies } from "next/headers";
import { HomePageClient } from "./HomePageClient";
import { authApi } from "@/lib/api/auth";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { kiwoomApi } from "@/lib/api/kiwoom";
import type { MarketNews, MarketStock } from "@/types";

/**
 * 홈 페이지 (서버 컴포넌트)
 *
 * @description 메인 홈 화면의 진입점입니다.
 * 서버에서 로그인 상태를 확인하고 클라이언트 컴포넌트에 전달합니다.
 */
export default async function HomePage() {
  // 쿠키에서 토큰 확인하여 로그인 여부 판단
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const isLoggedIn = !!token;

  let userName = "게스트";
  let hasKiwoomAccount = false;
  let kiwoomAccountData = null;
  let performanceChartData = null;
  let marketStocks: MarketStock[] = [];
  let marketNews: MarketNews[] = [];
  let dashboardData = {
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
      // 1. 사용자 정보 가져오기
      const userInfo = await authApi.getCurrentUserServer(token);
      userName = userInfo.nickname || "사용자";
      hasKiwoomAccount = userInfo.has_kiwoom_account || false;

      // 2. 키움 계좌 연동되어 있으면 잔고 조회
      if (hasKiwoomAccount) {
        try {
          const kiwoomStatus = await kiwoomApi.getStatusServer(token);
          if (kiwoomStatus.is_connected) {
            const accountResponse = await kiwoomApi.getAccountBalanceServer(token);
            // API 응답이 { data, message } 형태일 수 있어 데이터 필드 우선 사용
            kiwoomAccountData = (accountResponse as { data?: unknown }).data ?? accountResponse;
          }
        } catch (error) {
          console.warn("키움 계좌 데이터 조회 실패:", error);
        }
      }

      // 3. 포트폴리오 대시보드 데이터 가져오기
      try {
        dashboardData = await autoTradingApi.getPortfolioDashboardServer(token);
      } catch (error) {
        console.warn("대시보드 데이터 조회 실패:", error);
      }

      // 3-1. 성과 차트 데이터 가져오기 (계좌 연동된 경우에만)
      if (hasKiwoomAccount) {
        try {
          performanceChartData = await kiwoomApi.getPerformanceChartServer(token, 30);
        } catch (error) {
          console.warn("성과 차트 데이터 조회 실패:", error);
        }
      }
      // 4. 시황/뉴스 데이터 서버 사이드로 미리 가져오기
      try {
        const axios = (await import("axios")).default;
        const baseURL = process.env.API_BASE_URL || "http://backend:8000/api/v1";

        if (hasKiwoomAccount) {
          // 관심종목 체결량 상위 5
          try {
            const favorites = await axios.get(`${baseURL}/market/favorites`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const sorted = (favorites.data?.items || [])
              .filter((item: any) => item.volume !== null && item.volume !== undefined)
              .sort((a: any, b: any) => (b.volume || 0) - (a.volume || 0))
              .slice(0, 5);
            marketStocks = sorted.map((item: any) => ({
              id: item.stockCode,
              name: item.stockName,
              tag: item.stockCode,
              change: `${item.changeRate && item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
              price: item.currentPrice ? `${item.currentPrice.toLocaleString()}원` : "-",
              volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
            }));
          } catch (error) {
            console.warn("관심종목 시황 조회 실패, 전체 상위로 대체:", error);
          }
        }

        // 관심종목 없거나 로그인만 한 경우: 전체 체결량 상위
        if (!marketStocks.length) {
          const quotes = await axios.get(`${baseURL}/market/quotes`, {
            params: {
              sort_by: "volume",
              sort_order: "desc",
              page: 1,
              page_size: 5,
            },
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
          });
          marketStocks = (quotes.data?.items || []).map((item: any) => ({
            id: item.code,
            name: item.name,
            tag: item.code,
            change: `${item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
            price: item.price ? `${item.price.toLocaleString()}원` : "-",
            volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
          }));
        }

        const latestNews = await axios.get(`${baseURL}/news/db/latest`, {
          params: { limit: 5 },
        });
        marketNews = (latestNews.data?.news || []).map((item: any) => ({
          id: item.id,
          title: item.title,
          badge: item.tickerLabel || item.stockCode || "뉴스",
        }));
      } catch (error) {
        console.warn("시황/뉴스 데이터 조회 실패:", error);
      }
    } catch (error) {
      console.error("Failed to fetch user info:", error);
    }
  } else {
    // 게스트 사용자를 위해 서버에서 기본 시황/뉴스 가져오기
    try {
      const axios = (await import("axios")).default;
      const baseURL = process.env.API_BASE_URL || "http://backend:8000/api/v1";
      const quotes = await axios.get(`${baseURL}/market/quotes`, {
        params: { sort_by: "volume", sort_order: "desc", page: 1, page_size: 5 },
      });
      marketStocks = (quotes.data?.items || []).map((item: any) => ({
        id: item.code,
        name: item.name,
        tag: item.code,
        change: `${item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
        price: item.price ? `${item.price.toLocaleString()}원` : "-",
        volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
      }));

      const latestNews = await axios.get(`${baseURL}/news/db/latest`, {
        params: { limit: 5 },
      });
      marketNews = (latestNews.data?.news || []).map((item: any) => ({
        id: item.id,
        title: item.title,
        badge: item.tickerLabel || item.stockCode || "뉴스",
      }));
    } catch (error) {
      console.warn("게스트 시황/뉴스 조회 실패:", error);
    }
  }

  return (
    <HomePageClient
      userName={userName}
      isLoggedIn={isLoggedIn}
      hasKiwoomAccount={hasKiwoomAccount}
      kiwoomAccountData={kiwoomAccountData}
      performanceChartData={performanceChartData}
      dashboardData={dashboardData}
      marketStocksInitial={marketStocks}
      marketNewsInitial={marketNews}
    />
  );
}
