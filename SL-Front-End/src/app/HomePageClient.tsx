"use client";

import {
  GuestCommunityPreviewSection,
  GuestMarketInsightSection,
  GuestPortfolioSection,
} from "@/components/home/guest";
import {
  RecommendedQuestionsSection,
  WelcomeSection,
} from "@/components/home/sections";
import type {
  GuestCommunityPost,
  GuestMarketIndex,
  GuestMarketNews,
  GuestMarketStock,
  GuestPortfolioCardData,
} from "@/types";

/**
 * 홈 페이지 클라이언트 컴포넌트
 *
 * @description 인터랙티브한 홈 화면 UI를 담당합니다.
 * 이벤트 핸들러와 상태 관리가 필요한 부분만 클라이언트 컴포넌트로 분리.
 */

interface HomePageClientProps {
  userName: string;
  isLoggedIn: boolean;
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

export function HomePageClient({
  userName,
  isLoggedIn,
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

  const handleAISubmit = (value: string) => {
    // TODO: AI 전략 요청 처리 로직 구현
    console.log("AI request:", value);
  };

  const handleQuestionClick = (question: string) => {
    // TODO: 추천 질문 클릭 처리 로직 구현
    console.log("Question clicked:", question);
  };

  return (
    <div className="flex flex-col items-center px-10 pt-[120px] pb-20">
      <div className="flex w-full max-w-[1000px] flex-col items-center">
        <WelcomeSection userName={userName} onSubmit={handleAISubmit} />
        <RecommendedQuestionsSection onQuestionClick={handleQuestionClick} />
      </div>
    </div>
  );
}
