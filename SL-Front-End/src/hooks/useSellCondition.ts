import { useState } from "react";
import { DEFAULT_PROFIT_TARGET, DEFAULT_STOP_LOSS } from "@/constants";

export function useSellCondition() {
  const [toggles, setToggles] = useState({
    profitTarget: true,
    stopLoss: false,
    holdingPeriod: true,
    conditionalSell: true,
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
