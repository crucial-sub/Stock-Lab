import { Title, UnderlineInput } from "@/components/common";
import { FactorSelectionModal } from "@/components/quant/FactorSelectionModal";
import {
  ConditionCard,
  FieldPanel,
  SectionHeader,
} from "@/components/quant/ui";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useBacktestConfigStore } from "@/stores";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";

/**
 * 매수 조건식 설정 섹션
 * - 조건식 목록 관리
 * - 논리 조건식 작성
 * - 매수 종목 선택 우선순위 (팩터 선택 모달 사용)
 */
export function BuyConditionsSection() {
  // ✅ useShallow hook 사용 (데이터와 함수 분리)
  const { buyConditionsUI, buy_logic, priority_factor, priority_order } =
    useBacktestConfigStore(
      useShallow((state) => ({
        buyConditionsUI: state.buyConditionsUI,
        buy_logic: state.buy_logic,
        priority_factor: state.priority_factor,
        priority_order: state.priority_order,
      }))
    );

  // 함수들은 별도로 선택 (안정적인 참조)
  const addBuyConditionUI = useBacktestConfigStore(
    (state) => state.addBuyConditionUI
  );
  const updateBuyConditionUI = useBacktestConfigStore(
    (state) => state.updateBuyConditionUI
  );
  const removeBuyConditionUI = useBacktestConfigStore(
    (state) => state.removeBuyConditionUI
  );
  const setBuyLogic = useBacktestConfigStore((state) => state.setBuyLogic);
  const setPriorityFactor = useBacktestConfigStore(
    (state) => state.setPriorityFactor
  );
  const setPriorityOrder = useBacktestConfigStore(
    (state) => state.setPriorityOrder
  );

  const { data: subFactors = [] } = useSubFactorsQuery();
  const { data: factors = [] } = useFactorsQuery();

  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null
  );

  // 우선순위 팩터 선택 모달 상태
  const [isPriorityModalOpen, setIsPriorityModalOpen] = useState(false);
  const [priorityFactorDisplay, setPriorityFactorDisplay] =
    useState<string>("");

  // 우선순위 팩터 기본값 설정 (최초 1회만)
  useEffect(() => {
    if (!priority_factor && factors.length > 0) {
      // PER 팩터를 기본값으로 설정
      const defaultFactor = factors.find((f) => f.name === "per") || factors[0];
      if (defaultFactor) {
        setPriorityFactor(`{${defaultFactor.display_name}}`);
        setPriorityFactorDisplay(defaultFactor.display_name);
      }
    }
  }, [factors, priority_factor, setPriorityFactor]);

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

    updateBuyConditionUI(currentConditionId, {
      factorName,
      subFactorName,
      argument,
    });

    closeModal();
  };

  // 연산자 변경
  const handleOperatorChange = (id: string, operator: string) => {
    updateBuyConditionUI(id, { operator });
  };

  // 값 변경
  const handleValueChange = (id: string, value: string) => {
    updateBuyConditionUI(id, { value });
  };

  // 조건식 텍스트 생성
  const getConditionExpression = (condition: any) => {
    if (!condition.factorName) return "팩터를 선택하세요";

    let text = "";
    if (condition.subFactorName) {
      text = condition.argument
        ? `${condition.subFactorName}({${condition.factorName}},{${condition.argument}})`
        : `${condition.subFactorName}({${condition.factorName}})`;
    } else {
      text = condition.factorName;
    }

    return `${text} ${condition.operator} ${condition.value || "___"}`;
  };

  // 현재 조건 가져오기
  const getCurrentCondition = () => {
    if (!currentConditionId) return undefined;
    const condition = buyConditionsUI.find((c) => c.id === currentConditionId);
    if (!condition) return undefined;

    return {
      factorName: condition.factorName || undefined,
      subFactorName: condition.subFactorName || undefined,
      argument: condition.argument,
    };
  };

  // 우선순위 팩터 선택
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
              {buyConditionsUI.map((condition) => (
                <ConditionCard
                  key={condition.id}
                  condition={condition}
                  expressionText={getConditionExpression(condition)}
                  onFactorSelect={() => openModal(condition.id)}
                  onOperatorChange={(op) =>
                    handleOperatorChange(condition.id, op)
                  }
                  onValueChange={(val) => handleValueChange(condition.id, val)}
                  onRemove={() => removeBuyConditionUI(condition.id)}
                  conditionType="buy"
                />
              ))}
            </div>

            {/* 조건 추가 버튼 */}
            <button
              type="button"
              onClick={addBuyConditionUI}
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
              value={buy_logic}
              onChange={(e) => setBuyLogic(e.target.value)}
              className="w-[31.25rem]"
            />
          </div>

          {/* 매수 종목 선택 우선순위 */}
          <div>
            <div className="flex justify-between w-[31.25rem] mb-3">
              <Title variant="subtitle">매수 종목 선택 우선순위</Title>
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
                    className={`${priority_order === "desc" ? "opacity-100" : "opacity-30"
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
                    className={`${priority_order === "asc" ? "opacity-100" : "opacity-30"
                      }`}
                  />
                </div>
              </div>
            </div>
            <div
              onClick={() => setIsPriorityModalOpen(true)}
              className="w-[31.25rem] p-[14px] border-[0.5px] border-tag-neutral rounded-md cursor-pointer hover:border-accent-primary"
            >
              {priorityFactorDisplay ||
                priority_factor ||
                "팩터를 선택해주세요"}
            </div>
          </div>
        </div>
      </FieldPanel>

      {/* 매수 조건식 팩터 선택 모달 */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={closeModal}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition() as any}
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
