"use client";

import { QuestionCard } from "../ui";

/**
 * 추천 질문 섹션
 *
 * @description 홈 화면의 추천 질문 카드들을 표시하는 섹션입니다.
 * AI에게 물어볼 수 있는 추천 질문 3가지를 제공합니다.
 *
 * @example
 * ```tsx
 * <RecommendedQuestionsSection
 *   onQuestionClick={(question) => console.log("선택된 질문:", question)}
 * />
 * ```
 */

interface RecommendedQuestionsSectionProps {
  /** 질문 카드 클릭 시 호출되는 콜백 함수 */
  onQuestionClick?: (question: string) => void;
}

const RECOMMENDED_QUESTIONS = [
  {
    title: "요즘 뜨는 전략",
    description:
      "최신 유행하는 전략을 확인해보세요!\n저명한 주식 분석가들이 만든 신뢰도가 높은 전략이에요.",
  },
  {
    title: "퀀트 투자가 무엇인가요?",
    description:
      "퀀트 투자에 대해 알아보세요!\n퀀트 투자의 특징과 장점들, 처음 해보는 전략 작성까지 AI가 도와드릴게요!",
  },
  {
    title: "은따거가 누구인가요?",
    description:
      "주식계의 저명한 인사인 은따거에 대해 알아보세요!\n그가 주식을 하게 된 계기와, 전략의 작성까지 은따거가 직접 되어보세요!",
  },
];

export function RecommendedQuestionsSection({
  onQuestionClick,
}: RecommendedQuestionsSectionProps) {
  return (
    <section className="flex flex-col items-center w-full mt-[238px]">
      {/* 섹션 제목 */}
      <h2 className="text-[32px] font-bold text-center mb-20">
        <span className="text-body">혹은 </span>
        <span className="text-brand">추천 질문</span>
        <span className="text-body">으로 시작해보세요!</span>
      </h2>

      {/* 질문 카드 목록 */}
      <div className="flex flex-col items-center gap-[20px] w-full">
        {RECOMMENDED_QUESTIONS.map((question) => (
          <QuestionCard
            key={question.title}
            title={question.title}
            description={question.description}
            onClick={() => onQuestionClick?.(question.title)}
          />
        ))}
      </div>
    </section>
  );
}
