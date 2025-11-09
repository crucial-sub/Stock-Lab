"use client";

/**
 * 매수 조건 탭 - Figma 디자인 완전 재구현
 *
 * 레이아웃:
 * - 좌측: 사이드바 네비게이션 (일반 조건 설정, 매수 조건 설정, 매수 비중 설정, 매수 방법 선택)
 * - 중앙: 메인 컨텐츠
 * - 우측: 요약 패널
 */

import { useBacktestConfigStore, useConditionStore } from "@/stores";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import Image from "next/image";
import { useEffect, useState } from "react";
import { FactorSelectionModal } from "./FactorSelectionModal";

export default function BuyConditionTab() {
  const [activeSection, setActiveSection] = useState("일반 조건 설정");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentConditionId, setCurrentConditionId] = useState<string | null>(null);

  // Server data
  const { data: subFactors = [] } = useSubFactorsQuery();

  // Zustand stores
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
    slippage,
    setSlippage,
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
    buy_price_basis,
    buy_price_offset,
    setBuyPriceBasis,
    setBuyPriceOffset,
    setBuyConditions,
  } = useBacktestConfigStore();

  const {
    buyConditions,
    updateBuyCondition,
    addBuyCondition,
    removeBuyCondition,
    getConditionExpression,
  } = useConditionStore();

  // Local state
  const [buyCostBasisSelect, setBuyCostBasisSelect] = useState<string>(buy_price_basis || "전일 종가");
  const [buyCostBasisValue, setBuyCostBasisValue] = useState<number>(buy_price_offset || 0);
  const [enableMaxBuyValue, setEnableMaxBuyValue] = useState(max_buy_value !== null);
  const [enableMaxDailyStock, setEnableMaxDailyStock] = useState(max_daily_stock !== null);

  // Sync buyConditions to global store
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

  // Sync buy price basis and offset
  useEffect(() => {
    setBuyPriceBasis(buyCostBasisSelect);
    setBuyPriceOffset(buyCostBasisValue);
  }, [buyCostBasisSelect, buyCostBasisValue, setBuyPriceBasis, setBuyPriceOffset]);

  // Factor selection handlers
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

      updateBuyCondition(currentConditionId, {
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
    const condition = buyConditions.find((c) => c.id === currentConditionId);
    if (!condition || !condition.factorId) return undefined;
    return {
      factorId: condition.factorId,
      subFactorId: condition.subFactorId,
    };
  };

  const handleOperatorChange = (
    id: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!=",
  ) => {
    updateBuyCondition(id, { operator });
  };

  const handleValueChange = (id: string, value: number) => {
    updateBuyCondition(id, { value });
  };

  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <>
      {/* Main Content */}
      <div className="space-y-6 pb-12">
        {/* 일반 조건 설정 */}
        <div id="일반 조건 설정" className="bg-bg-surface rounded-lg shadow-card p-8">
          <h2 className="text-2xl font-bold text-text-strong mb-6">
            일반 조건 설정
          </h2>

          {/* 백테스트 데이터 기준 */}
          <div className="mb-8">
            <label className="block text-base font-medium text-text-strong mb-3">
              백테스트 데이터 기준
            </label>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="dataType"
                  checked={is_day_or_month === "daily"}
                  onChange={() => setIsDayOrMonth("daily")}
                  className="w-5 h-5 accent-accent-primary"
                />
                <span className="text-text-body">일봉</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="dataType"
                  checked={is_day_or_month === "monthly"}
                  onChange={() => setIsDayOrMonth("monthly")}
                  className="w-5 h-5 accent-accent-primary"
                />
                <span className="text-text-body">월봉</span>
              </label>
            </div>
          </div>

          <div className="h-px bg-border-subtle mb-8" />

          {/* 투자 설정 */}
          <div className="grid grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                투자 금액
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={initial_investment}
                  onChange={(e) => setInitialInvestment(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  만원
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                투자 시작일
              </label>
              <input
                type="date"
                value={
                  start_date
                    ? `${start_date.slice(0, 4)}-${start_date.slice(4, 6)}-${start_date.slice(6, 8)}`
                    : ""
                }
                onChange={(e) => {
                  const date = e.target.value.replace(/-/g, "");
                  setStartDate(date);
                }}
                className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                투자 종료일
              </label>
              <input
                type="date"
                value={
                  end_date
                    ? `${end_date.slice(0, 4)}-${end_date.slice(4, 6)}-${end_date.slice(6, 8)}`
                    : ""
                }
                onChange={(e) => {
                  const date = e.target.value.replace(/-/g, "");
                  setEndDate(date);
                }}
                className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                수수료율
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={commission_rate}
                  onChange={(e) => setCommissionRate(Number(e.target.value))}
                  step={0.1}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  %
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                슬리피지
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={slippage}
                  onChange={(e) => setSlippage(Number(e.target.value))}
                  step={0.1}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  %
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 매수 조건 설정 */}
        <div id="매수 조건 설정" className="bg-bg-surface rounded-lg shadow-card p-8">
          <h2 className="text-2xl font-bold mb-6">
            <span className="text-brand-primary">매수</span>
            <span className="text-text-strong"> 조건 설정</span>
          </h2>

          <div className="space-y-6">
            {/* 매수 조건식 설정 */}
            <div>
              <label className="block text-base font-medium text-text-strong mb-4">
                매수 조건식 설정
              </label>

              {/* 조건 목록 */}
              <div className="space-y-3 mb-4">
                {buyConditions.map((condition) => (
                  <div
                    key={condition.id}
                    className="flex items-center gap-3 p-4 border border-border-default rounded-lg hover:border-accent-primary transition-colors"
                  >
                    {/* 조건 ID */}
                    <div className="w-12 h-12 flex items-center justify-center bg-brand-primary text-white font-bold text-lg rounded-md flex-shrink-0">
                      {condition.id}
                    </div>

                    {/* 조건 표시 */}
                    <div className="flex-1 text-text-body font-medium">
                      {getConditionExpression(condition)}
                    </div>

                    {/* 팩터 선택 버튼 */}
                    <button
                      onClick={() => openModal(condition.id)}
                      className="px-4 py-2 border border-accent-primary text-accent-primary rounded-sm hover:bg-accent-primary hover:text-white transition-colors text-sm font-medium flex items-center gap-2"
                    >
                      <Image src="/icons/search.svg" alt="" width={16} height={16} />
                      팩터 선택
                    </button>

                    {/* 부등호 선택 */}
                    <select
                      value={condition.operator}
                      onChange={(e) =>
                        handleOperatorChange(
                          condition.id,
                          e.target.value as ">=" | "<=" | ">" | "<" | "=" | "!=",
                        )
                      }
                      className="w-20 px-2 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
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
                      className="w-24 px-3 py-2 border border-border-default rounded-sm text-text-body text-center focus:outline-none focus:border-accent-primary"
                    />

                    {/* 삭제 버튼 */}
                    <button
                      onClick={() => removeBuyCondition(condition.id)}
                      className="w-10 h-10 flex items-center justify-center border border-brand-primary text-brand-primary rounded-sm hover:bg-brand-primary hover:text-white transition-colors"
                    >
                      <Image src="/icons/trash.svg" alt="삭제" width={20} height={20} />
                    </button>
                  </div>
                ))}
              </div>

              {/* 조건 추가 버튼 */}
              <div className="flex justify-center">
                <button
                  onClick={addBuyCondition}
                  className="px-6 py-2 border-2 border-dashed border-border-default text-text-muted rounded-lg hover:border-accent-primary hover:text-accent-primary transition-colors font-medium"
                >
                  + 조건식 추가
                </button>
              </div>
            </div>

            <div className="h-px bg-border-subtle" />

            {/* 논리 조건식 & 우선순위 */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-text-strong mb-2">
                  논리 조건식 작성
                </label>
                <input
                  type="text"
                  placeholder="A and B"
                  value={buy_logic}
                  onChange={(e) => setBuyLogic(e.target.value)}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-strong mb-2">
                  매수 종목 선택 우선순위
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={priority_factor}
                    onChange={(e) => setPriorityFactor(e.target.value)}
                    placeholder="예: {PBR}"
                    className="flex-1 px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                  />
                  <select
                    value={priority_order}
                    onChange={(e) => setPriorityOrder(e.target.value)}
                    className="px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                  >
                    <option value="desc">내림차순</option>
                    <option value="asc">오름차순</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 매수 비중 설정 */}
        <div id="매수 비중 설정" className="bg-bg-surface rounded-lg shadow-card p-8">
          <h2 className="text-2xl font-bold mb-6">
            <span className="text-brand-primary">매수</span>
            <span className="text-text-strong"> 비중 설정</span>
          </h2>

          <div className="grid grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                종목당 매수 비중
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={per_stock_ratio}
                  onChange={(e) => setPerStockRatio(Number(e.target.value))}
                  step={1}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  %
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                최대 보유 종목 수
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={max_holdings}
                  onChange={(e) => setMaxHoldings(Number(e.target.value))}
                  step={1}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  종목
                </span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium text-text-strong">
                  종목당 최대 매수 금액
                </label>
                <input
                  type="checkbox"
                  checked={enableMaxBuyValue}
                  onChange={(e) => {
                    setEnableMaxBuyValue(e.target.checked);
                    if (!e.target.checked) setMaxBuyValue(null);
                    else setMaxBuyValue(0);
                  }}
                  className="w-5 h-5 accent-brand-primary"
                />
              </div>
              <div className="relative">
                <input
                  type="number"
                  value={max_buy_value ?? 0}
                  onChange={(e) => setMaxBuyValue(Number(e.target.value))}
                  disabled={!enableMaxBuyValue}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary disabled:bg-bg-muted disabled:opacity-50"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  만원
                </span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <label className="text-sm font-medium text-text-strong">
                  1일 최대 매수 종목 수
                </label>
                <input
                  type="checkbox"
                  checked={enableMaxDailyStock}
                  onChange={(e) => {
                    setEnableMaxDailyStock(e.target.checked);
                    if (!e.target.checked) setMaxDailyStock(null);
                    else setMaxDailyStock(0);
                  }}
                  className="w-5 h-5 accent-brand-primary"
                />
              </div>
              <div className="relative">
                <input
                  type="number"
                  value={max_daily_stock ?? 0}
                  onChange={(e) => setMaxDailyStock(Number(e.target.value))}
                  disabled={!enableMaxDailyStock}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary disabled:bg-bg-muted disabled:opacity-50"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  종목
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 매수 방법 선택 */}
        <div id="매수 방법 선택" className="bg-bg-surface rounded-lg shadow-card p-8">
          <h2 className="text-2xl font-bold mb-6">
            <span className="text-brand-primary">매수</span>
            <span className="text-text-strong"> 방법 선택</span>
          </h2>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                매수 가격 기준
              </label>
              <select
                value={buyCostBasisSelect}
                onChange={(e) => setBuyCostBasisSelect(e.target.value)}
                className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
              >
                <option value="{전일 종가}">전일 종가</option>
                <option value="{당일 시가}">당일 시가</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-strong mb-2">
                가격 조정
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={buyCostBasisValue}
                  onChange={(e) => setBuyCostBasisValue(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                  %
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

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
