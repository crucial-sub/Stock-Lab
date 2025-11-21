"use client";

import { useEffect, useState } from "react";
import {
  HighlightsSection,
  MarketInsightSection,
  PerformanceChartSection,
  StatsOverviewSection,
} from "@/components/home/auth";
import {
  GuestMarketInsightSection,
  GuestPortfolioSection,
} from "@/components/home/guest";
import { DiscussionPreviewSection } from "@/components/community";
import { FloatingChatWidget } from "@/components/home/FloatingChatWidget";
import type {
  GuestMarketIndex,
  GuestMarketStock,
  HomeCommunityHighlight,
  HomePortfolioHighlight,
  HomeStatCardData,
  MarketNews,
  MarketStock,
} from "@/types";
import type { AccountPerformanceChart } from "@/types/kiwoom";
import { marketQuoteApi } from "@/lib/api/market-quote";
import { fetchLatestNews } from "@/lib/api/news";

/**
 * 홈 페이지 클라이언트 컴포넌트
 *
 * @description 인터랙티브한 홈 화면 UI를 담당합니다.
 * 이벤트 핸들러와 상태 관리가 필요한 부분만 클라이언트 컴포넌트로 분리.
 */

interface DashboardData {
  total_assets: number;
  total_return: number;
  total_profit: number;
  active_strategy_count: number;
  total_positions: number;
  total_trades_today: number;
  total_allocated_capital: number;  // 자동매매에 할당된 총 금액
}

interface KiwoomAccountData {
  cash?: {
    balance?: string | number;
    withdrawable?: string | number;
    orderable?: string | number;
  };
  holdings?: {
    tot_evlt_amt?: string | number;
    tot_evlt_pl?: string | number;
    tot_prft_rt?: string | number;
    tot_pur_amt?: string | number;
  };
}

interface HomePageClientProps {
  userName: string;
  isLoggedIn: boolean;
  hasKiwoomAccount: boolean;
  kiwoomAccountData: KiwoomAccountData | null;
  performanceChartData: AccountPerformanceChart | null;
  dashboardData: DashboardData;
  marketStocksInitial: MarketStock[];
  marketNewsInitial: MarketNews[];
}

const parseNumericValue = (value?: string | number): number => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0;
  }
  if (!value) return 0;

  const cleaned = value.toString().replace(/[,%\s]/g, "");
  const parsed = Number.parseFloat(cleaned);
  return Number.isNaN(parsed) ? 0 : parsed;
};

