"use client";

import {
  RecommendedQuestionsSection,
  WelcomeSection,
} from "@/components/home/sections";

/**
 * 홈 페이지 클라이언트 컴포넌트
 *
 * @description 인터랙티브한 홈 화면 UI를 담당합니다.
 * 이벤트 핸들러와 상태 관리가 필요한 부분만 클라이언트 컴포넌트로 분리.
 */

interface HomePageClientProps {
  /** 사용자 이름 (서버에서 전달) */
  userName: string;
}

export function HomePageClient({ userName }: HomePageClientProps) {
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
      {/* 환영 섹션 */}
      <WelcomeSection userName={userName} onSubmit={handleAISubmit} />

      {/* 추천 질문 섹션 */}
      <RecommendedQuestionsSection onQuestionClick={handleQuestionClick} />
    </div>
  );
}
