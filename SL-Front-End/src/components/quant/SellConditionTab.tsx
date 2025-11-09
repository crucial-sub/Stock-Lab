"use client";

import { useBacktestConfigStore, useConditionStore } from "@/stores";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import Image from "next/image";
import { useEffect, useState } from "react";
import { FactorSelectionModal } from "./FactorSelectionModal";

/**
 * 매도 조건 설정 탭 - 새 디자인
 *
 * ThreeColumnLayout을 사용한 완전히 새로운 구현:
 * - 왼쪽: 네비게이션 사이드바
 * - 중앙: 매도 조건 설정 폼
 * - 오른쪽: 설정 요약 패널
 */
export default function SellConditionTab() {
  // Server data
  const { data: subFactors = [] } = useSubFactorsQuery();

  // Zustand stores
  const {
    target_and_loss,
    setTargetAndLoss,
    hold_days,
    setHoldDays,
    condition_sell,
    setConditionSell,
  } = useBacktestConfigStore();

  const {
    sellConditions,
    updateSellCondition,
    addSellCondition,
    removeSellCondition,
    getConditionExpression,
  } = useConditionStore();

  // 사이드바 상태
  const [activeSection, setActiveSection] = useState("목표가 / 손절가");
  const sidebarItems = [
    "매수 조건",
    "매도 조건",
    "  목표가 / 손절가",
    "  보유 기간",
    "  조건 매도",
    "매매 대상 설정",
  ];

  // 섹션 토글 상태
  const [targetLossOpen, setTargetLossOpen] = useState(false);
  const [holdPeriodOpen, setHoldPeriodOpen] = useState(false);
  const [conditionalSellOpen, setConditionalSellOpen] = useState(false);

  // 목표가/손절가 개별 토글
  const [profitTargetEnabled, setProfitTargetEnabled] = useState(false);
  const [stopLossEnabled, setStopLossEnabled] = useState(false);

  // 목표가/손절가 값
  const [targetGain, setTargetGain] = useState<number>(10);
  const [stopLoss, setStopLoss] = useState<number>(10);

  // 보유 기간 값
  const [minHoldDays, setMinHoldDays] = useState<number>(10);
  const [maxHoldDays, setMaxHoldDays] = useState<number>(10);
  const [holdSellCostBasisSelect, setHoldSellCostBasisSelect] =
    useState<string>("전일 종가");
  const [holdSellCostBasisValue, setHoldSellCostBasisValue] =
    useState<number>(10);

  // 조건 매도 값
  const [sellLogic, setSellLogic] = useState<string>("A and B");
  const [condSellCostBasisSelect, setCondSellCostBasisSelect] =
    useState<string>("전일 종가");
  const [condSellCostBasisValue, setCondSellCostBasisValue] =
    useState<number>(10);

  // 모달 상태
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null
  );

  // 목표가/손절가 전역 스토어 업데이트
  useEffect(() => {
    if (targetLossOpen) {
      setTargetAndLoss({
        target_gain: profitTargetEnabled ? targetGain : null,
        stop_loss: stopLossEnabled ? stopLoss : null,
      });
    } else {
      setTargetAndLoss(null);
    }
  }, [
    targetLossOpen,
    profitTargetEnabled,
    stopLossEnabled,
    targetGain,
    stopLoss,
    setTargetAndLoss,
  ]);

  // 보유 기간 전역 스토어 업데이트
  useEffect(() => {
    if (holdPeriodOpen) {
      setHoldDays({
        min_hold_days: minHoldDays,
        max_hold_days: maxHoldDays,
        sell_price_basis: holdSellCostBasisSelect,
        sell_price_offset: holdSellCostBasisValue,
      });
    } else {
      setHoldDays(null);
    }
  }, [
    holdPeriodOpen,
    minHoldDays,
    maxHoldDays,
    holdSellCostBasisSelect,
    holdSellCostBasisValue,
    setHoldDays,
  ]);

  // 조건 매도 토글 시 초기 조건 추가
  useEffect(() => {
    if (conditionalSellOpen && sellConditions.length === 0) {
      addSellCondition();
      addSellCondition();
    }
  }, [conditionalSellOpen]);

  // 조건 매도 전역 스토어 업데이트
  useEffect(() => {
    if (conditionalSellOpen) {
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
        sell_price_basis: condSellCostBasisSelect,
        sell_price_offset: condSellCostBasisValue,
      });
    } else {
      setConditionSell(null);
    }
  }, [
    conditionalSellOpen,
    sellConditions,
    sellLogic,
    condSellCostBasisSelect,
    condSellCostBasisValue,
    setConditionSell,
  ]);

  // 팩터 선택 모달
  const openModal = (id: string) => {
    setCurrentConditionId(id);
    setIsModalOpen(true);
  };

  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string,
  ) => {
    if (currentConditionId) {
      // subFactorId로 subFactorName 찾기
      const subFactor = subFactors.find(
        (sf) => String(sf.id) === subFactorId
      );
      const subFactorName = subFactor?.display_name;

      updateSellCondition(currentConditionId, {
        factorId,
        factorName,
        subFactorId,
        subFactorName,
        argument,
      });
    }
    setIsModalOpen(false);
    setCurrentConditionId(null);
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

  // 메인 컨텐츠
  const mainContent = (
    <div className="space-y-6">
      {/* 목표가 / 손절가 섹션 */}
      <div id="목표가-/-손절가" className="space-y-3">
        {/* 제목과 설명을 패널 외부로 이동 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-text-strong">
              목표가 / 손절가
            </h3>
            <p className="text-sm text-text-body">
              설사리 감사에 따라 목표 기준에서의 매수가 / 손절가에 도달 시 매도
              주문을 합니다.
            </p>
          </div>
          <button
            onClick={() => setTargetLossOpen(!targetLossOpen)}
            className="relative w-[50px] h-[28px] rounded-full transition-colors"
            style={{
              backgroundColor: targetLossOpen ? "#0066FF" : "#6B7280",
            }}
          >
            <div
              className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${targetLossOpen ? "left-[25px]" : "left-[3px]"
                }`}
            />
          </button>
        </div>

        {/* 패널에 파란색 좌측 border 추가 */}
        {targetLossOpen && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-secondary">
            <div className="grid grid-cols-2 gap-6">
              {/* 목표가 */}
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <h4 className="text-base font-semibold text-text-strong">
                    목표가
                  </h4>
                  <button
                    onClick={() => setProfitTargetEnabled(!profitTargetEnabled)}
                    className="relative w-[50px] h-[28px] rounded-full transition-colors"
                    style={{
                      backgroundColor: profitTargetEnabled ? "#0066FF" : "#6B7280",
                    }}
                  >
                    <div
                      className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${profitTargetEnabled ? "left-[25px]" : "left-[3px]"
                        }`}
                    />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-body">매수가 대비</span>
                  <input
                    type="number"
                    value={targetGain}
                    onChange={(e) => setTargetGain(Number(e.target.value))}
                    disabled={!profitTargetEnabled}
                    className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong disabled:opacity-50"
                  />
                  <span className="text-sm text-text-body">% 상승 시 매도 주문</span>
                </div>
              </div>

              {/* 손절가 */}
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <h4 className="text-base font-semibold text-text-strong">
                    손절가
                  </h4>
                  <button
                    onClick={() => setStopLossEnabled(!stopLossEnabled)}
                    className="relative w-[50px] h-[28px] rounded-full transition-colors"
                    style={{
                      backgroundColor: stopLossEnabled ? "#0066FF" : "#6B7280",
                    }}
                  >
                    <div
                      className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${stopLossEnabled ? "left-[25px]" : "left-[3px]"
                        }`}
                    />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-body">매수가 대비</span>
                  <input
                    type="number"
                    value={stopLoss}
                    onChange={(e) => setStopLoss(Number(e.target.value))}
                    disabled={!stopLossEnabled}
                    className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong disabled:opacity-50"
                  />
                  <span className="text-sm text-text-body">% 하락 시 매도 주문</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 보유 기간 섹션 */}
      <div id="보유-기간" className="space-y-3">
        {/* 제목과 설명을 패널 외부로 이동 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-text-strong">보유 기간</h3>
            <p className="text-sm text-text-body">
              최소 보유일 만큼 시 매수 후 일정 기간 이상 매매 어떤 상황에도
              매도되지 않습니다. 최대 보유일 경과 시 매매 주 후에도 주문을 합니다.
            </p>
          </div>
          <button
            onClick={() => setHoldPeriodOpen(!holdPeriodOpen)}
            className="relative w-[50px] h-[28px] rounded-full transition-colors"
            style={{
              backgroundColor: holdPeriodOpen ? "#0066FF" : "#6B7280",
            }}
          >
            <div
              className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${holdPeriodOpen ? "left-[25px]" : "left-[3px]"
                }`}
            />
          </button>
        </div>

        {/* 패널에 파란색 좌측 border 추가 */}
        {holdPeriodOpen && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-secondary">
            <div className="flex items-center gap-6">
              {/* 최소 종목 보유일 */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-text-strong whitespace-nowrap">
                  최소 종목 보유일
                </span>
                <input
                  type="number"
                  value={minHoldDays}
                  onChange={(e) => setMinHoldDays(Number(e.target.value))}
                  className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong"
                />
                <span className="text-sm text-text-body">일</span>
              </div>

              {/* 최대 종목 보유일 */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-text-strong whitespace-nowrap">
                  최대 종목 보유일
                </span>
                <input
                  type="number"
                  value={maxHoldDays}
                  onChange={(e) => setMaxHoldDays(Number(e.target.value))}
                  className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong"
                />
                <span className="text-sm text-text-body">일</span>
              </div>

              {/* 매도 가격 기준 */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-text-strong whitespace-nowrap">
                  매도 가격 기준
                </span>
                <select
                  value={holdSellCostBasisSelect}
                  onChange={(e) => setHoldSellCostBasisSelect(e.target.value)}
                  className="px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong appearance-none cursor-pointer"
                >
                  <option value="전일 종가">전일 종가</option>
                  <option value="당일 시가">당일 시가</option>
                </select>
                <input
                  type="number"
                  value={holdSellCostBasisValue}
                  onChange={(e) =>
                    setHoldSellCostBasisValue(Number(e.target.value))
                  }
                  className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong"
                />
                <span className="text-sm text-text-body">%</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 조건 매도 섹션 */}
      <div id="조건-매도" className="space-y-3">
        {/* 제목과 설명을 패널 외부로 이동 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-bold text-text-strong">조건 매도</h3>
            <p className="text-sm text-text-body">
              변경된 상영한 조건식을 충족했을 때도 주문을 합니다.
            </p>
          </div>
          <button
            onClick={() => setConditionalSellOpen(!conditionalSellOpen)}
            className="relative w-[50px] h-[28px] rounded-full transition-colors"
            style={{
              backgroundColor: conditionalSellOpen ? "#0066FF" : "#6B7280",
            }}
          >
            <div
              className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${conditionalSellOpen ? "left-[25px]" : "left-[3px]"
                }`}
            />
          </button>
        </div>

        {/* 패널에 파란색 좌측 border 추가 */}
        {conditionalSellOpen && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-secondary">
            <div className="space-y-6">
              {/* 매도 조건식 설정 */}
              <div>
                <h4 className="text-base font-semibold text-text-strong mb-3">
                  매도 조건식 설정
                </h4>
                <div className="space-y-3">
                  {sellConditions.map((condition) => (
                    <div
                      key={condition.id}
                      className="flex items-center gap-3 p-4 bg-bg-app rounded-lg border border-border-default"
                    >
                      {/* 조건 ID */}
                      <div className="flex items-center justify-center w-10 h-10 bg-brand-primary text-white rounded-md font-bold text-lg">
                        {condition.id}
                      </div>

                      <div className="h-8 w-px bg-border-default" />

                      {/* 조건 표현식 */}
                      <div className="flex-1 text-text-body">
                        {condition.factorName
                          ? `조건식이 다음과 같이 들어갑니다.`
                          : "조건식을 추가하려면 클릭하세요."}
                      </div>

                      {/* 팩터 선택 버튼 */}
                      <button
                        onClick={() => openModal(condition.id)}
                        className="px-4 py-2 border border-white rounded-md text-white text-sm font-medium hover:bg-white hover:text-bg-app transition-colors"
                      >
                        팩터 선택
                      </button>

                      {/* 부등호 */}
                      <select
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
                            | "!="
                          )
                        }
                        className="w-20 px-2 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong text-center"
                      >
                        <option value=">=">≥</option>
                        <option value="<=">≤</option>
                        <option value=">">{">"}</option>
                        <option value="<">{"<"}</option>
                        <option value="=">=</option>
                        <option value="!=">≠</option>
                      </select>

                      {/* 값 입력 */}
                      <input
                        type="number"
                        value={condition.value}
                        onChange={(e) =>
                          handleValueChange(condition.id, Number(e.target.value))
                        }
                        className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong text-center"
                      />

                      {/* 삭제 버튼 */}
                      <button
                        onClick={() => removeSellCondition(condition.id)}
                        className="p-2 border border-accent-primary rounded-md hover:bg-accent-primary transition-colors"
                      >
                        <Image
                          src="/icons/trash.svg"
                          alt="삭제"
                          width={20}
                          height={20}
                        />
                      </button>
                    </div>
                  ))}

                  {/* 조건식 추가 버튼 */}
                  <button
                    onClick={addSellCondition}
                    className="w-full py-3 border border-white rounded-md text-white text-sm font-medium hover:bg-white hover:bg-opacity-20 transition-colors"
                  >
                    조건식을 추가하려면 클릭하세요.
                  </button>
                </div>
              </div>

              {/* 논리 조건식 - 별도 행으로 분리 */}
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
                    className="w-64 px-3 py-2 bg-bg-app border-b border-text-muted text-text-strong placeholder:text-text-muted"
                  />
                </div>
              </div>

              {/* 매도 가격 기준 - 별도 행으로 분리 */}
              <div className="flex items-center gap-3">
                <h4 className="text-base font-semibold text-text-strong">
                  매도 가격 기준
                </h4>
                <select
                  value={condSellCostBasisSelect}
                  onChange={(e) =>
                    setCondSellCostBasisSelect(e.target.value)
                  }
                  className="px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong appearance-none cursor-pointer"
                >
                  <option value="전일 종가">전일 종가</option>
                  <option value="당일 시가">당일 시가</option>
                </select>
                <input
                  type="number"
                  value={condSellCostBasisValue}
                  onChange={(e) =>
                    setCondSellCostBasisValue(Number(e.target.value))
                  }
                  className="w-24 px-3 py-2 bg-bg-app border border-border-default rounded-sm text-text-strong"
                />
                <span className="text-sm text-text-body">%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {mainContent}

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
    </>
  );
}