const formatCurrencyWithSign = (value: number): string => {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toLocaleString()}원`;
};

const formatPercentWithSign = (value: number): string => {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
};

const guestMarketIndexes: GuestMarketIndex[] = [
  { label: "KOSPI", value: "4,089.25", change: "+22.4%" },
  { label: "KOSDAQ", value: "906.24", change: "+22.4%" },
];

const guestMarketStocksFallback: GuestMarketStock[] = Array.from({ length: 5 }).map(
  (_, index) => ({
    id: `guest-${index}`,
    name: "종목",
    tag: "예시",
    change: "+0.00%",
    price: "-",
    volume: "-",
  }),
);

// 로그인/로그아웃 공통 시황: 로그인 시 관심종목 상위, 비로그인 시 전체 상위
const marketStocksFallback: MarketStock[] = [
  { id: "guest-1", name: "크래프톤", tag: "예시", change: "+0.00%", price: "226,000원", volume: "113억" },
  { id: "guest-2", name: "삼성전자", tag: "예시", change: "+0.00%", price: "70,000원", volume: "99억" },
  { id: "guest-3", name: "LG에너지솔루션", tag: "예시", change: "+0.00%", price: "400,000원", volume: "87억" },
  { id: "guest-4", name: "현대차", tag: "예시", change: "+0.00%", price: "200,000원", volume: "70억" },
  { id: "guest-5", name: "카카오", tag: "예시", change: "+0.00%", price: "60,000원", volume: "65억" },
];

const buildAuthenticatedStats = (
  dashboardData: DashboardData,
  kiwoomAccountData: KiwoomAccountData | null
): HomeStatCardData[] => {
  // 키움 데이터가 있으면 키움 데이터 사용, 없으면 포트폴리오 데이터 사용
  const activeCount = Number(dashboardData.active_strategy_count) || 0;
  const allocatedCapital = Number(dashboardData.total_allocated_capital) || 0;

  if (kiwoomAccountData?.holdings) {
    const evaluationAmount = parseNumericValue(kiwoomAccountData.holdings.tot_evlt_amt);
    const totalProfit = parseNumericValue(kiwoomAccountData.holdings.tot_evlt_pl);
    const totalReturn = parseNumericValue(kiwoomAccountData.holdings.tot_prft_rt);
    const cashBalance = parseNumericValue(kiwoomAccountData.cash?.balance);

    // 키움 계좌 전체 금액에서 자동매매 할당 금액을 빼서 실제 사용 가능한 자산 계산
    const totalAssets = evaluationAmount + cashBalance - allocatedCapital;
    const availableCash = cashBalance - allocatedCapital;

    return [
      {
        id: "asset",
        title: "총 자산",
        value: `${totalAssets.toLocaleString()}원`,
        change: `평가손익 ${formatCurrencyWithSign(totalProfit)}`,
        badge: availableCash > 0 ? `예수금 ${availableCash.toLocaleString()}원` : "연동계좌",
      },
      {
        id: "return",
        title: "수익률",
        value: formatPercentWithSign(totalReturn),
        change: `평가금액 ${evaluationAmount.toLocaleString()}원`,
      },
      {
      id: "active",
      title: "활성 포트폴리오",
      value: `${activeCount}개`,
      change: "현재 활성 포트폴리오 개수",
      }
    ];
  }

  // 키움 데이터 없으면 기존 포트폴리오 데이터 사용
  const totalAssets = parseNumericValue(dashboardData.total_assets);
  const totalReturn = parseNumericValue(dashboardData.total_return);
  const totalProfit = parseNumericValue(dashboardData.total_profit);
  
  return [
    {
      id: "asset",
      title: "총 자산",
      value: `${totalAssets.toLocaleString()}원`,
      change: formatCurrencyWithSign(totalProfit),
    },
    {
      id: "return",
      title: "수익률",
      value: formatPercentWithSign(totalReturn),
      change: "포트폴리오 전체 기준",
    },
    {
      id: "active",
      title: "활성 포트폴리오",
      value: `${activeCount}개`,
      change: "현재 활성 포트폴리오 개수",
    }
  ];
};

const authPortfolios: HomePortfolioHighlight[] = [
  { id: "auth-port-1", name: "Portfolio Name", returnRate: 1323, rank: 1 },
  { id: "auth-port-2", name: "Portfolio Name", returnRate: 1323, rank: 2 },
  { id: "auth-port-3", name: "Portfolio Name", returnRate: 1323, rank: 3 },
];

const authCommunityHighlights: HomeCommunityHighlight[] = [
  {
    id: "auth-comm-1",
    title: "게시물 이름은 이렇게 들어갑니다.",
    preview:
      "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ...으로 처리할 수 있습니다.",
    tag: "태그",
    views: "999+",
    likes: "999+",
    comments: "999+",
  },
  {
    id: "auth-comm-2",
    title: "게시물 이름은 이렇게 들어갑니다.",
    preview:
      "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ...으로 처리할 수 있습니다.",
    tag: "태그",
    views: "999+",
    likes: "999+",
    comments: "999+",
  },
  {
    id: "auth-comm-3",
    title: "게시물 이름은 이렇게 들어갑니다.",
    preview:
      "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ...으로 처리할 수 있습니다.",
    tag: "태그",
    views: "999+",
    likes: "999+",
    comments: "999+",
  },
];

export function HomePageClient({
  userName,
  isLoggedIn,
  hasKiwoomAccount,
  kiwoomAccountData,
  performanceChartData,
  dashboardData,
  marketStocksInitial,
  marketNewsInitial,
}: HomePageClientProps) {
  const [marketStocks, setMarketStocks] = useState<MarketStock[]>(marketStocksInitial.length ? marketStocksInitial : marketStocksFallback);
  const [guestMarketStocks, setGuestMarketStocks] = useState<GuestMarketStock[]>(
    marketStocksInitial.length
      ? marketStocksInitial.map((item) => ({
          id: item.id,
          name: item.name,
          tag: item.tag,
          change: item.change,
          price: item.price,
          volume: item.volume,
        }))
      : guestMarketStocksFallback,
  );
  const [marketNews, setMarketNews] = useState<MarketNews[]>(marketNewsInitial.length ? marketNewsInitial : []);

  useEffect(() => {
    let isMounted = true;

    const fetchTopVolume = async () => {
      // 관심종목 기준 (로그인)
      if (isLoggedIn) {
        try {
          const favorites = await marketQuoteApi.getFavorites();
          const sortedByVolume = favorites.items
            .filter((item) => item.volume !== null && item.volume !== undefined)
            .sort((a, b) => (b.volume || 0) - (a.volume || 0))
            .slice(0, 5);

          if (sortedByVolume.length && isMounted) {
            const mapped = sortedByVolume.map((item) => ({
              id: item.stockCode,
              name: item.stockName,
              tag: item.stockCode,
              change: `${item.changeRate && item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
              price: item.currentPrice ? `${item.currentPrice.toLocaleString()}원` : "-",
              volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
            }));
            setMarketStocks(mapped);
            return;
          }
        } catch (error) {
          console.warn("관심종목 기준 시황 조회 실패, 전체 상위로 대체:", error);
        }
      }

      // 로그인 안 됐거나 관심 5종 부족 시: 전체 종목 체결량 상위
      try {
        const topVolume = await marketQuoteApi.getMarketQuotes({
          sortBy: "volume",
          sortOrder: "desc",
          page: 1,
          pageSize: 5,
        });
        if (isMounted) {
          const mapped = topVolume.items.map((item) => ({
            id: item.code,
            name: item.name,
            tag: item.code,
            change: `${item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
            price: item.price ? `${item.price.toLocaleString()}원` : "-",
            volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
          }));
          setMarketStocks(mapped);
          setGuestMarketStocks(mapped);
        }
      } catch (error) {
        console.warn("전체 종목 시황 조회 실패:", error);
      }
    };

    fetchTopVolume();
    return () => {
      isMounted = false;
    };
  }, [isLoggedIn]);

  // 최신 뉴스 5개 (백엔드 정렬: id desc 가정)
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const newsList = await fetchLatestNews(5);
        setMarketNews(
          newsList.slice(0, 5).map((item) => ({
            id: item.id,
            title: item.title,
            badge: item.tickerLabel || item.stockCode || "뉴스",
          })),
        );
      } catch (error) {
        console.warn("주요 시황 뉴스 조회 실패:", error);
      }
    };

    // 서버에서 내려준 초기 값이 없을 때만 호출
    if (!marketNews.length) {
      fetchNews();
    }
  }, [marketNews.length]);

  if (!isLoggedIn) {
    return (
      <>
        <div className="flex flex-col items-center px-10 pt-[120px] pb-20">
          <div className="flex w-full max-w-[1000px] flex-col gap-10">
            <GuestPortfolioSection />
            <GuestMarketInsightSection
              indexes={guestMarketIndexes}
              stocks={guestMarketStocks}
              news={marketNews}
            />
            <DiscussionPreviewSection limit={3} />
          </div>
        </div>
        <FloatingChatWidget />
      </>
    );
  }

  const authenticatedStats = buildAuthenticatedStats(dashboardData, kiwoomAccountData);

  return (
    <>
      <div className="flex flex-col items-center px-10 pt-[120px] pb-20">
        <div className="flex w-full max-w-[1000px] flex-col gap-10">
          <div className="text-[2rem] font-semibold text-text-body">
            안녕하세요, {userName}님
          </div>

          {/* 계좌 연동 안내 */}
          {!hasKiwoomAccount && (
            <div className="bg-bg-surface rounded-lg shadow-card p-6 border-2 border-accent-primary">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-text-title mb-2">
                    증권사 계좌 연동이 필요합니다
                  </h3>
                  <p className="text-text-body">
                    자동매매 기능을 사용하려면 키움증권 모의투자 계좌를 연동해주세요.
                  </p>
                </div>
                <a
                  href="/mypage"
                  className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-primary/90 transition-colors font-semibold whitespace-nowrap"
                >
                  증권사 계좌 연동하기
                </a>
              </div>
            </div>
          )}

          <StatsOverviewSection stats={authenticatedStats} />
          <PerformanceChartSection />
          <MarketInsightSection
            stocks={marketStocks}
            news={marketNews}
          />
          <HighlightsSection
            portfolios={authPortfolios}
            posts={authCommunityHighlights}
          />
          <DiscussionPreviewSection limit={3} className="mt-4" />
        </div>
      </div>
      <FloatingChatWidget />
    </>
  );
}
