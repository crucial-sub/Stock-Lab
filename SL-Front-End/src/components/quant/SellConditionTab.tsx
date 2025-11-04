"use client";

import { Input, Panel, Toggle } from "@/components/common";
import { useSellCondition } from "@/hooks";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";

/**
 * 매도 조건 설정 탭 컴포넌트
 *
 * BacktestRunRequest의 매도 조건 형식에 맞춰 데이터를 저장합니다:
 * - target_and_loss: { target_gain, stop_loss } | null
 * - hold_days: { min_hold_days, max_hold_days, sell_cost_basis } | null
 * - sell_conditions: { name, expression, sell_logic, sell_cost_basis } | null
 */
export function SellConditionTab() {
  const { toggles, toggleState } = useSellCondition();

  // 전역 백테스트 설정 스토어
  const {
    target_and_loss,
    setTargetAndLoss,
    hold_days,
    setHoldDays,
    sell_conditions,
    setSellConditions,
  } = useBacktestConfigStore();

  // 목표가/손절가 입력값 (내부 상태)
  const [targetGain, setTargetGainValue] = useState<number>(
    target_and_loss?.target_gain ?? 0,
  );
  const [stopLoss, setStopLossValue] = useState<number>(
    target_and_loss?.stop_loss ?? 0,
  );

  // 보유 기간 입력값 (내부 상태)
  const [minHoldDays, setMinHoldDays] = useState<number>(
    hold_days?.min_hold_days ?? 0,
  );
  const [maxHoldDays, setMaxHoldDays] = useState<number>(
    hold_days?.max_hold_days ?? 0,
  );
  const [holdSellCostBasis, setHoldSellCostBasis] =
    useState<string>("{전일 종가}");
  const [holdSellCostBasisValue, setHoldSellCostBasisValue] =
    useState<number>(0);

  // 조건 매도 입력값 (내부 상태)
  const [sellConditionName, setSellConditionName] = useState<string>(
    sell_conditions?.name ?? "A",
  );
  const [sellConditionExpression, setSellConditionExpression] =
    useState<string>(sell_conditions?.expression ?? "");
  const [sellLogic, setSellLogic] = useState<string>(
    sell_conditions?.sell_logic ?? "",
  );
  const [condSellCostBasis, setCondSellCostBasis] =
    useState<string>("{전일 종가}");
  const [condSellCostBasisValue, setCondSellCostBasisValue] =
    useState<number>(0);

  /**
   * 목표가/손절가 토글 및 값 변경 시 전역 스토어 업데이트
   */
  useEffect(() => {
    if (toggles.profitTarget || toggles.stopLoss) {
      setTargetAndLoss({
        target_gain: toggles.profitTarget ? targetGain : null,
        stop_loss: toggles.stopLoss ? stopLoss : null,
      });
    } else {
      setTargetAndLoss(null);
    }
  }, [
    toggles.profitTarget,
    toggles.stopLoss,
    targetGain,
    stopLoss,
    setTargetAndLoss,
  ]);

  /**
   * 보유 기간 토글 및 값 변경 시 전역 스토어 업데이트
   */
  useEffect(() => {
    if (toggles.holdingPeriod) {
      const sellBasis = `${holdSellCostBasis} ${holdSellCostBasisValue}`;
      setHoldDays({
        min_hold_days: minHoldDays,
        max_hold_days: maxHoldDays,
        sell_cost_basis: sellBasis,
      });
    } else {
      setHoldDays(null);
    }
  }, [
    toggles.holdingPeriod,
    minHoldDays,
    maxHoldDays,
    holdSellCostBasis,
    holdSellCostBasisValue,
    setHoldDays,
  ]);

  /**
   * 조건 매도 토글 및 값 변경 시 전역 스토어 업데이트
   */
  useEffect(() => {
    if (toggles.conditionalSell) {
      const sellBasis = `${condSellCostBasis} ${condSellCostBasisValue}`;
      setSellConditions({
        name: sellConditionName,
        expression: sellConditionExpression,
        sell_logic: sellLogic,
        sell_cost_basis: sellBasis,
      });
    } else {
      setSellConditions(null);
    }
  }, [
    toggles.conditionalSell,
    sellConditionName,
    sellConditionExpression,
    sellLogic,
    condSellCostBasis,
    condSellCostBasisValue,
    setSellConditions,
  ]);

  return (
    <div className="space-y-6">
      {/* 목표가 / 손절가 */}
      <Panel className="p-6 space-y-4">
        <h3 className="text-base font-semibold text-text-primary">
          목표가 / 손절가
        </h3>

        <div className="grid grid-cols-2 gap-6">
          {/* Profit Target */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm text-text-secondary">
              <span>목표가</span>
              <Toggle
                enabled={toggles.profitTarget}
                onChange={() => toggleState("profitTarget")}
                label="목표가"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-secondary whitespace-nowrap">
                매수가 대비
              </span>
              <Input
                type="number"
                value={targetGain}
                onChange={(e) => setTargetGainValue(Number(e.target.value))}
                disabled={!toggles.profitTarget}
                suffix="%"
                className="flex-1"
              />
              <span className="text-sm text-text-secondary whitespace-nowrap">
                상승 시 매도 주문
              </span>
            </div>
          </div>

          {/* Stop Loss */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm text-text-secondary">
              <span>손절가</span>
              <Toggle
                enabled={toggles.stopLoss}
                onChange={() => toggleState("stopLoss")}
                label="손절가"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-text-secondary whitespace-nowrap">
                매수가 대비
              </span>
              <Input
                type="number"
                value={stopLoss}
                onChange={(e) => setStopLossValue(Number(e.target.value))}
                disabled={!toggles.stopLoss}
                suffix="%"
                className="flex-1"
              />
              <span className="text-sm text-text-secondary whitespace-nowrap">
                손실 시 매도 주문
              </span>
            </div>
          </div>
        </div>
      </Panel>

      {/* 보유 기간 */}
      <Panel className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-text-primary">
            보유 기간
          </h3>
          <Toggle
            enabled={toggles.holdingPeriod}
            onChange={() => toggleState("holdingPeriod")}
            label="보유 기간"
          />
        </div>

        {toggles.holdingPeriod && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  최소 보유 기간 (일)
                </div>
                <Input
                  type="number"
                  value={minHoldDays}
                  onChange={(e) => setMinHoldDays(Number(e.target.value))}
                  suffix="일"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  최대 보유 기간 (일)
                </div>
                <Input
                  type="number"
                  value={maxHoldDays}
                  onChange={(e) => setMaxHoldDays(Number(e.target.value))}
                  suffix="일"
                  className="w-full"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  매도 가격 기준
                </div>
                <select
                  value={holdSellCostBasis}
                  onChange={(e) => setHoldSellCostBasis(e.target.value)}
                  className="quant-input w-full"
                >
                  <option value="{전일 종가}">전일 종가</option>
                  <option value="{당일 시가}">당일 시가</option>
                </select>
              </div>
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  가격 조정 비율
                </div>
                <Input
                  type="number"
                  value={holdSellCostBasisValue}
                  onChange={(e) =>
                    setHoldSellCostBasisValue(Number(e.target.value))
                  }
                  suffix="%"
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}
      </Panel>

      {/* 조건 매도 */}
      <Panel className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-text-primary">
            조건 매도
          </h3>
          <Toggle
            enabled={toggles.conditionalSell}
            onChange={() => toggleState("conditionalSell")}
            label="조건 매도"
          />
        </div>

        {toggles.conditionalSell && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  조건식 이름
                </div>
                <Input
                  type="text"
                  value={sellConditionName}
                  onChange={(e) => setSellConditionName(e.target.value)}
                  placeholder="예: A"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">조건식</div>
                <Input
                  type="text"
                  value={sellConditionExpression}
                  onChange={(e) => setSellConditionExpression(e.target.value)}
                  placeholder="예: {PER} > 10"
                  className="w-full"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="block text-sm text-text-secondary">
                논리 조건식
              </div>
              <Input
                type="text"
                value={sellLogic}
                onChange={(e) => setSellLogic(e.target.value)}
                placeholder="예: A and B"
                className="w-full"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  매도 가격 기준
                </div>
                <select
                  value={condSellCostBasis}
                  onChange={(e) => setCondSellCostBasis(e.target.value)}
                  className="quant-input w-full"
                >
                  <option value="{전일 종가}">전일 종가</option>
                  <option value="{당일 시가}">당일 시가</option>
                </select>
              </div>
              <div className="space-y-2">
                <div className="block text-sm text-text-secondary">
                  가격 조정 비율
                </div>
                <Input
                  type="number"
                  value={condSellCostBasisValue}
                  onChange={(e) =>
                    setCondSellCostBasisValue(Number(e.target.value))
                  }
                  suffix="%"
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
