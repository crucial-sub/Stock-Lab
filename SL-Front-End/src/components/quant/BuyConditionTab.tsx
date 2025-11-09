"use client";

import {
  CustomSelect,
  DatePickerField,
  GradientDivider,
  Panel,
  RadioButton,
  Title,
  UnderlineInput,
} from "@/components/common";
import { SVG_PATH } from "@/constants";
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
   * 선택된 팩터와 함수를 조건에 반영
   */
  const handleFactorSelect = (
    factorId: string,
    factorName: string,
    subFactorId: string,
  ) => {
    if (currentConditionId) {
      updateBuyCondition(currentConditionId, {
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

    const condition = buyConditions.find((c) => c.id === currentConditionId);
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
    updateBuyCondition(id, { operator });
  };

  /**
   * 조건의 값 변경 핸들러
   */
  const handleValueChange = (id: string, value: number) => {
    updateBuyCondition(id, { value });
  };

  return (
    <div className="space-y-6">
      {/* 기본 설정 (Basic Settings) */}
      <Panel className="p-6 space-y-4">
        <Title size="lg">기본 설정</Title>

        {/* 백테스트 데이터 기준 */}
        <div className="space-y-2">
          <Title size="md">백테스트 데이터 기준</Title>
          <div className="flex items-center gap-6">
            <RadioButton
              name="dataType"
              checked={is_day_or_month === "daily"}
              onChange={() => setIsDayOrMonth("daily")}
              label="일봉"
            />
            <RadioButton
              name="dataType"
              checked={is_day_or_month === "monthly"}
              onChange={() => setIsDayOrMonth("monthly")}
              label="월봉"
            />
          </div>
        </div>

        <GradientDivider gradientId="paint0_linear_divider2" />

        {/* Investment Fields */}
        <div className="grid grid-cols-4 gap-4">
          <div>
            <Title size="sm">투자 금액</Title>
            <UnderlineInput
              type="text"
              value={initial_investment}
              onChange={(e) => setInitialInvestment(Number(e.target.value))}
              inputWidth="w-[80px]"
              suffix="만원"
              borderColor="white"
              textColor="white"
            />
          </div>
          <div>
            <Title size="sm">투자 시작일</Title>
            <DatePickerField
              value={start_date}
              onChange={setStartDate}
              placeholder="투자 시작일 선택"
              className="w-full"
            />
          </div>

          <div>
            <Title size="sm">투자 종료일</Title>
            <DatePickerField
              value={end_date}
              onChange={setEndDate}
              placeholder="투자 종료일 선택"
              className="w-full"
              minDate={start_date ? new Date(parseInt(start_date.slice(0, 4)), parseInt(start_date.slice(4, 6)) - 1, parseInt(start_date.slice(6, 8))) : undefined}
            />
          </div>

          <div>
            <Title size="sm">수수료율</Title>
            <UnderlineInput
              type="number"
              value={commission_rate}
              onChange={(e) => setCommissionRate(Number(e.target.value))}
              step={0.1}
              suffix="%"
            />
          </div>
        </div>
      </Panel>

      {/* 매수 조건 설정 */}
      <Panel className="p-6 space-y-4">
        <Title size="lg">
          <span className="text-brand-primary">매수</span>
          <span>{` 조건 설정`}</span>
        </Title>

        <div className="space-y-2">
          <Title size="md">매수 조건식 설정</Title>

          {/* 매수 조건 목록 */}
          <div className="space-y-[8px] mb-[20px]">
            {buyConditions.map((condition) => (
              <div key={condition.id} className="flex items-center gap-[8px]">
                {/* 조건식 표시 영역 */}
                <div className="h-[60px] rounded-[12px] border border-neutral-500 flex-1">
                  <div className="h-[60px] overflow-clip relative rounded-[inherit] w-full px-[23.5px] flex items-center gap-[16px]">
                    {/* 조건 ID (A, B, C, ...) */}
                    <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-center text-nowrap text-white tracking-[-0.6px]">
                      <p className="leading-[normal] whitespace-pre">{condition.id}</p>
                    </div>

                    <GradientDivider direction="vertical" gradientId="paint0_linear_cond" className="h-[32px] w-[4px]" />

                    {/* 조건식 미리보기 */}
                    <div className="flex-1">
                      <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-text-muted text-[20px] text-nowrap tracking-[-0.6px]">
                        <p className="leading-[normal] whitespace-pre">{getConditionExpression(condition)}</p>
                      </div>
                    </div>

                    {/* 팩터 선택 버튼 */}
                    <button onClick={() => openModal(condition.id)}
                      className="rounded-[8px] border border-solid border-white px-[24px] py-[8px]">
                      <div className="flex flex-col font-bold justify-center leading-[0] not-italic text-xl text-center text-nowrap text-white tracking-[-0.6px]">
                        <p className="leading-[normal] whitespace-pre">팩터 선택</p>
                      </div>
                    </button>

                    {/* 삭제 버튼 */}
                    <button
                      onClick={() => removeBuyCondition(condition.id)}
                      className="rounded-[8px] size-[40px] border border-brand-primary border-solid flex items-center justify-center"
                    >
                      <svg className="block size-[24px]" fill="none" preserveAspectRatio="none" viewBox="0 0 24 24">
                        <path d={SVG_PATH.pa683700} fill="var(--color-brand-primary)" />
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
                >
                  <option value=">=">≥</option>
                  <option value="<=">≤</option>
                  <option value=">">{">"}</option>
                  <option value="<">{"<"}</option>
                  <option value="=">=</option>
                  <option value="!=">≠</option>
                </CustomSelect>
                {/* 값 입력 */}
                <div className="relative h-[60px] w-[92px] border-b border-text-muted">
                  <input
                    type="number"
                    value={condition.value}
                    onChange={(e) =>
                      handleValueChange(condition.id, Number(e.target.value))
                    }
                    className="absolute left-[55%] top-1/2 -translate-x-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-text-muted text-[20px] tracking-[-0.6px] w-full text-center"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* 조건식 추가 버튼 */}
          <div className="flex justify-center mb-[60px]">
            <button
              onClick={addBuyCondition}
              className="backdrop-blur-[50px] backdrop-filter bg-[rgba(255,255,255,0.2)] rounded-[8px] border border-solid border-white shadow-[0px_0px_8px_2px_rgba(255,255,255,0.3)] px-[24px] py-[8px]"
            >
              <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-center text-nowrap text-white tracking-[-0.6px]">
                <p className="leading-[normal] whitespace-pre">조건식 추가</p>
              </div>
            </button>
          </div>
        </div>

        <GradientDivider gradientId="paint0_linear_divider3" />

        {/* Bottom Fields */}
        <div className="grid grid-cols-2 gap-11">
          <div>
            <Title size="md" className="w-[125px]">논리 조건식 작성</Title>
            <UnderlineInput
              type="text"
              placeholder="A and B"
              value={buy_logic}
              onChange={(e) => setBuyLogic(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Title size="md" className="w-[179px]">매수 종목 선택 우선순위</Title>
            <div className="flex h-[40px] border-b border-text-muted">
              <input
                type="text"
                value={priority_factor}
                onChange={(e) => setPriorityFactor(e.target.value)}
                placeholder="예: {PBR}"
                className="bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] text-text-muted tracking-[-0.6px] w-full"
              />
              <select
                value={priority_order}
                onChange={(e) => setPriorityOrder(e.target.value)}
                className="bg-transparent px-3 w-32"
              >
                <option value="desc">내림차순</option>
                <option value="asc">오름차순</option>
              </select>
            </div>
          </div>
        </div>
      </Panel>

      {/* 매수 비중 설정 */}
      <Panel className="relative p-6 space-y-4">
        <Title size="lg">
          <span className="text-brand-primary">매수</span>
          <span>{` 비중 설정`}</span>
        </Title>
        <div className="grid grid-cols-4 gap-8">
          <div>
            <Title size="sm">종목당 매수 비중</Title>
            <UnderlineInput
              type="number"
              value={per_stock_ratio}
              onChange={(e) => setPerStockRatio(Number(e.target.value))}
              step={1}
              suffix="%"
            />
          </div>

          <div>
            <Title size="sm">최대 보유 종목 수</Title>
            <UnderlineInput
              type="number"
              value={max_holdings}
              onChange={(e) => setMaxHoldings(Number(e.target.value))}
              step={1}
              inputWidth="w-[80%]"
              suffix="종목"
            />
          </div>

          <div>
            <div className="flex items-center gap-[8px] mb-[15px]">
              <Title size="sm" marginBottom="mb-0">종목당 최대 매수 금액</Title>
              <button
                onClick={() => {
                  toggleState("maxPerDay");
                  // 토글이 꺼지면 null로 설정
                  if (toggles.maxPerDay) {
                    setMaxBuyValue(null);
                  } else {
                    setMaxBuyValue(0);
                  }
                }}
                className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.maxPerDay ? 'bg-[#d68c45]' : 'bg-text-muted'
                  }`}
              >
                <div className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.maxPerDay ? 'left-[15px]' : 'left-[2px]'
                  }`} />
              </button>
            </div>
            <UnderlineInput
              type="text"
              value={max_buy_value ?? 0}
              onChange={(e) => setMaxBuyValue(Number(e.target.value))}
              disabled={!toggles.maxPerDay}
              suffix="만원"
              className="disabled:opacity-50"
            />
          </div>

          <div>
            <div className="flex items-center gap-[8px] mb-[15px]">
              <Title size="sm" marginBottom="mb-0">1일 최대 매수 종목 수</Title>
              <button
                onClick={() => {
                  toggleState("maxPerStock");
                  // 토글이 꺼지면 null로 설정
                  if (toggles.maxPerStock) {
                    setMaxDailyStock(null);
                  } else {
                    setMaxDailyStock(0);
                  }
                }} className={`h-[21px] w-[34px] rounded-[100px] relative transition-colors ${toggles.maxPerStock ? 'bg-[#d68c45]' : 'bg-text-muted'
                  }`}
              >
                <div className={`absolute rounded-[100px] size-[17px] top-1/2 -translate-y-1/2 bg-white transition-all ${toggles.maxPerStock ? 'left-[15px]' : 'left-[2px]'
                  }`} />
              </button>
            </div>
            <UnderlineInput
              type="text"
              value={max_daily_stock ?? 0}
              onChange={(e) => setMaxDailyStock(Number(e.target.value))}
              disabled={!toggles.maxPerStock}
              suffix="종목"
              className="disabled:opacity-50"
            />
          </div>
        </div>
      </Panel>

      {/* 매수 방법 선택 */}
      <Panel className="p-6 space-y-4">
        <Title size="lg">
          <span className="text-brand-primary">매수</span>
          <span>{` 방법 선택`}</span>
        </Title>

        <div className="grid grid-cols-2 gap-[28px]">
          <div>
            <Title size="sm">매수 가격 기준</Title>
            <div className="relative h-[40px] border-b border-text-muted">
              <select
                value={buyCostBasisSelect}
                onChange={(e) => setBuyCostBasisSelect(e.target.value)}
                className="absolute left-0 top-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] text-text-muted tracking-[-0.6px] w-full appearance-none cursor-pointer"
              >
                <option value="{전일 종가}">전일 종가</option>
                <option value="{당일 시가}">당일 시가</option>
              </select>
              <div className="absolute right-0 top-1/2 -translate-y-1/2 size-[32px] pointer-events-none">
                <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 32 32">
                  <path d={SVG_PATH.p2a094a00} fill="var(--color-text-muted)" />
                </svg>
              </div>
            </div>
          </div>

          <div>
            <div className="relative h-full border-b border-text-muted">
              <input
                type="number"
                value={buyCostBasisValue}
                onChange={(e) => setBuyCostBasisValue(Number(e.target.value))}
                className="absolute left-0 bottom-1 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] text-text-muted tracking-[-0.6px] w-[95%]"
              />
              <div className="absolute right-1 bottom-2 flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-nowrap text-text-muted tracking-[-0.6px]">
                <p className="leading-[normal] whitespace-pre">%</p>
              </div>
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
