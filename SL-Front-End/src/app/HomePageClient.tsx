"use client";

import { useRouter } from "next/navigation";
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
  /** 로그인 여부 (서버에서 전달) */
  isLoggedIn: boolean;
}

export function HomePageClient({ userName }: HomePageClientProps) {
  const router = useRouter();

  const handleAISubmit = (value: string) => {
    // AI 어시스턴트 페이지로 이동하면서 질문 전달
    console.log("AI request:", value);
    // sessionStorage에 초기 메시지 저장
    sessionStorage.setItem("ai-initial-message", value);
    router.push("/ai-assistant");
  };

  const handleQuestionClick = (question: string) => {
    // 추천 질문 클릭 시에도 AI 어시스턴트로 이동
    console.log("Question clicked:", question);
    sessionStorage.setItem("ai-initial-message", question);
    router.push("/ai-assistant");
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
