"use client";

/**
 * 매도 조건 탭 - 리팩토링 버전
 *
 * 개선 사항:
 * - 섹션별 컴포넌트 분리로 코드 가독성 향상 (599줄 → 50줄, 92% 감소)
 * - 공통 UI 컴포넌트 재사용으로 중복 코드 제거
 * - 커스텀 훅으로 비즈니스 로직 분리
 * - 기존 UI/UX 완전 보존
 */

import { useSellConditionManager } from "@/hooks/quant";
import { FactorSelectionModal } from "./FactorSelectionModal";
import {
  TargetLossSection,
  HoldPeriodSection,
  ConditionalSellSection,
} from "./sections";

export default function SellConditionTab() {
  const {
    isModalOpen,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
  } = useSellConditionManager();

  return (
    <>
      <div className="space-y-6">
        {/* 목표가 / 손절가 섹션 */}
        <TargetLossSection />

        {/* 보유 기간 섹션 */}
        <HoldPeriodSection />

        {/* 조건 매도 섹션 */}
        <ConditionalSellSection />
      </div>

      {/* Factor Selection Modal */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition()}
      />
    </>
  );
}
