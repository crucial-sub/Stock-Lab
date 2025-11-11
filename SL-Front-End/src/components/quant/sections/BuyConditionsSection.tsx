import { Title } from "@/components/common";
import { useBuyConditionManager } from "@/hooks/quant";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useBacktestConfigStore } from "@/stores";
import Image from "next/image";
import { useState } from "react";
import { ConditionCard, FieldPanel, SectionHeader, UnderLineInput } from "../common";
import { FactorSelectionModal } from "../FactorSelectionModal";

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
    <div id="section-buy-conditions" className="space-y-3">
      <SectionHeader title="매수 조건 설정" />

      <FieldPanel conditionType="buy">
        <div className="space-y-10">
          {/* 매수 조건식 설정 */}
          <div>
            <Title variant="subtitle" className="mb-3">
              매수 조건식 설정
            </Title>

            {/* 조건 목록 */}
            <div className="space-y-2 mb-2">
              {buyConditions.map((condition) => (
                <ConditionCard
                  key={condition.id}
                  condition={condition}
                  expressionText={getConditionExpression(condition)}
                  onFactorSelect={() => openModal(condition.id)}
                  onOperatorChange={(op) => handleOperatorChange(condition.id, op)}
                  onValueChange={(val) => handleValueChange(condition.id, val)}
                  onRemove={() => removeBuyCondition(condition.id)}
                  conditionType="buy"
                />
              ))}
            </div>

            {/* 조건 추가 버튼 */}
            <button
              type="button"
              onClick={addBuyCondition}
              className="w-[31.25rem] h-12 flex items-center gap-3 rounded-md border-[0.5px] relative"
            >
              {/* plus 아이콘 */}
              <div className="">
                <Image
                  src="/icons/plus.svg"
                  alt=""
                  width={48}
                  height={48}
                  className="rounded-tl-md rounded-bl-md"
                />
              </div>

              {/* 텍스트 */}
              <div className="text-tag-neutral">
                조건식을 추가하려면 클릭하세요.
              </div>

              {/* 삭제 아이콘 */}
              <Image
                src="/icons/trash.svg"
                alt=""
                width={24}
                height={24}
                className="absolute right-3 opacity-30"
              />
            </button>
          </div>

          {/* 논리 조건식 */}
          <div>
            <Title variant="subtitle" className="mb-3">
              논리 조건식 작성
            </Title>
            <UnderLineInput
              placeholder="A and B"
              value={buy_logic}
              onChange={(e) => setBuyLogic(e.target.value)}
              className="w-[31.25rem]"
            />
          </div>

          {/* 매수 종목 선택 우선순위 */}
          <div>
            <div className="flex justify-between w-[31.25rem] mb-3">
              <Title variant="subtitle">
                매수 종목 선택 우선순위
              </Title>
              <div className="flex gap-4 justify-center items-center">
                <div className="flex justify-center items-center">
                  <button
                    type="button"
                    onClick={() => setPriorityOrder("desc")}
                    className={`${priority_order === "desc"
                      ? "text-text-strong"
                      : "text-tag-neutral"
                      }`}
                  >
                    높은 값부터
                  </button>
                  <Image
                    src="/icons/arrow_down.svg"
                    alt=""
                    width={16}
                    height={16}
                    className={`${priority_order === "desc"
                      ? "opacity-100"
                      : "opacity-30"
                      }`}
                  />
                </div>
                <div className="flex justify-center items-center">
                  <button
                    type="button"
                    onClick={() => setPriorityOrder("asc")}
                    className={`${priority_order === "asc"
                      ? "text-text-strong"
                      : "text-tag-neutral"
                      }`}
                  >
                    낮은 값부터
                  </button>
                  <Image
                    src="/icons/arrow_up.svg"
                    alt=""
                    width={16}
                    height={16}
                    className={`${priority_order === "asc"
                      ? "opacity-100"
                      : "opacity-30"
                      }`}
                  />
                </div>
              </div>
            </div>
            <div
              onClick={() => setIsPriorityModalOpen(true)}
              className="w-[31.25rem] p-[14px] border-[0.5px] border-tag-neutral rounded-md cursor-pointe hover:border-accent-primary"
            >
              {priorityFactorDisplay || priority_factor || "팩터를 선택해주세요"}
            </div>
          </div>
        </div>
      </FieldPanel>

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
