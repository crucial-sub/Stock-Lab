import { useState, useEffect } from "react";
import { useBacktestConfigStore } from "@/stores";
import { useSellConditionManager } from "@/hooks/quant";
import { SectionHeader, ToggleSwitch, ConditionCard } from "../common";
import { FactorSelectionModal } from "../FactorSelectionModal";

/**
 * 조건 매도 섹션
 * - 매도 조건식 목록
 * - 논리 조건식
 * - 매도 가격 기준
 */
export function ConditionalSellSection() {
  const { condition_sell, setConditionSell } = useBacktestConfigStore();

  const {
    sellConditions,
    isModalOpen,
    openModal,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
    handleOperatorChange,
    handleValueChange,
    addSellCondition,
    removeSellCondition,
    getConditionExpression,
  } = useSellConditionManager();

  const [isOpen, setIsOpen] = useState(condition_sell !== null);
  const [sellLogic, setSellLogic] = useState<string>(
    condition_sell?.sell_logic ?? "A and B"
  );
  const [sellPriceBasis, setSellPriceBasis] = useState<string>(
    condition_sell?.sell_price_basis ?? "전일 종가"
  );
  const [sellPriceOffset, setSellPriceOffset] = useState<number>(
    condition_sell?.sell_price_offset ?? 10
  );

  // 조건 매도 토글 시 초기 조건 추가
  useEffect(() => {
    if (isOpen && sellConditions.length === 0) {
      addSellCondition();
      addSellCondition();
    }
  }, [isOpen]);

  // 전역 스토어 업데이트
  useEffect(() => {
    if (isOpen) {
      const formattedConditions = sellConditions
        .filter((c) => c.factorName !== null)
        .map((c) => {
          let expLeftSide = "";
          if (c.subFactorName) {
            if (c.argument) {
              expLeftSide = `${c.subFactorName}({${c.factorName}},{${c.argument}})`;
            } else {
              expLeftSide = `${c.subFactorName}({${c.factorName}})`;
            }
          } else {
            expLeftSide = `{${c.factorName}}`;
          }

          return {
            name: c.id,
            exp_left_side: expLeftSide,
            inequality: c.operator,
            exp_right_side: c.value,
          };
        });

      setConditionSell({
        sell_conditions: formattedConditions,
        sell_logic: sellLogic,
        sell_price_basis: sellPriceBasis,
        sell_price_offset: sellPriceOffset,
      });
    } else {
      setConditionSell(null);
    }
  }, [
    isOpen,
    sellConditions,
    sellLogic,
    sellPriceBasis,
    sellPriceOffset,
    setConditionSell,
  ]);

  return (
    <div className="space-y-3">
      <SectionHeader
        title="조건 매도"
        description="변경된 상영한 조건식을 충족했을 때도 주문을 합니다."
        action={<ToggleSwitch checked={isOpen} onChange={setIsOpen} />}
      />

      {isOpen && (
        <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-secondary">
          <div className="space-y-6">
            {/* 매도 조건식 설정 */}
            <div>
              <h4 className="text-base font-semibold text-text-strong mb-3">
                매도 조건식 설정
              </h4>
              <div className="space-y-3">
                {sellConditions.map((condition) => (
                  <ConditionCard
                    key={condition.id}
                    condition={condition}
                    expressionText={getConditionExpression(condition)}
                    onFactorSelect={() => openModal(condition.id)}
                    onOperatorChange={(op) => handleOperatorChange(condition.id, op)}
                    onValueChange={(val) => handleValueChange(condition.id, val)}
                    onRemove={() => removeSellCondition(condition.id)}
                  />
                ))}

                {/* 조건식 추가 버튼 */}
                <button
                  type="button"
                  onClick={addSellCondition}
                  className="w-full py-3 border border-white rounded-md text-white text-sm font-medium hover:bg-white hover:bg-opacity-20 transition-colors"
                >
                  조건식을 추가하려면 클릭하세요.
                </button>
              </div>
            </div>

            {/* 논리 조건식 */}
            <div className="border-t border-border-subtle pt-4">
              <div className="flex items-center gap-3">
                <h4 className="text-base font-semibold text-text-strong">
                  논리 조건식
                </h4>
                <input
                  type="text"
                  placeholder="논리 조건식을 입력해주세요."
                  value={sellLogic}
                  onChange={(e) => setSellLogic(e.target.value)}
                  className="w-64 px-3 py-2 bg-transparent border-b border-text-muted text-text-strong placeholder:text-text-muted"
                />
              </div>
            </div>

            {/* 매도 가격 기준 */}
            <div className="flex items-center gap-3">
              <h4 className="text-base font-semibold text-text-strong">
                매도 가격 기준
              </h4>
              <select
                value={sellPriceBasis}
                onChange={(e) => setSellPriceBasis(e.target.value)}
                className="px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong appearance-none cursor-pointer"
              >
                <option value="전일 종가">전일 종가</option>
                <option value="당일 시가">당일 시가</option>
              </select>
              <input
                type="number"
                value={sellPriceOffset}
                onChange={(e) => setSellPriceOffset(Number(e.target.value))}
                className="w-24 px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong"
              />
              <span className="text-sm text-text-body">%</span>
            </div>
          </div>
        </div>
      )}

      {/* 매도 조건식 팩터 선택 모달 */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition()}
      />
    </div>
  );
}
