"use client";

import { AISearchInput } from "../ui";

/**
 * 홈 화면 환영 섹션
 *
 * @description 홈 화면 상단의 환영 메시지와 AI 입력창을 포함하는 섹션입니다.
 * 사용자 이름을 동적으로 표시하고, AI 전략 요청을 입력받습니다.
 *
 * @example
 * ```tsx
 * <WelcomeSection
 *   userName="은따거"
 *   onSubmit={(value) => console.log("AI 요청:", value)}
 * />
 * ```
 */

interface WelcomeSectionProps {
  /** 사용자 닉네임 */
  nickname?: string;
  /** AI 입력 전송 시 호출되는 콜백 함수 */
  onSubmit?: (value: string) => void;
}

export function WelcomeSection({
  nickname = "은따거",
  onSubmit,
}: WelcomeSectionProps) {
  return (
    <section className="flex flex-col items-center w-full">
      {/* 환영 메시지 */}
      <h1 className="text-[32px] font-bold text-center mb-20">
        <span className="text-body">{nickname}님, 오늘도 </span>
        <span className="text-brand">수익</span>
        <span className="text-body">을 내볼까요?</span>
      </h1>

      {/* AI 검색 입력창 */}
      <AISearchInput
        placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
        onSubmit={onSubmit}
      />
    </section>
  );
}
