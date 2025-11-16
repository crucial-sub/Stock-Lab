"use client";

import { useRouter } from "next/navigation";
import {
  RankingCard,
  PortfolioShareCard,
  CommunityPostCard,
} from "@/components/community";

/**
 * 커뮤니티 페이지 클라이언트 컴포넌트
 * - 수익률 랭킹
 * - 포트폴리오 공유하기
 * - 자유게시판
 */
export default function CommunityPageClient() {
  const router = useRouter();

  // TODO: API 연동으로 실제 데이터 가져오기
  const rankingData = [
    {
      rank: 1 as const,
      portfolioName: "Portfolio Name",
      author: "FMJS",
      returnRate: "+1,323",
    },
    {
      rank: 2 as const,
      portfolioName: "Portfolio Name",
      author: "FMJS",
      returnRate: "+1,323",
    },
    {
      rank: 3 as const,
      portfolioName: "Portfolio Name",
      author: "FMJS",
      returnRate: "+1,323",
    },
  ];

  const portfolioShareData = [
    {
      portfolioName: "Portfolio Name",
      author: "FMJS",
      description: "설명은 여기에 들어갑니다. 이렇게 간단하게 들어갈 수 있습니다.",
      returnRate: "+1,323",
      stocks: ["삼성전자", "LG 화학", "크래프톤", "카카오"],
    },
    {
      portfolioName: "Portfolio Name",
      author: "FMJS",
      description: "설명은 여기에 들어갑니다. 이렇게 간단하게 들어갈 수 있습니다.",
      returnRate: "+1,323",
      stocks: ["삼성전자", "LG 화학", "크래프톤", "카카오"],
    },
    {
      portfolioName: "Portfolio Name",
      author: "FMJS",
      description: "설명은 여기에 들어갑니다. 이렇게 간단하게 들어갈 수 있습니다.",
      returnRate: "+1,323",
      stocks: ["삼성전자", "LG 화학", "크래프톤", "카카오"],
    },
  ];

  const postsData = [
    {
      id: 1,
      tag: "태그",
      title: "게시물 이름은 이렇게 들어갑니다.",
      author: "FMJS",
      date: "2025.12.31 19:00",
      preview:
        "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ... 으로 처리할 수 있습니다.",
      views: 999,
      likes: 999,
      comments: 999,
    },
    {
      id: 2,
      tag: "태그",
      title: "게시물 이름은 이렇게 들어갑니다.",
      author: "FMJS",
      date: "2025.12.31 19:00",
      preview:
        "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ... 으로 처리할 수 있습니다.",
      views: 999,
      likes: 999,
      comments: 999,
    },
    {
      id: 3,
      tag: "태그",
      title: "게시물 이름은 이렇게 들어갑니다.",
      author: "FMJS",
      date: "2025.12.31 19:00",
      preview:
        "게시물 내용 미리보기가 들어갑니다. 두 줄 이상으로 길어질 경우에는 ... 으로 처리할 수 있습니다.",
      views: 999,
      likes: 999,
      comments: 999,
    },
  ];

  return (
    <div className="flex flex-col max-w-[1040px] mx-auto px-5 py-10">
      {/* 수익률 랭킹 섹션 */}
      <section className="mb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-body">수익률 랭킹</h2>
          <a
            href="#"
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {rankingData.map((item) => (
            <RankingCard
              key={item.rank}
              rank={item.rank}
              portfolioName={item.portfolioName}
              author={item.author}
              returnRate={item.returnRate}
              onCopy={() => console.log(`복제: ${item.portfolioName}`)}
            />
          ))}
        </div>
      </section>

      {/* 포트폴리오 공유하기 섹션 */}
      <section className="mb-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-body">포트폴리오 공유하기</h2>
          <a
            href="#"
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {portfolioShareData.map((item, index) => (
            <PortfolioShareCard
              key={index}
              portfolioName={item.portfolioName}
              author={item.author}
              description={item.description}
              returnRate={item.returnRate}
              stocks={item.stocks}
              onAdd={() => console.log(`추가: ${item.portfolioName}`)}
            />
          ))}
        </div>
      </section>

      {/* 자유게시판 섹션 */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-body">자유게시판</h2>
          <a
            href="#"
            className="text-base text-gray-700 underline hover:text-gray-600"
          >
            더보기
          </a>
        </div>

        <div className="flex flex-col gap-5">
          {postsData.map((item) => (
            <CommunityPostCard
              key={item.id}
              tag={item.tag}
              title={item.title}
              author={item.author}
              date={item.date}
              preview={item.preview}
              views={item.views}
              likes={item.likes}
              comments={item.comments}
              onClick={() => router.push(`/community/${item.id}`)}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
