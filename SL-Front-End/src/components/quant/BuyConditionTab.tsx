"use client";

import { Button, Input, Panel, Toggle } from "@/components/common";
import { useBuyCondition } from "@/hooks";
import { useBacktestConfigStore, useConditionStore } from "@/stores";
import { useEffect, useState } from "react";
import { FactorSelectionModal } from "./FactorSelectionModal";

/**
 * 매수 조건 설정 탭 컴포넌트
 *
 * 주요 기능:
 * 1. 백테스트 기본 설정 (데이터 기준, 투자 금액 등)
 * 2. 매수 조건식 설정 (팩터 선택을 통한 조건 생성)
 * 3. 매수 비중 설정
 * 4. 매수 방법 선택
 *
 * 모든 설정값은 useBacktestConfigStore에 저장되며
 * BacktestRunRequest 형식과 완벽하게 일치합니다.
 */
export function BuyConditionTab() {
  // 기존 useBuyCondition 훅은 기본값과 토글 상태 관리용
  const { toggles, toggleState } = useBuyCondition();

  // 전역 백테스트 설정 스토어
  const {
    is_day_or_month,
    setIsDayOrMonth,
    initial_investment,
    setInitialInvestment,
    start_date,
    setStartDate,
    end_date,
    setEndDate,
    commission_rate,
    setCommissionRate,
    buy_logic,
    setBuyLogic,
    priority_factor,
    setPriorityFactor,
    priority_order,
    setPriorityOrder,
    per_stock_ratio,
    setPerStockRatio,
    max_holdings,
    setMaxHoldings,
    max_buy_value,
    setMaxBuyValue,
    max_daily_stock,
    setMaxDailyStock,
    setBuyCostBasis,
    setBuyConditions,
  } = useBacktestConfigStore();

  // Zustand 스토어에서 매수 조건 가져오기
  const {
    buyConditions,
    updateBuyCondition,
    addBuyCondition,
    removeBuyCondition,
    getConditionExpression,
  } = useConditionStore();

  // 모달 상태 관리
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(
    null,
  );

  // 매수 가격 기준 선택값 (내부 상태)
  const [buyCostBasisSelect, setBuyCostBasisSelect] =
    useState<string>("{전일 종가}");
  const [buyCostBasisValue, setBuyCostBasisValue] = useState<number>(0);

  /**
   * buyConditions가 변경될 때마다 전역 스토어에 반영
   * conditionStore → backtestConfigStore 동기화
   */
  useEffect(() => {
    // Condition[] 타입을 BacktestRunRequest의 buy_conditions 형식으로 변환
    const formattedConditions = buyConditions
      .filter((c) => c.factorName !== null) // 팩터가 선택된 조건만
      .map((c) => ({
        name: c.id, // 조건 이름 (A, B, C, ...)
        expression: `{${c.factorName}} ${c.operator} ${c.value}`, // 조건식 (예: "{PER} > 10")
      }));

    setBuyConditions(formattedConditions);
  }, [buyConditions, setBuyConditions]);

  /**
   * 매수 가격 기준 업데이트 (선택값 + 퍼센트 값 결합)
   */
  useEffect(() => {
    const basis = `${buyCostBasisSelect} ${buyCostBasisValue}`;
    setBuyCostBasis(basis);
  }, [buyCostBasisSelect, buyCostBasisValue, setBuyCostBasis]);

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
   * 선택된 팩터, 함수, 부등호, 값을 조건에 반영
   */
  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!=",
    value: number,
  ) => {
    if (currentConditionId) {
      updateBuyCondition(currentConditionId, {
        factorId,
        factorName,
        subFactorId,
        operator,
        value,
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

    const condition = buyConditions.find((c) => c.id === currentConditionId);
    if (!condition || !condition.factorId) return undefined;

    return {
      factorId: condition.factorId,
      subFactorId: condition.subFactorId,
      operator: condition.operator,
      value: condition.value,
    };
  };

  return (
    <div className="space-y-6">
      {/* 기본 설정 (Basic Settings) */}
      <Panel className="p-6 space-y-4">
        <h3 className="text-base font-semibold text-text-primary">기본 설정</h3>

        {/* 백테스트 데이터 기준 */}
        <div className="space-y-2">
          <div className="block text-sm text-text-secondary">
            백테스트 데이터 기준
          </div>
          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="dataType"
                checked={is_day_or_month === "daily"}
                onChange={() => setIsDayOrMonth("daily")}
                className="w-4 h-4 accent-white"
              />
              <span className="text-sm text-text-primary">일봉</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="dataType"
                checked={is_day_or_month === "monthly"}
                onChange={() => setIsDayOrMonth("monthly")}
                className="w-4 h-4 accent-white"
              />
              <span className="text-sm text-text-primary">월봉</span>
            </label>
          </div>
        </div>

        {/* Investment Fields */}
        <div className="grid grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">투자 금액</div>
            <Input
              type="number"
              value={initial_investment}
              onChange={(e) => setInitialInvestment(Number(e.target.value))}
              suffix="만원"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              투자 시작일 (YYYYMMDD)
            </div>
            <Input
              type="text"
              value={start_date}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="20190101"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              투자 종료일 (YYYYMMDD)
            </div>
            <Input
              type="text"
              value={end_date}
              onChange={(e) => setEndDate(e.target.value)}
              placeholder="20241231"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">수수료율</div>
            <Input
              type="number"
              value={commission_rate}
              onChange={(e) => setCommissionRate(Number(e.target.value))}
              step={0.1}
              suffix="%"
              className="w-full"
            />
          </div>
        </div>
      </Panel>

      {/* 매수 조건 설정 */}
      <Panel className="p-6 space-y-4">
        <h3 className="text-base font-semibold text-state-positive">
          매수 조건 설정
        </h3>

        <div className="space-y-2">
          <div className="block text-sm text-text-secondary">
            매수 조건식 설정
          </div>

          {/* 매수 조건 목록 */}
          <div className="space-y-3">
            {buyConditions.map((condition) => (
              <div
                key={condition.id}
                className="flex items-center gap-3 p-4 bg-bg-surface rounded-lg border border-border-default"
              >
                {/* 조건 ID (A, B, C, ...) */}
                <span className="text-sm font-medium text-text-primary w-6">
                  {condition.id}
                </span>

                {/* 조건식 표시 영역 */}
                <span className="flex-1 text-sm text-text-tertiary">
                  {getConditionExpression(condition)}
                </span>

                {/* 팩터 선택 버튼 */}
                <Button
                  variant="ghost"
                  onClick={() => openModal(condition.id)}
                  className="text-sm px-4 py-2"
                >
                  팩터 선택
                </Button>

                {/* 삭제 버튼 */}
                <button
                  type="button"
                  onClick={() => removeBuyCondition(condition.id)}
                  className="w-8 h-8 flex items-center justify-center rounded bg-state-positive/20 text-state-positive hover:bg-state-positive/30"
                >
                  🗑
                </button>
              </div>
            ))}
          </div>

          {/* 조건식 추가 버튼 */}
          <div className="flex justify-center py-2">
            <Button variant="secondary" onClick={addBuyCondition}>
              조건식 추가
            </Button>
          </div>
        </div>

        {/* Bottom Fields */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              논리 조건식 작성
            </div>
            <Input
              type="text"
              value={buy_logic}
              onChange={(e) => setBuyLogic(e.target.value)}
              placeholder="예: A and B"
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              매수 종목 선택 우선순위
            </div>
            <div className="flex gap-2">
              <Input
                type="text"
                value={priority_factor}
                onChange={(e) => setPriorityFactor(e.target.value)}
                placeholder="예: {PBR}"
                className="flex-1"
              />
              <select
                value={priority_order}
                onChange={(e) => setPriorityOrder(e.target.value)}
                className="quant-input px-3"
              >
                <option value="desc">내림차순</option>
                <option value="asc">오름차순</option>
              </select>
            </div>
          </div>
        </div>
      </Panel>

      {/* 매수 비중 설정 */}
      <Panel className="p-6 space-y-4">
        <h3 className="text-base font-semibold text-state-positive">
          매수 비중 설정
        </h3>

        <div className="grid grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              종목당 매수 비중
            </div>
            <Input
              type="number"
              value={per_stock_ratio}
              onChange={(e) => setPerStockRatio(Number(e.target.value))}
              suffix="%"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              최대 보유 종목 수
            </div>
            <Input
              type="number"
              value={max_holdings}
              onChange={(e) => setMaxHoldings(Number(e.target.value))}
              suffix="종목"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <span>종목당 최대 매수 금액</span>
              <Toggle
                enabled={toggles.maxPerStock}
                onChange={() => {
                  toggleState("maxPerStock");
                  // 토글이 꺼지면 null로 설정
                  if (toggles.maxPerStock) {
                    setMaxBuyValue(null);
                  } else {
                    setMaxBuyValue(0);
                  }
                }}
                label="종목당 최대 매수 금액"
              />
            </div>
            <Input
              type="number"
              value={max_buy_value ?? 0}
              onChange={(e) => setMaxBuyValue(Number(e.target.value))}
              disabled={!toggles.maxPerStock}
              suffix="만원"
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              <span>1일 최대 매수 종목 수</span>
              <Toggle
                enabled={toggles.maxPerDay}
                onChange={() => {
                  toggleState("maxPerDay");
                  // 토글이 꺼지면 null로 설정
                  if (toggles.maxPerDay) {
                    setMaxDailyStock(null);
                  } else {
                    setMaxDailyStock(0);
                  }
                }}
                label="1일 최대 매수 종목 수"
              />
            </div>
            <Input
              type="number"
              value={max_daily_stock ?? 0}
              onChange={(e) => setMaxDailyStock(Number(e.target.value))}
              disabled={!toggles.maxPerDay}
              suffix="종목"
              className="w-full"
            />
          </div>
        </div>
      </Panel>

      {/* 매수 방법 선택 */}
      <Panel className="p-6 space-y-4">
        <h3 className="text-base font-semibold text-state-positive">
          매수 방법 선택
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="block text-sm text-text-secondary">
              매수 가격 기준
            </div>
            <select
              value={buyCostBasisSelect}
              onChange={(e) => setBuyCostBasisSelect(e.target.value)}
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
              value={buyCostBasisValue}
              onChange={(e) => setBuyCostBasisValue(Number(e.target.value))}
              suffix="%"
              className="w-full"
            />
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
