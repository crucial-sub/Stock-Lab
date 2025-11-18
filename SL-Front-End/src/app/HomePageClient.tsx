"use client";

import {
  HighlightsSection,
  MarketInsightSection,
  PerformanceChartSection,
  StatsOverviewSection,
} from "@/components/home/auth";
import {
  GuestCommunityPreviewSection,
  GuestMarketInsightSection,
  GuestPortfolioSection,
} from "@/components/home/guest";
import type {
  GuestCommunityPost,
  GuestMarketIndex,
  GuestMarketNews,
  GuestMarketStock,
  GuestPortfolioCardData,
  HomeCommunityHighlight,
  HomePortfolioHighlight,
  HomeStatCardData,
  MarketNews,
  MarketStock,
} from "@/types";

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
}

interface HomePageClientProps {
  userName: string;
  isLoggedIn: boolean;
  hasKiwoomAccount: boolean;
  dashboardData: DashboardData;
}

const guestPortfolioMock: GuestPortfolioCardData[] = [
  {
    rank: 1,
    name: "Portfolio Name",
    organization: "FMJS",
    returnRate: 1323,
    highlight: "gold",
  },
  {
    rank: 2,
    name: "Portfolio Name",
    organization: "FMJS",
    returnRate: 1323,
    highlight: "silver",
  },
  {
    rank: 3,
    name: "Portfolio Name",
    organization: "FMJS",
    returnRate: 1323,
    highlight: "bronze",
  },
  {
    rank: 4,
    name: "Portfolio Name",
    organization: "FMJS",
    returnRate: 1323,
  },
  {
    rank: 5,
    name: "Portfolio Name",
    organization: "FMJS",
    returnRate: 1323,
  },
];

const guestMarketIndexes: GuestMarketIndex[] = [
  { label: "KOSPI", value: "4,089.25", change: "+22.4%" },
  { label: "KOSDAQ", value: "906.24", change: "+22.4%" },
];

const guestMarketStocks: GuestMarketStock[] = Array.from({ length: 3 }).map(
  (_, index) => ({
    id: `stock-${index}`,
    name: "크래프톤",
    tag: "IT",
    change: "+22.4%",
    price: "226,000원",
    volume: "113억",
  }),
);

const guestMarketNews: GuestMarketNews[] = Array.from({ length: 5 }).map(
  (_, index) => ({
    id: `news-${index}`,
    title: "크래프톤 정글의 SW-AI랩 신규 런칭, 차세대 AI 교육...",
    badge: "크래프톤",
  }),
);

const guestCommunityPosts: GuestCommunityPost[] = Array.from({ length: 3 }).map(
  (_, index) => ({
    id: `post-${index}`,
    title: "게시물 이름은 이렇게 들어갑니다.",
    preview:
      "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ...으로 처리할 수 있습니다.",
    author: "FMJS",
    date: "2025.12.31 19:00",
    tag: "태그",
    views: "999+",
    likes: "999+",
    comments: "999+",
  }),
);

const buildAuthenticatedStats = (dashboardData: DashboardData): HomeStatCardData[] => {
  const totalAssets = Number(dashboardData.total_assets) || 0;
  const totalReturn = Number(dashboardData.total_return) || 0;
  const totalProfit = Number(dashboardData.total_profit) || 0;
  const activeCount = Number(dashboardData.active_strategy_count) || 0;

  return [
    {
      id: "asset",
      title: "총 자산",
      value: `${totalAssets.toLocaleString()}원`,
      change: `${totalProfit >= 0 ? '+' : ''}${totalProfit.toLocaleString()}원`,
      badge: `${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%`,
    },
    {
      id: "profit",
      title: "수익률",
      value: `${totalProfit.toLocaleString()}원`,
      change: `${totalAssets.toLocaleString()}원`,
      badge: "누적",
    },
    {
      id: "active",
      title: "활성 포트폴리오",
      value: `${activeCount}개`,
      change: "현재 활성 포트폴리오 개수",
    },
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

const MarketStocks: MarketStock[] = Array.from({ length: 5 }).map(
  (_, index) => ({
    id: `stock-${index}`,
    name: "크래프톤",
    tag: "IT",
    change: "+22.4%",
    price: "226,000원",
    volume: "113억",
  }),
);

const MarketNews: MarketNews[] = Array.from({ length: 5 }).map(
  (_, index) => ({
    id: `news-${index}`,
    title: "크래프톤 정글의 SW-AI랩 신규 런칭, 차세대 AI 교육...",
    badge: "크래프톤",
  }),
);

export function HomePageClient({
  userName,
  isLoggedIn,
  hasKiwoomAccount,
  dashboardData,
}: HomePageClientProps) {
  if (!isLoggedIn) {
    return (
      <div className="flex flex-col items-center px-10 pt-[120px] pb-20">
        <div className="flex w-full max-w-[1000px] flex-col gap-10">
          <GuestPortfolioSection portfolios={guestPortfolioMock} />
          <GuestMarketInsightSection
            indexes={guestMarketIndexes}
            stocks={guestMarketStocks}
            news={guestMarketNews}
          />
          <GuestCommunityPreviewSection posts={guestCommunityPosts} />
        </div>
      </div>
    );
  }

  const authenticatedStats = buildAuthenticatedStats(dashboardData);

  return (
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
          stocks={MarketStocks}
          news={MarketNews}
        />
        <HighlightsSection
          portfolios={authPortfolios}
          posts={authCommunityHighlights}
        />
      </div>
    </div>
  );
}
