"use client";

import { useRouter } from "next/navigation";
import { DiscussionPreviewSection } from "@/components/community";

/**
 * 커뮤니티 페이지 클라이언트 컴포넌트
 * - 수익률 랭킹
 * - 포트폴리오 공유하기
 * - 자유게시판 - 얘만 남기고 수익률, 포트폴리오 공유는 전략포트폴리오 페이지
 */
export default function CommunityPageClient() {
  return (
    <div className="flex flex-col max-w-[1000px] mx-auto px-5 py-10">
      <DiscussionPreviewSection limit={5} />
    </div>
  );
}
