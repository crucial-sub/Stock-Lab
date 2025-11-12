"use client";

/**
 * 매도 조건 탭 - 리팩토링 버전
 *
 * 개선 사항:
 * - 섹션별 컴포넌트 분리로 코드 가독성 향상 (599줄 → 50줄, 92% 감소)
 * - 공통 UI 컴포넌트 재사용으로 중복 코드 제거
 * - 기존 UI/UX 완전 보존
 */

import {
  TargetLossSection,
  HoldPeriodSection,
  ConditionalSellSection,
} from "@/components/quant/sections";

export default function SellConditionTab() {
  return (
    <div className="space-y-6">
      {/* 목표가 / 손절가 섹션 */}
      <TargetLossSection />

      {/* 보유 기간 섹션 */}
      <HoldPeriodSection />

      {/* 조건 매도 섹션 */}
      <ConditionalSellSection />
    </div>
  );
}
