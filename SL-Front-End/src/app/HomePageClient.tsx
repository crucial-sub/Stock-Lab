"use client";

import { useEffect, useState } from "react";
import { Title } from "@/components/common/Title";
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

export interface KiwoomAccountData {
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
  { label: "KOSPI", value: "-", change: "+0.00%" },
  { label: "KOSDAQ", value: "-", change: "+0.00%" },
];

const guestTips = [
  {
    title: "관심 전략 저장",
    description: "회원가입 후 마음에 드는 전략을 저장하고 알림을 받아보세요.",
    accent: "bg-[#FDECEF] text-[#E2506E] border-[0.5px] border-[#E2506E]",
  },
  {
    title: "키움 계좌 연동",
    description: "모의투자 계좌를 연동하면 자동 매매와 실계좌 시뮬레이션이 가능해요.",
    accent: "bg-[#EAF5FF] text-[#2B7DDD] border-[0.5px] border-[#2B7DDD]",
  },
  {
    title: "전략 비교",
    description: "성과 차트를 통해 지난 30일간의 전략 성과를 한눈에 비교할 수 있어요.",
    accent: "bg-[#F2ECFE] text-[#6C40B5] border-[0.5px] border-[#6C40B5]",
  },
  {
    title: "시장 인사이트",
    description: "테마와 종목을 실시간으로 분석해 드립니다. 맞춤형 뉴스도 확인해보세요.",
    accent: "bg-[#FFF4E6] text-[#D8862B] border-[0.5px] border-[#D8862B]",
  },
  {
    title: "커뮤니티 참여",
    description: "전략 운영 꿀팁과 투자 일지를 공유하며 트레이더들과 소통해 보세요.",
    accent: "bg-[#ECFDF3] text-[#1C8757] border-[0.5px] border-[#1C8757]",
  },
  {
    title: "AI 도우미",
    description: "AI에게 전략 설계와 리밸런싱을 물어보세요. 실시간 답변을 제공합니다.",
    accent: "bg-[#EAF2FF] text-[#3A64CB] border-[0.5px] border-[#3A64CB]",
  },
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
  const normalizeStock = (item: MarketStock): MarketStock => ({
    ...item,
    tag: item.tag || "테마 정보 없음",
  });

  const [marketStocks, setMarketStocks] = useState<MarketStock[]>(() =>
    (marketStocksInitial || []).map(normalizeStock),
  );
  const [guestMarketStocks, setGuestMarketStocks] = useState<GuestMarketStock[]>(() =>
    (marketStocksInitial || []).map((item) => ({
      id: item.id,
      name: item.name,
      tag: item.tag || "테마 정보 없음",
      change: item.change,
      price: item.price,
      volume: item.volume,
    })),
  );
  const [marketNews, setMarketNews] = useState<MarketNews[]>(() => marketNewsInitial || []);

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
              tag: item.theme ?? item.stockCode,
              change: `${item.changeRate && item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
              price: item.currentPrice ? `${item.currentPrice.toLocaleString()}원` : "-",
              volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
            }));
            setMarketStocks(mapped.map(normalizeStock));
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
          pageSize: 3,
        });
        if (isMounted) {
          const mapped = topVolume.items.map((item) => ({
            id: item.code,
            name: item.name,
            tag: item.theme ?? item.code,
            change: `${item.changeRate > 0 ? "+" : ""}${(item.changeRate ?? 0).toFixed(2)}%`,
            price: item.price ? `${item.price.toLocaleString()}원` : "-",
            volume: item.volume ? `${item.volume.toLocaleString()}주` : "-",
          }));
          const normalized = mapped.map(normalizeStock);
          setMarketStocks(normalized);
          setGuestMarketStocks(normalized);
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
            <section className="flex w-full flex-col gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-[1.5rem] font-semibold">Stock-Lab 사용 Tip</span>
              </div>
              <div className="tip-wrapper relative overflow-hidden">
                <div className="ticker-track">
                  {[...guestTips, ...guestTips].map((tip, index) => (
                    <article
                      key={`${tip.title}-${index}`}
                      className="my-1 tip-card group relative min-w-[280px] max-w-[320px] rounded-[12px] border-[0.5px] border-[#18223433] bg-[#1822340D] p-5 shadow-elev-card-soft transition-colors duration-300 hover:bg-white/20"
                    >
                      <div className={`inline-flex items-center rounded-full px-3 pt-1 pb-0.5 text-xs font-semibold ${tip.accent}`}>
                        ✔︎ TIP
                      </div>
                      <h3 className="mt-4 text-[1rem] font-semibold text-body">{tip.title}</h3>
                      <p className="mt-1 text-[0.875rem] font-normal text-muted">{tip.description}</p>
                      <div className="mt-5 h-0.5 w-20 rounded-full bg-gradient-to-r from-[#FF8FB1] via-[#A08BFF] to-[#5EB7FF] opacity-75 transition-opacity duration-300 group-hover:opacity-100" />
                    </article>
                  ))}
                </div>
              </div>
            </section>
            <DiscussionPreviewSection limit={3} />
          </div>
        </div>
        <FloatingChatWidget />
        <style jsx global>{`
          @keyframes guest-tip-marquee {
            0% {
              transform: translateX(0);
            }
            100% {
              transform: translateX(-50%);
            }
          }

          .ticker-track {
            display: flex;
            gap: 1rem;
            width: max-content;
            animation: guest-tip-marquee 60s linear infinite;
            will-change: transform;
          }

          .tip-wrapper:hover .ticker-track {
            animation-play-state: paused;
          }

          .ticker-track .tip-card {
            flex-shrink: 0;
          }

          @media (prefers-reduced-motion: reduce) {
            .ticker-track {
              animation: none;
            }
          }
        `}</style>
      </>
    );
  }

  const authenticatedStats = buildAuthenticatedStats(dashboardData, kiwoomAccountData);
  const portfolioHighlights: HomePortfolioHighlight[] = [];
  const communityHighlights: HomeCommunityHighlight[] = [];
  const hasHighlights = portfolioHighlights.length > 0 && communityHighlights.length > 0;

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
          {hasHighlights && (
            <HighlightsSection
              portfolios={portfolioHighlights}
              posts={communityHighlights}
            />
          )}
          <DiscussionPreviewSection limit={3} className="mt-4" />
        </div>
      </div>
      <FloatingChatWidget />
    </>
  );
}
