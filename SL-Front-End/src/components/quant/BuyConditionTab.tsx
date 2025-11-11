"use client";

/**
 * 매수 조건 탭 - 리팩토링 버전
 *
 * 개선 사항:
 * - 섹션별 컴포넌트 분리로 코드 가독성 향상
 * - 공통 UI 컴포넌트 재사용으로 중복 코드 제거
 * - 커스텀 훅으로 비즈니스 로직 분리
 * - 기존 UI/UX 완전 보존
 */

import { useBuyConditionManager } from "@/hooks/quant";
import { FactorSelectionModal } from "./FactorSelectionModal";
import {
  BuyConditionsSection,
  BuyMethodSection,
  BuyWeightSection,
  GeneralSettingsSection,
} from "./sections";

export default function BuyConditionTab() {
  const {
    isModalOpen,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
  } = useBuyConditionManager();

  return (
    <>
      {/* Main Content */}
      <div className="space-y-6">
        {/* 일반 조건 설정 */}
        <GeneralSettingsSection />

        {/* 매수 조건 설정 */}
        <BuyConditionsSection />

        {/* 매수 비중 설정 */}
        <BuyWeightSection />

        {/* 매수 방법 선택 */}
        <BuyMethodSection />
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
