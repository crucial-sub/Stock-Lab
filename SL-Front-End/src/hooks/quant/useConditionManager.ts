import { useConditionStore, useBacktestConfigStore } from "@/stores";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import { useState, useEffect } from "react";

/**
 * 조건식 관리 커스텀 훅
 * - 매수/매도 조건식 관리 로직을 캡슐화
 * - 팩터 선택 모달 상태 관리
 * - 조건식과 전역 스토어 동기화
 */
export function useBuyConditionManager() {
  const { data: subFactors = [] } = useSubFactorsQuery();
  const { setBuyConditions } = useBacktestConfigStore();
  const {
    buyConditions,
    updateBuyCondition,
    addBuyCondition,
    removeBuyCondition,
    getConditionExpression,
  } = useConditionStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null
  );

  // 조건식을 백테스트 설정 스토어에 동기화
  useEffect(() => {
    const formattedConditions = buyConditions
      .filter((c) => c.factorName !== null)
      .map((c) => {
        // exp_left_side 생성: 서브팩터가 있으면 "서브팩터({팩터},{인자})", 없으면 "{팩터}"
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
    setBuyConditions(formattedConditions);
  }, [buyConditions, setBuyConditions]);

  // 팩터 선택 핸들러
  const openModal = (id: string) => {
    setCurrentConditionId(id);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setCurrentConditionId(null);
  };

  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string
  ) => {
    if (currentConditionId) {
      // subFactorId로 subFactorName 찾기
      const subFactor = subFactors.find((sf) => String(sf.id) === subFactorId);
      const subFactorName = subFactor?.display_name;

      updateBuyCondition(currentConditionId, {
        factorId,
        factorName,
        subFactorId,
        subFactorName,
        argument,
      });
    }
    closeModal();
  };

  const getCurrentCondition = () => {
    if (!currentConditionId) return undefined;
    const condition = buyConditions.find((c) => c.id === currentConditionId);
    if (!condition || !condition.factorId) return undefined;
    return {
      factorId: condition.factorId,
      subFactorId: condition.subFactorId,
    };
  };

  const handleOperatorChange = (
    id: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!="
  ) => {
    updateBuyCondition(id, { operator });
  };

  const handleValueChange = (id: string, value: number) => {
    updateBuyCondition(id, { value });
  };

  return {
    buyConditions,
    isModalOpen,
    currentConditionId,
    openModal,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
    handleOperatorChange,
    handleValueChange,
    addBuyCondition,
    removeBuyCondition,
    getConditionExpression,
  };
}

/**
 * 매도 조건 관리 커스텀 훅
 */
export function useSellConditionManager() {
  const { data: subFactors = [] } = useSubFactorsQuery();
  const { setConditionSell } = useBacktestConfigStore();
  const {
    sellConditions,
    updateSellCondition,
    addSellCondition,
    removeSellCondition,
    getConditionExpression,
  } = useConditionStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null
  );

  // 팩터 선택 핸들러
  const openModal = (id: string) => {
    setCurrentConditionId(id);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setCurrentConditionId(null);
  };

  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string
  ) => {
    if (currentConditionId) {
      const subFactor = subFactors.find((sf) => String(sf.id) === subFactorId);
      const subFactorName = subFactor?.display_name;

      updateSellCondition(currentConditionId, {
        factorId,
        factorName,
        subFactorId,
        subFactorName,
        argument,
      });
    }
    closeModal();
  };

  const getCurrentCondition = () => {
    if (!currentConditionId) return undefined;
    const condition = sellConditions.find((c) => c.id === currentConditionId);
    if (!condition || !condition.factorId) return undefined;
    return {
      factorId: condition.factorId,
      subFactorId: condition.subFactorId,
    };
  };

  const handleOperatorChange = (
    id: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!="
  ) => {
    updateSellCondition(id, { operator });
  };

  const handleValueChange = (id: string, value: number) => {
    updateSellCondition(id, { value });
  };

  return {
    sellConditions,
    isModalOpen,
    currentConditionId,
    openModal,
    closeModal,
    handleFactorSelect,
    getCurrentCondition,
    handleOperatorChange,
    handleValueChange,
    addSellCondition,
    removeSellCondition,
    getConditionExpression,
  };
}
