import { useState, useEffect } from "react";
import { useBacktestConfigStore } from "@/stores";
import { useBuyConditionManager } from "@/hooks/quant";
import { ConditionCard, SectionHeader } from "../common";
import { FactorSelectionModal } from "../FactorSelectionModal";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";

/**
 * 매수 조건식 설정 섹션
 * - 조건식 목록 관리
 * - 논리 조건식 작성
 * - 매수 종목 선택 우선순위 (팩터 선택 모달 사용)
 */
export function BuyConditionsSection() {
  const { buy_logic, setBuyLogic, priority_factor, setPriorityFactor, priority_order, setPriorityOrder } =
    useBacktestConfigStore();

  const { data: subFactors = [] } = useSubFactorsQuery();
  const { data: factors = [] } = useFactorsQuery();

  // 우선순위 팩터 기본값 설정 (최초 1회만)
  useEffect(() => {
    if (!priority_factor && factors.length > 0) {
      // PER 팩터를 기본값으로 설정
      const defaultFactor = factors.find(f => f.name === 'per') || factors[0];
      if (defaultFactor) {
        setPriorityFactor(`{${defaultFactor.display_name}}`);
        setPriorityFactorDisplay(defaultFactor.display_name);
      }
    }
  }, [factors, priority_factor, setPriorityFactor]);

  const {
    buyConditions,
    isModalOpen,
    openModal,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
    handleOperatorChange,
    handleValueChange,
    addBuyCondition,
    removeBuyCondition,
    getConditionExpression,
  } = useBuyConditionManager();

  // 우선순위 팩터 선택 모달 상태
  const [isPriorityModalOpen, setIsPriorityModalOpen] = useState(false);
  const [priorityFactorDisplay, setPriorityFactorDisplay] = useState<string>("");

  const handlePriorityFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string
  ) => {
    // subFactorId로 subFactorName 찾기
    const subFactor = subFactors.find((sf) => String(sf.id) === subFactorId);
    const subFactorName = subFactor?.display_name;

    // 팩터 표현식 생성
    let expression = "";
    let displayText = "";
    if (subFactorName) {
      if (argument) {
        expression = `${subFactorName}({${factorName}},{${argument}})`;
        displayText = `${subFactorName}({${factorName}},{${argument}})`;
      } else {
        expression = `${subFactorName}({${factorName}})`;
        displayText = `${subFactorName}({${factorName}})`;
      }
    } else {
      expression = `{${factorName}}`;
      displayText = factorName;
    }

    setPriorityFactor(expression);
    setPriorityFactorDisplay(displayText);
    setIsPriorityModalOpen(false);
  };

  return (
    <div className="space-y-3">
      <SectionHeader title="매수 조건 설정" />

      <div className="bg-bg-surface rounded-lg shadow-card p-8 border-l-4 border-brand-primary">
        <div className="space-y-6">
        {/* 매수 조건식 설정 */}
        <div>
          <label className="block text-base font-medium text-text-strong mb-4">
            매수 조건식 설정
          </label>

          {/* 조건 목록 */}
          <div className="space-y-3 mb-4">
            {buyConditions.map((condition) => (
              <ConditionCard
                key={condition.id}
                condition={condition}
                expressionText={getConditionExpression(condition)}
                onFactorSelect={() => openModal(condition.id)}
                onOperatorChange={(op) => handleOperatorChange(condition.id, op)}
                onValueChange={(val) => handleValueChange(condition.id, val)}
                onRemove={() => removeBuyCondition(condition.id)}
              />
            ))}
          </div>

          {/* 조건 추가 버튼 */}
          <div className="flex justify-center">
            <button
              type="button"
              onClick={addBuyCondition}
              className="px-6 py-2 border-2 border-dashed border-border-default text-text-muted rounded-lg hover:border-accent-primary hover:text-accent-primary transition-colors font-medium"
            >
              + 조건식 추가
            </button>
          </div>
        </div>

        <div className="h-px bg-border-subtle" />

        {/* 논리 조건식 */}
        <div>
          <label className="block text-sm font-medium text-text-strong mb-2">
            논리 조건식 작성
          </label>
          <input
            type="text"
            placeholder="A and B"
            value={buy_logic}
            onChange={(e) => setBuyLogic(e.target.value)}
            className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
          />
        </div>

        <div className="h-px bg-border-subtle" />

        {/* 매수 종목 선택 우선순위 */}
        <div>
          <label className="block text-sm font-medium text-text-strong mb-2">
            매수 종목 선택 우선순위
          </label>
          <div className="flex gap-2">
            <div
              onClick={() => setIsPriorityModalOpen(true)}
              className="flex-1 px-3 py-2 border border-border-default rounded-sm text-text-body hover:border-accent-primary cursor-pointer transition-colors"
            >
              {priorityFactorDisplay || priority_factor || "팩터를 선택해주세요"}
            </div>
            <select
              value={priority_order}
              onChange={(e) => setPriorityOrder(e.target.value)}
              className="px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
            >
              <option value="desc">내림차순</option>
              <option value="asc">오름차순</option>
            </select>
          </div>
        </div>
      </div>
      </div>

      {/* 매수 조건식 팩터 선택 모달 */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition()}
      />

      {/* 우선순위 팩터 선택 모달 */}
      <FactorSelectionModal
        isOpen={isPriorityModalOpen}
        onClose={() => setIsPriorityModalOpen(false)}
        onSelect={handlePriorityFactorSelect}
      />
    </div>
  );
}
