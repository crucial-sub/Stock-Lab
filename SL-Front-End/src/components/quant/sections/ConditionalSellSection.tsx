import { Dropdown, Title, ToggleSwitch, UnderlineInput } from "@/components/common";
import { ConditionCard, FieldPanel, SectionHeader } from "@/components/quant/ui";
import ActiveConditionBtn from "@/components/quant/ui/ActivateConditionBtn";
import { FactorSelectionModal } from "@/components/quant/FactorSelectionModal";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useBacktestConfigStore } from "@/stores";
import Image from "next/image";
import { useEffect, useState } from "react";

/**
 * 조건 매도 섹션
 * - 매도 조건식 목록
 * - 논리 조건식
 * - 매도 가격 기준
 */
export function ConditionalSellSection() {
  // ✅ backtestConfigStore에서 직접 가져오기
  const {
    sellConditionsUI,
    addSellConditionUI,
    updateSellConditionUI,
    removeSellConditionUI,
    condition_sell,
    setConditionSell,
  } = useBacktestConfigStore((state) => ({
    sellConditionsUI: state.sellConditionsUI,
    addSellConditionUI: state.addSellConditionUI,
    updateSellConditionUI: state.updateSellConditionUI,
    removeSellConditionUI: state.removeSellConditionUI,
    condition_sell: state.condition_sell,
    setConditionSell: state.setConditionSell,
  }));

  const { data: subFactors = [] } = useSubFactorsQuery();
  const { data: factors = [] } = useFactorsQuery();

  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(null);

  // 토글 및 설정 상태
  const [isOpen, setIsOpen] = useState(condition_sell !== null);
  const [sellLogic, setSellLogic] = useState<string>(
    condition_sell?.sell_logic || ""
  );
  const [sellPriceBasis, setSellPriceBasis] = useState<string>(
    condition_sell?.sell_price_basis ?? "전일 종가"
  );
  const [sellPriceOffset, setSellPriceOffset] = useState<number>(
    condition_sell?.sell_price_offset ?? 10
  );

  // 조건 매도 토글 시 초기 조건 추가
  useEffect(() => {
    if (isOpen && sellConditionsUI.length === 0) {
      addSellConditionUI();
    }
  }, [isOpen, sellConditionsUI.length, addSellConditionUI]);

  // 전역 스토어 업데이트
  useEffect(() => {
    if (isOpen) {
      const formattedConditions = sellConditionsUI
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
            exp_right_side: Number(c.value) || 0, // API 명세 확정 후 수정 예정
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
    sellConditionsUI,
    sellLogic,
    sellPriceBasis,
    sellPriceOffset,
    setConditionSell,
  ]);

  // 모달 열기
  const openModal = (id: string) => {
    setCurrentConditionId(id);
    setIsModalOpen(true);
  };

  // 모달 닫기
  const closeModal = () => {
    setIsModalOpen(false);
    setCurrentConditionId(null);
  };

  // 팩터 선택
  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string
  ) => {
    if (!currentConditionId) return;

    const subFactor = subFactors.find((sf) => String(sf.id) === subFactorId);
    const subFactorName = subFactor?.display_name || null;

    updateSellConditionUI(currentConditionId, {
      factorName,
      subFactorName,
      argument,
    });

    closeModal();
  };

  // 연산자 변경
  const handleOperatorChange = (id: string, operator: string) => {
    updateSellConditionUI(id, { operator });
  };

  // 값 변경
  const handleValueChange = (id: string, value: string) => {
    updateSellConditionUI(id, { value });
  };

  // 조건식 텍스트 생성
  const getConditionExpression = (condition: any) => {
    if (!condition.factorName) return '팩터를 선택하세요';

    let text = '';
    if (condition.subFactorName) {
      text = condition.argument
        ? `${condition.subFactorName}({${condition.factorName}},{${condition.argument}})`
        : `${condition.subFactorName}({${condition.factorName}})`;
    } else {
      text = condition.factorName;
    }

    return `${text} ${condition.operator} ${condition.value || '___'}`;
  };

  // 현재 조건 가져오기
  const getCurrentCondition = () => {
    if (!currentConditionId) return undefined;
    const condition = sellConditionsUI.find(c => c.id === currentConditionId);
    if (!condition) return undefined;

    return {
      factorName: condition.factorName || undefined,
      subFactorName: condition.subFactorName || undefined,
      argument: condition.argument,
    };
  };

  return (
    <div id="section-conditional-sell" className="space-y-3">
      <SectionHeader
        title="조건 매도"
        description="본인이 설정한 조건식을 충족했을 때, 매도 주문을 합니다."
        action={<ToggleSwitch checked={isOpen} onChange={setIsOpen} />}
      />

      {isOpen ? (
        <FieldPanel conditionType="sell">
          <div className="space-y-10">
            {/* 매도 조건식 설정 */}
            <div>
              <Title variant="subtitle" className="mb-3">
                매도 조건식 설정
              </Title>

              {/* 조건 목록 */}
              <div className="space-y-2 mb-2">
                {sellConditionsUI.map((condition) => (
                  <ConditionCard
                    key={condition.id}
                    condition={condition}
                    expressionText={getConditionExpression(condition)}
                    onFactorSelect={() => openModal(condition.id)}
                    onOperatorChange={(op) => handleOperatorChange(condition.id, op)}
                    onValueChange={(val) => handleValueChange(condition.id, val)}
                    onRemove={() => removeSellConditionUI(condition.id)}
                    conditionType="sell"
                  />
                ))}
              </div>

              {/* 조건 추가 버튼 */}
              <button
                type="button"
                onClick={addSellConditionUI}
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
              <UnderlineInput
                placeholder="A and B"
                value={sellLogic}
                onChange={(e) => setSellLogic(e.target.value)}
                className="w-[31.25rem]"
              />
            </div>

            {/* 매도 가격 기준 */}
            <div>
              <Title variant="subtitle" className="mb-3">
                매도 가격 기준
              </Title>
              <div className="flex gap-4 items-center">
                <Dropdown
                  value={sellPriceBasis}
                  options={[
                    { value: "전일 종가", label: "전일 종가" },
                    { value: "당일 시가", label: "당일 시가" },
                  ]}
                  onChange={setSellPriceBasis}
                  variant="medium"
                />
                <div className="relative">
                  <UnderlineInput
                    value={sellPriceOffset}
                    onChange={(e) => setSellPriceOffset(Number(e.target.value))}
                    className="w-32"
                  />
                  <span className="absolute right-0 bottom-[0.625rem]">
                    %
                  </span>
                </div>
              </div>
            </div>
          </div>
        </FieldPanel>
      ) : (
        <ActiveConditionBtn checked={isOpen} onChange={setIsOpen} />
      )}

      {/* 매도 조건식 팩터 선택 모달 */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition() as any}
      />
    </div>
  );
}
