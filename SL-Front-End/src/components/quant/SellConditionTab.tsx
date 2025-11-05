"use client";

import {
  CustomSelect,
  GradientDivider,
  Panel,
  Title,
  UnderlineInput,
} from "@/components/common";
import { SVG_PATH } from "@/constants";
import { useSellCondition } from "@/hooks";
import { useBacktestConfigStore, useConditionStore } from "@/stores";
import { useEffect, useState } from "react";
import { FactorSelectionModal } from "./FactorSelectionModal";

/**
 * 매도 조건 설정 탭 컴포넌트
 *
 * 주요 기능:
 * 1. 목표가/손절가 설정 (토글 가능, target_and_loss)
 * 2. 보유 기간 설정 (토글 가능, hold_days)
 * 3. 조건 매도 설정 (토글 가능, condition_sell)
 *    - 매수 조건과 동일한 UI: 팩터 선택, 부등호, 값 입력
 *
 * 모든 설정값은 useBacktestConfigStore에 저장되며
 * BacktestRunRequest 형식과 완벽하게 일치합니다.
 */
export function SellConditionTab() {
  const { toggles, toggleState } = useSellCondition();

  // 전역 백테스트 설정 스토어
  const {
    target_and_loss,
    setTargetAndLoss,
    hold_days,
    setHoldDays,
    condition_sell,
    setConditionSell,
  } = useBacktestConfigStore();

  // Zustand 스토어에서 매도 조건 가져오기
  const {
    sellConditions,
    updateSellCondition,
    addSellCondition,
    removeSellCondition,
    getConditionExpression,
  } = useConditionStore();

  // 목표가/손절가 입력값 (내부 상태)
  const [targetGain, setTargetGainValue] = useState<number>(
    target_and_loss?.target_gain ?? 10,
  );
  const [stopLoss, setStopLossValue] = useState<number>(
    target_and_loss?.stop_loss ?? 10,
  );

  // 보유 기간 입력값 (내부 상태)
  const [minHoldDays, setMinHoldDays] = useState<number>(
    hold_days?.min_hold_days ?? 0,
  );
  const [maxHoldDays, setMaxHoldDays] = useState<number>(
    hold_days?.max_hold_days ?? 0,
  );
  const [holdSellCostBasisSelect, setHoldSellCostBasisSelect] =
    useState<string>("{전일 종가}");
  const [holdSellCostBasisValue, setHoldSellCostBasisValue] =
    useState<number>(0);

  // 조건 매도 - 논리 조건식 및 가격 기준 (내부 상태)
  const [sellLogic, setSellLogicValue] = useState<string>(
    condition_sell?.sell_logic ?? "",
  );
  const [condSellCostBasisSelect, setCondSellCostBasisSelect] =
    useState<string>("{전일 종가}");
  const [condSellCostBasisValue, setCondSellCostBasisValue] =
    useState<number>(0);

  // 모달 상태 관리
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null,
  );

  /**
   * 목표가/손절가 토글 및 값 변경 시 전역 스토어 업데이트
   * 전체 토글이 OFF면 null, ON이면 개별 토글 상태에 따라 값 설정
   */
  useEffect(() => {
    if (toggles.targetAndLoss) {
      setTargetAndLoss({
        target_gain: toggles.profitTarget ? targetGain : null,
        stop_loss: toggles.stopLoss ? stopLoss : null,
      });
    } else {
      setTargetAndLoss(null);
    }
  }, [
    toggles.targetAndLoss,
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
      const sellBasis = `${holdSellCostBasisSelect} ${holdSellCostBasisValue}`;
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
    holdSellCostBasisSelect,
    holdSellCostBasisValue,
    setHoldDays,
  ]);

  /**
   * 조건 매도 토글이 ON될 때 초기 조건 하나 자동 추가
   */
  useEffect(() => {
    if (toggles.conditionalSell && sellConditions.length === 0) {
      addSellCondition();
    }
  }, [toggles.conditionalSell]); // sellConditions를 의존성에 포함하지 않음 (무한 루프 방지)

  /**
   * 조건 매도 토글 및 값 변경 시 전역 스토어 업데이트
   * sellConditions가 변경될 때마다 condition_sell 업데이트
   */
  useEffect(() => {
    if (toggles.conditionalSell) {
      const sellBasis = `${condSellCostBasisSelect} ${condSellCostBasisValue}`;

      // Condition[] 타입을 BacktestRunRequest의 condition_sell 형식으로 변환
      const formattedConditions = sellConditions
        .filter((c) => c.factorName !== null) // 팩터가 선택된 조건만
        .map((c) => ({
          name: c.id, // 조건 이름 (A, B, C, ...)
          expression: `{${c.factorName}} ${c.operator} ${c.value}`, // 조건식 (예: "{PER} > 10")
        }));

      setConditionSell({
        sell_conditions: formattedConditions,
        sell_logic: sellLogic,
        sell_cost_basis: sellBasis,
      });
    } else {
      setConditionSell(null);
    }
  }, [
    toggles.conditionalSell,
    sellConditions,
    sellLogic,
    condSellCostBasisSelect,
    condSellCostBasisValue,
    setConditionSell,
  ]);

  /**
   * 팩터 선택 모달 열기
   * @param id 조건 ID (A, B, C, ...)
   */
  const openModal = (id: string) => {
    setCurrentConditionId(id);
    setIsModalOpen(true);
  };

  /**
   * 팩터 선택 완료 핸들러
   * 선택된 팩터와 함수를 조건에 반영
   */
  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
  ) => {
    if (currentConditionId) {
      updateSellCondition(currentConditionId, {
        factorId,
        factorName,
        subFactorId,
      });
    }
    setIsModalOpen(false);
    setCurrentConditionId(null);
  };

  /**
   * 현재 조건의 초기값을 가져오기 (편집 모드)
   */
  const getCurrentCondition = () => {
    if (!currentConditionId) return undefined;

    const condition = sellConditions.find((c) => c.id === currentConditionId);
    if (!condition || !condition.factorId) return undefined;

    return {
      factorId: condition.factorId,
      subFactorId: condition.subFactorId,
    };
  };

  /**
   * 조건의 부등호 변경 핸들러
   */
  const handleOperatorChange = (
    id: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!=",
  ) => {
    updateSellCondition(id, { operator });
  };

  /**
   * 조건의 값 변경 핸들러
   */
  const handleValueChange = (id: string, value: number) => {
    updateSellCondition(id, { value });
  };

  return (
    <div className="space-y-6">
      {/* 목표가/손절가 */}
      <Panel className="p-6 space-y-4">
        {/* 전체 토글 - 필드명 왼쪽, 토글 오른쪽 */}
        <div className="flex items-center justify-between">
          <Title size="lg" marginBottom="mb-0">
            목표가/손절가
          </Title>
          <button
            onClick={() => {
              toggleState("targetAndLoss");
              if (!toggles.targetAndLoss) {
                // 토글 켜질 때 기본값 설정
                setTargetGainValue(10);
                setStopLossValue(10);
              }
            }}
            className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.targetAndLoss ? "bg-[#d68c45]" : "bg-[#a0a0a0]"
              }`}
          >
            <div
              className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.targetAndLoss ? "left-[15px]" : "left-[2px]"
                }`}
            />
          </button>
        </div>

        {/* 토글 ON시 펼쳐지는 컨텐츠 - 부드러운 애니메이션 */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${toggles.targetAndLoss ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
            }`}
        >
          {/* 목표가와 손절가 가로 배치 */}
          <div className="grid grid-cols-2 gap-4 pt-2">
            {/* 목표가 - 한 줄에 배치 */}
            <div className="flex flex-col">
              <div className="flex items-center gap-[8px] mb-[15px]">
                <Title size="sm" marginBottom="mb-0">
                  목표가
                </Title>
                <button
                  onClick={() => {
                    toggleState("profitTarget");
                    if (toggles.profitTarget) {
                      setTargetGainValue(0);
                    } else {
                      setTargetGainValue(10);
                    }
                  }}
                  disabled={!toggles.targetAndLoss}
                  className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.profitTarget ? "bg-[#d68c45]" : "bg-[#a0a0a0]"
                    } disabled:opacity-50`}
                >
                  <div
                    className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.profitTarget ? "left-[15px]" : "left-[2px]"
                      }`}
                  />
                </button>
              </div>
              <div className="flex items-center gap-[8px]">
                <span className="text-white text-[14px] font-['Pretendard',sans-serif] tracking-[-0.42px] whitespace-nowrap">
                  매수가 대비
                </span>
                <UnderlineInput
                  type="number"
                  value={targetGain}
                  onChange={(e) => setTargetGainValue(Number(e.target.value))}
                  disabled={!toggles.targetAndLoss || !toggles.profitTarget}
                  suffix="%"
                  className="disabled:opacity-50 w-[120px]"
                />
                <span className="text-white text-[14px] font-['Pretendard',sans-serif] tracking-[-0.42px] whitespace-nowrap">
                  상승 시 매도 주문
                </span>
              </div>
            </div>

            {/* 손절가 - 한 줄에 배치 */}
            <div className="flex flex-col">
              <div className="flex items-center gap-[8px] mb-[15px]">
                <Title size="sm" marginBottom="mb-0">
                  손절가
                </Title>
                <button
                  onClick={() => {
                    toggleState("stopLoss");
                    if (toggles.stopLoss) {
                      setStopLossValue(0);
                    } else {
                      setStopLossValue(10);
                    }
                  }}
                  disabled={!toggles.targetAndLoss}
                  className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.stopLoss ? "bg-[#d68c45]" : "bg-[#a0a0a0]"
                    } disabled:opacity-50`}
                >
                  <div
                    className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.stopLoss ? "left-[15px]" : "left-[2px]"
                      }`}
                  />
                </button>
              </div>
              <div className="flex items-center gap-[8px]">
                <span className="text-white text-[14px] font-['Pretendard',sans-serif] tracking-[-0.42px] whitespace-nowrap">
                  매수가 대비
                </span>
                <UnderlineInput
                  type="number"
                  value={stopLoss}
                  onChange={(e) => setStopLossValue(Number(e.target.value))}
                  disabled={!toggles.targetAndLoss || !toggles.stopLoss}
                  suffix="%"
                  className="disabled:opacity-50 w-[120px]"
                />
                <span className="text-white text-[14px] font-['Pretendard',sans-serif] tracking-[-0.42px] whitespace-nowrap">
                  하락 시 매도 주문
                </span>
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* 보유 기간 */}
      <Panel className="p-6 space-y-4">
        {/* 전체 토글 - 필드명 왼쪽, 토글 오른쪽 */}
        <div className="flex items-center justify-between">
          <Title size="lg" marginBottom="mb-0">
            <span>{`보유 `}</span>
            <span className="text-[#7878FF]">기간</span>
          </Title>
          <button
            onClick={() => {
              toggleState("holdingPeriod");
              if (!toggles.holdingPeriod) {
                setMinHoldDays(0);
                setMaxHoldDays(0);
              }
            }}
            className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.holdingPeriod ? "bg-[#d68c45]" : "bg-[#a0a0a0]"
              }`}
          >
            <div
              className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.holdingPeriod ? "left-[15px]" : "left-[2px]"
                }`}
            />
          </button>
        </div>

        {/* 토글 ON시 펼쳐지는 컨텐츠 - 부드러운 애니메이션 */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${toggles.holdingPeriod ? "max-h-[200px] opacity-100" : "max-h-0 opacity-0"
            }`}
        >
          {/* 한 줄에 3가지 항목 모두 배치 - justify-between */}
          <div className="flex items-center justify-between pt-2">
            {/* 최소 종목 보유일 */}
            <div className="flex items-center gap-[8px]">
              <Title size="sm" marginBottom="mb-0">
                최소 종목 보유일
              </Title>
              <UnderlineInput
                type="number"
                value={minHoldDays}
                onChange={(e) => setMinHoldDays(Number(e.target.value))}
                disabled={!toggles.holdingPeriod}
                suffix="일"
                className="disabled:opacity-50 w-[100px]"
              />
            </div>

            {/* 최대 종목 보유일 */}
            <div className="flex items-center gap-[8px]">
              <Title size="sm" marginBottom="mb-0">
                최대 종목 보유일
              </Title>
              <UnderlineInput
                type="number"
                value={maxHoldDays}
                onChange={(e) => setMaxHoldDays(Number(e.target.value))}
                disabled={!toggles.holdingPeriod}
                suffix="일"
                className="disabled:opacity-50 w-[100px]"
              />
            </div>

            {/* 매도 가격 기준 */}
            <div className="flex items-center gap-[8px]">
              <Title size="sm" marginBottom="mb-0">
                매도 가격 기준
              </Title>
              <div className="relative h-[40px] border-b border-[#a0a0a0] w-[150px]">
                <select
                  value={holdSellCostBasisSelect}
                  onChange={(e) => setHoldSellCostBasisSelect(e.target.value)}
                  disabled={!toggles.holdingPeriod}
                  className="absolute left-0 top-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] text-[#a0a0a0] tracking-[-0.6px] w-full appearance-none cursor-pointer disabled:opacity-50"
                >
                  <option value="{전일 종가}">전일 종가</option>
                  <option value="{당일 시가}">당일 시가</option>
                </select>
                <div className="absolute right-0 top-1/2 -translate-y-1/2 size-[32px] pointer-events-none">
                  <svg
                    className="block size-full"
                    fill="none"
                    preserveAspectRatio="none"
                    viewBox="0 0 32 32"
                  >
                    <path d={SVG_PATH.p2a094a00} fill="#A0A0A0" />
                  </svg>
                </div>
              </div>
              <UnderlineInput
                type="number"
                value={holdSellCostBasisValue}
                onChange={(e) =>
                  setHoldSellCostBasisValue(Number(e.target.value))
                }
                disabled={!toggles.holdingPeriod}
                suffix="%"
                className="disabled:opacity-50 w-[100px]"
              />
            </div>
          </div>
        </div>
      </Panel>

      {/* 조건 매도 */}
      <Panel className="p-6 space-y-4">
        {/* 전체 토글 - 필드명 왼쪽, 토글 오른쪽 */}
        <div className="flex items-center justify-between">
          <Title size="lg" marginBottom="mb-0">
            <span>{`조건 `}</span>
            <span className="text-[#7878FF]">매도</span>
          </Title>
          <button
            onClick={() => toggleState("conditionalSell")}
            className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.conditionalSell ? "bg-[#d68c45]" : "bg-[#a0a0a0]"
              }`}
          >
            <div
              className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.conditionalSell ? "left-[15px]" : "left-[2px]"
                }`}
            />
          </button>
        </div>

        {/* 토글 ON시 펼쳐지는 컨텐츠 - 부드러운 애니메이션 */}
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${toggles.conditionalSell ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
            }`}
        >
          <div className="space-y-2 pt-2">
            <Title size="md">매도 조건식 설정</Title>

            {/* 매도 조건 목록 */}
            <div className="space-y-[8px] mb-[20px]">
              {sellConditions.map((condition) => (
                <div key={condition.id} className="flex items-center gap-[8px]">
                  {/* 조건식 표시 영역 */}
                  <div className="h-[60px] rounded-[12px] border border-neutral-500 flex-1">
                    <div className="h-[60px] overflow-clip relative rounded-[inherit] w-full px-[23.5px] flex items-center gap-[16px]">
                      {/* 조건 ID (A, B, C, ...) */}
                      <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-center text-nowrap text-white tracking-[-0.6px]">
                        <p className="leading-[normal] whitespace-pre">
                          {condition.id}
                        </p>
                      </div>

                      <GradientDivider
                        direction="vertical"
                        gradientId={`paint0_linear_sell_cond_${condition.id}`}
                        className="h-[32px] w-[4px]"
                      />

                      {/* 조건식 미리보기 */}
                      <div className="flex-1">
                        <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[#a0a0a0] text-[20px] text-nowrap tracking-[-0.6px]">
                          <p className="leading-[normal] whitespace-pre">
                            {getConditionExpression(condition)}
                          </p>
                        </div>
                      </div>

                      {/* 팩터 선택 버튼 */}
                      <button
                        onClick={() => openModal(condition.id)}
                        disabled={!toggles.conditionalSell}
                        className="rounded-[8px] border border-solid border-white px-[24px] py-[8px] disabled:opacity-50"
                      >
                        <div className="flex flex-col font-bold justify-center leading-[0] not-italic text-xl text-center text-nowrap text-white tracking-[-0.6px]">
                          <p className="leading-[normal] whitespace-pre">
                            팩터 선택
                          </p>
                        </div>
                      </button>

                      {/* 삭제 버튼 */}
                      <button
                        onClick={() => removeSellCondition(condition.id)}
                        disabled={!toggles.conditionalSell}
                        className="rounded-[8px] size-[40px] border border-[#ff6464] border-solid flex items-center justify-center disabled:opacity-50"
                      >
                        <svg
                          className="block size-[24px]"
                          fill="none"
                          preserveAspectRatio="none"
                          viewBox="0 0 24 24"
                        >
                          <path d={SVG_PATH.pa683700} fill="#FF6464" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  {/* 부등호 선택 */}
                  <CustomSelect
                    value={condition.operator}
                    onChange={(e) =>
                      handleOperatorChange(
                        condition.id,
                        e.target.value as
                        | ">="
                        | "<="
                        | ">"
                        | "<"
                        | "="
                        | "!=",
                      )
                    }
                    width="w-[92px]"
                    disabled={!toggles.conditionalSell}
                    className="disabled:opacity-50"
                  >
                    <option value=">=">≥</option>
                    <option value="<=">≤</option>
                    <option value=">">{">"}</option>
                    <option value="<">{"<"}</option>
                    <option value="=">=</option>
                    <option value="!=">≠</option>
                  </CustomSelect>
                  {/* 값 입력 */}
                  <div className="relative h-[60px] w-[92px] border-b border-[#a0a0a0]">
                    <input
                      type="number"
                      value={condition.value}
                      onChange={(e) =>
                        handleValueChange(condition.id, Number(e.target.value))
                      }
                      disabled={!toggles.conditionalSell}
                      className="absolute left-[55%] top-1/2 -translate-x-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[#a0a0a0] text-[20px] tracking-[-0.6px] w-full text-center disabled:opacity-50"
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* 조건식 추가 버튼 */}
            <div className="flex justify-center mb-[60px]">
              <button
                onClick={addSellCondition}
                disabled={!toggles.conditionalSell}
                className="backdrop-blur-[50px] backdrop-filter bg-[rgba(255,255,255,0.2)] rounded-[8px] border border-solid border-white shadow-[0px_0px_8px_2px_rgba(255,255,255,0.3)] px-[24px] py-[8px] disabled:opacity-50"
              >
                <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-center text-nowrap text-white tracking-[-0.6px]">
                  <p className="leading-[normal] whitespace-pre">조건식 추가</p>
                </div>
              </button>
            </div>
          </div>

          <GradientDivider gradientId="paint0_linear_divider_sell" />

          {/* 한 줄에 논리 조건식과 매도 가격 기준 배치 - justify-between */}
          <div className="flex items-center justify-between">
            {/* 논리 조건식 작성 */}
            <div className="flex items-center gap-[8px]">
              <Title size="md" marginBottom="mb-0">
                논리 조건식 작성
              </Title>
              <UnderlineInput
                type="text"
                placeholder="A and B"
                value={sellLogic}
                onChange={(e) => setSellLogicValue(e.target.value)}
                disabled={!toggles.conditionalSell}
                className="disabled:opacity-50 w-[250px]"
              />
            </div>

            {/* 매도 가격 기준 */}
            <div className="flex items-center gap-[8px]">
              <Title size="md" marginBottom="mb-0">
                매도 가격 기준
              </Title>
              <div className="relative h-[40px] border-b border-[#a0a0a0] w-[150px]">
                <select
                  value={condSellCostBasisSelect}
                  onChange={(e) => setCondSellCostBasisSelect(e.target.value)}
                  disabled={!toggles.conditionalSell}
                  className="absolute left-0 top-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] text-[#a0a0a0] tracking-[-0.6px] w-full appearance-none cursor-pointer disabled:opacity-50"
                >
                  <option value="{전일 종가}">전일 종가</option>
                  <option value="{당일 시가}">당일 시가</option>
                </select>
                <div className="absolute right-0 top-1/2 -translate-y-1/2 size-[32px] pointer-events-none">
                  <svg
                    className="block size-full"
                    fill="none"
                    preserveAspectRatio="none"
                    viewBox="0 0 32 32"
                  >
                    <path d={SVG_PATH.p2a094a00} fill="#A0A0A0" />
                  </svg>
                </div>
              </div>
              <UnderlineInput
                type="number"
                value={condSellCostBasisValue}
                onChange={(e) =>
                  setCondSellCostBasisValue(Number(e.target.value))
                }
                disabled={!toggles.conditionalSell}
                suffix="%"
                className="disabled:opacity-50 w-[100px]"
              />
            </div>
          </div>
        </div>
      </Panel>

      {/* Factor Selection Modal */}
      <FactorSelectionModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setCurrentConditionId(null);
        }}
        onSelect={handleFactorSelect}
        initialValues={getCurrentCondition()}
      />
    </div>
  );
}
