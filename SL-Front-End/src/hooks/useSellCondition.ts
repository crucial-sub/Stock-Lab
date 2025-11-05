import { useState } from "react";
import { DEFAULT_PROFIT_TARGET, DEFAULT_STOP_LOSS } from "@/constants";

export function useSellCondition() {
  const [toggles, setToggles] = useState({
    targetAndLoss: true, // 목표가/손절가 전체 토글 (default: ON)
    profitTarget: true, // 목표가 개별 토글 (default: ON)
    stopLoss: true, // 손절가 개별 토글 (default: ON)
    holdingPeriod: false, // 보유 기간 (default: OFF)
    conditionalSell: false, // 조건 매도 (default: OFF)
  });

  const toggleState = (key: keyof typeof toggles) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return {
    toggles,
    toggleState,
    defaults: {
      profitTarget: DEFAULT_PROFIT_TARGET,
      stopLoss: DEFAULT_STOP_LOSS,
    },
  };
}
