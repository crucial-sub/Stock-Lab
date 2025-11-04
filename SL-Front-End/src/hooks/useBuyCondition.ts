import {
  DEFAULT_COMMISSION_RATE,
  DEFAULT_DATE,
  DEFAULT_INVESTMENT_AMOUNT,
  DEFAULT_MAX_POSITIONS,
  DEFAULT_POSITION_SIZE,
  INITIAL_BUY_CONDITIONS,
} from "@/constants";
import type { BuyCondition, DataType } from "@/types";
import { useState } from "react";

export function useBuyCondition() {
  const [dataType, setDataType] = useState<DataType>("daily");
  const [conditions, setConditions] = useState<BuyCondition[]>(
    INITIAL_BUY_CONDITIONS,
  );
  const [toggles, setToggles] = useState({
    maxPerStock: false,
    maxPerDay: false,
  });

  const addCondition = () => {
    const nextId = String.fromCharCode(65 + conditions.length);
    setConditions([
      ...conditions,
      { id: nextId, expression: "조건식이 표시됩니다." },
    ]);
  };

  const removeCondition = (id: string) => {
    setConditions(conditions.filter((c) => c.id !== id));
  };

  const updateCondition = (id: string, expression: string) => {
    setConditions((prev) =>
      prev.map((c) => (c.id === id ? { ...c, expression } : c)),
    );
  };

  const toggleState = (key: keyof typeof toggles) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return {
    dataType,
    setDataType,
    conditions,
    addCondition,
    removeCondition,
    updateCondition,
    toggles,
    toggleState,
    defaults: {
      investmentAmount: DEFAULT_INVESTMENT_AMOUNT,
      date: DEFAULT_DATE,
      commissionRate: DEFAULT_COMMISSION_RATE,
      positionSize: DEFAULT_POSITION_SIZE,
      maxPositions: DEFAULT_MAX_POSITIONS,
    },
  };
}
