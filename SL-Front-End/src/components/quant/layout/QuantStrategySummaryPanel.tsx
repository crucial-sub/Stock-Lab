"use client";

import { getCurrentDate, getOneYearAgo } from "@/lib/date-utils";
import { useBacktestConfigStore } from "@/stores/backtestConfigStore";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";

interface QuantStrategySummaryPanelProps {
  activeTab: "buy" | "sell" | "target";
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

interface SummaryTabsType {
  tabName: "buy" | "sell" | "target",
  tabDisplayName: string,
  items: {
    [key: string]: string
  }[]
}

/**
 * 퀀트 전략 생성 페이지의 우측 요약 패널
 * - 설정한 조건들의 요약 표시
 * - 화살표 버튼으로 열기/닫기 가능
 * - 닫혀도 완전히 사라지지 않고 화살표만 표시
 */

export default function QuantStrategySummaryPanel({
  activeTab,
  isOpen,
  setIsOpen,
}: QuantStrategySummaryPanelProps) {
  const [selectedSummaryTab, setSelectedSummaryTab] = useState<
    "buy" | "sell" | "target"
  >(activeTab);

  // 클라이언트 전용 마운트 상태
  const [isMounted, setIsMounted] = useState(false);

  // ✅ useShallow hook 사용 (Zustand 5.0+)
  // 데이터 필드들을 객체로 선택 (useShallow가 얕은 비교 수행)
  const {
    is_day_or_month,
    initial_investment,
    start_date,
    end_date,
    commission_rate,
    slippage,
    buyConditionsUI,
    buy_logic,
    priority_factor,
    priority_order,
    per_stock_ratio,
    max_holdings,
    max_buy_value,
    max_daily_stock,
    buy_price_basis,
    buy_price_offset,
    target_and_loss,
    hold_days,
    sellConditionsUI,
    condition_sell,
    trade_targets,
  } = useBacktestConfigStore(
    useShallow((state) => ({
      is_day_or_month: state.is_day_or_month,
      initial_investment: state.initial_investment,
      start_date: state.start_date,
      end_date: state.end_date,
      commission_rate: state.commission_rate,
      slippage: state.slippage,
      buyConditionsUI: state.buyConditionsUI,
      buy_logic: state.buy_logic,
      priority_factor: state.priority_factor,
      priority_order: state.priority_order,
      per_stock_ratio: state.per_stock_ratio,
      max_holdings: state.max_holdings,
      max_buy_value: state.max_buy_value,
      max_daily_stock: state.max_daily_stock,
      buy_price_basis: state.buy_price_basis,
      buy_price_offset: state.buy_price_offset,
      target_and_loss: state.target_and_loss,
      hold_days: state.hold_days,
      sellConditionsUI: state.sellConditionsUI,
      condition_sell: state.condition_sell,
      trade_targets: state.trade_targets,
    }))
  );

  // setter 함수들은 별도로 선택 (안정적인 참조)
  const setStartDate = useBacktestConfigStore(state => state.setStartDate);
  const setEndDate = useBacktestConfigStore(state => state.setEndDate);

  // 날짜 초기화 (클라이언트 사이드에서만 실행)
  // setter 함수는 안정적이므로 dependency에서 제외 (React Compiler가 자동 처리)
  useEffect(() => {
    if (!start_date || !end_date) {
      setStartDate(getOneYearAgo());
      setEndDate(getCurrentDate());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [start_date, end_date]);

  // 클라이언트 마운트 감지
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // 탭 동기화
  useEffect(() => {
    setSelectedSummaryTab(activeTab);
  }, [activeTab]);

  return (
    <div className={`relative
        transition-all duration-300 ease-in-out
        ${isOpen ? "w-[26.25rem]" : "w-10"}
      `}>
      {/* 화살표 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`absolute ${isOpen ? "left-5 top-5" : "right-2 left-2 top-5"} top-5 z-10 hover:opacity-70 transition-opacity`}
        aria-label={isOpen ? "요약 패널 닫기" : "요약 패널 열기"}
      >
        <Image
          src={isOpen ? "/icons/arrow_right.svg" : "/icons/arrow_left.svg"}
          alt={isOpen ? "닫기" : "열기"}
          width={24}
          height={24}
        />
      </button>

      {/* 요약 패널 컨텐츠 - 열린 상태에서만 표시 */}
      {isOpen && (
        <div className="mb-10">
          {/* 요약보기 / AI 헬퍼 탭 */}
          <div className="h-16 border-b border-tag-neutral mb-5">
            <div className="flex pl-16">
              <div className="flex w-[44.5rem] border-b-2 border-brand-primary h-16 justify-center items-center">
                <h2 className="text-xl font-semibold text-brand-primary">
                  요약보기
                </h2>
              </div>
              <div className="flex w-[44.5rem] h-16 justify-center items-center">
                <h2 className="text-xl font-normal text-tag-neutral">
                  AI 헬퍼
                </h2>
              </div>
            </div>
          </div>

          {/* 탭 버튼 */}
          <div className="flex gap-3 px-4 mb-6 w-full justify-center">
            <button
              onClick={() => setSelectedSummaryTab("buy")}
              className={`
                px-5 py-2 rounded-md text-[1.25rem] font-semibold transition-colors
                ${selectedSummaryTab === "buy"
                  ? "bg-brand-primary text-white"
                  : "bg-bg-surface-hover  hover:bg-bg-surface-active"
                }
              `}
            >
              매수 조건
            </button>
            <button
              onClick={() => setSelectedSummaryTab("sell")}
              className={`
                px-5 py-2 rounded-md text-[1.25rem] font-semibold transition-colors
                ${selectedSummaryTab === "sell"
                  ? "bg-accent-primary text-white"
                  : ""
                }
              `}
            >
              매도 조건
            </button>
            <button
              onClick={() => setSelectedSummaryTab("target")}
              className={`
                px-5 py-2 rounded-md text-[1.25rem] font-semibold transition-colors
                ${selectedSummaryTab === "target"
                  ? "bg-[#f0f0f0]"
                  : "bg-bg-surface-hover  hover:bg-bg-surface-active"
                }
              `}
            >
              매매 대상
            </button>
          </div>

          {/* 요약 내용 */}
          <div className="px-10 space-y-8">
            {selectedSummaryTab === "buy" && (
              <>
                {/* 일반 조건 */}
                <div className="space-y-4">
                  <FieldTitle tab="buy">일반 조건</FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <SummaryItem
                      label="백테스트 데이터"
                      value={is_day_or_month === "daily" ? "일봉" : "월봉"}
                    />
                    <SummaryItem
                      label="투자 금액"
                      value={`${initial_investment.toLocaleString()}만원`}
                    />
                    <SummaryItem
                      label="투자 시작일"
                      value={isMounted ? `${start_date.slice(0, 4)}.${start_date.slice(4, 6)}.${start_date.slice(6, 8)}` : ""}
                    />
                    <SummaryItem
                      label="투자 종료일"
                      value={isMounted ? `${end_date.slice(0, 4)}.${end_date.slice(4, 6)}.${end_date.slice(6, 8)}` : ""}
                    />
                    <SummaryItem
                      label="수수료율"
                      value={`${commission_rate}%`}
                    />
                    <SummaryItem
                      label="슬리피지"
                      value={`${slippage}%`}
                    />
                  </div>
                </div>

                {/* 매수 조건 */}
                <div className="space-y-4">
                  <FieldTitle tab="buy">매수 조건</FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <div>
                      <div className={`text-[1rem] font-normal ${buyConditionsUI.length > 0 && buyConditionsUI.some(c => c.factorName) ? "" : "text-tag-neutral"}`}>매수 조건식</div>
                      <div className={`font-semibold text-[1rem] ${buyConditionsUI.length > 0 && buyConditionsUI.some(c => c.factorName) ? "" : "text-tag-neutral"}`}>
                        {buyConditionsUI.length > 0 && buyConditionsUI.some(c => c.factorName) ? (
                          <div className="space-y-1">
                            {buyConditionsUI.filter(c => c.factorName).map((c) => {
                              let expression = '';
                              if (c.subFactorName) {
                                expression = c.argument
                                  ? `${c.subFactorName}({${c.factorName}},{${c.argument}})`
                                  : `${c.subFactorName}({${c.factorName}})`;
                              } else {
                                expression = `{${c.factorName}}`;
                              }
                              return (
                                <div key={c.id} className="flex gap-2">
                                  <span className="font-semibold">{c.id}:</span>
                                  <span>{expression} {c.operator} {c.value}</span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          "미설정"
                        )}
                      </div>
                    </div>
                    <SummaryItem
                      label="논리 조건식"
                      value={buy_logic || "미설정"}
                      disabled={!buy_logic}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label="매수 종목 선택 우선순위"
                        value={priority_factor ? `[${priority_order === "desc" ? "높은 값부터" : "낮은 값부터"}] ${priority_factor}` : "미설정"}
                        disabled={!priority_factor}
                      />
                    </div>
                  </div>
                </div>

                {/* 매수 비중 설정 */}
                <div className="space-y-4">
                  <FieldTitle tab="buy">매수 비중 설정</FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <SummaryItem
                      label="종목당 매수 비중"
                      value={`${per_stock_ratio}%`}
                    />
                    <SummaryItem
                      label="최대 보유 종목 수"
                      value={`${max_holdings}종목`}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label={`종목당 최대 매수 금액 ${max_buy_value !== null ? "(활성화)" : "(비활성화)"}`}
                        value={max_buy_value !== null ? `${max_buy_value.toLocaleString()}만원` : "0만원"}
                        disabled={max_buy_value === null}
                      />
                    </div>
                    <div className="col-span-2">
                      <SummaryItem
                        label={`1일 최대 매수 종목 수 ${max_daily_stock !== null ? "(활성화)" : "(비활성화)"}`}
                        value={max_daily_stock !== null ? `${max_daily_stock}종목` : "0종목"}
                        disabled={max_daily_stock === null}
                      />
                    </div>
                  </div>
                </div>

                {/* 매수 방법 설정 */}
                <div className="space-y-4">
                  <FieldTitle tab="buy">매수 방법 설정</FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <div className="col-span-2">
                      <SummaryItem
                        label="매수 가격 기준"
                        value={`${buy_price_basis} 기준, ${buy_price_offset > 0 ? "+" : ""}${buy_price_offset}%`}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {selectedSummaryTab === "sell" && (
              <>
                {/* 목표가/손절가 설정 */}
                <div className="space-y-4">
                  <FieldTitle tab="sell" isActive={target_and_loss !== null}>
                    목표가 / 손절가 설정
                  </FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <SummaryItem
                      label="목표가"
                      value={target_and_loss?.target_gain !== null && target_and_loss?.target_gain !== undefined
                        ? `${target_and_loss.target_gain}%`
                        : "미설정"}
                      disabled={!target_and_loss}
                    />
                    <SummaryItem
                      label="손절가"
                      value={target_and_loss?.stop_loss !== null && target_and_loss?.stop_loss !== undefined
                        ? `${target_and_loss.stop_loss}%`
                        : "미설정"}
                      disabled={!target_and_loss}
                    />
                  </div>
                </div>

                {/* 보유 기간 */}
                <div className="space-y-4">
                  <FieldTitle tab="sell" isActive={hold_days !== null}>
                    보유 기간
                  </FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <SummaryItem
                      label="최소 보유 기간"
                      value={hold_days ? `${hold_days.min_hold_days}일` : "미설정"}
                      disabled={!hold_days}
                    />
                    <SummaryItem
                      label="최대 보유 기간"
                      value={hold_days ? `${hold_days.max_hold_days}일` : "미설정"}
                      disabled={!hold_days}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label="매도 가격 기준"
                        value={hold_days
                          ? `${hold_days.sell_price_basis} 기준, ${hold_days.sell_price_offset > 0 ? "+" : ""}${hold_days.sell_price_offset}%`
                          : "미설정"}
                        disabled={!hold_days}
                      />
                    </div>
                  </div>
                </div>

                {/* 조건 매도 */}
                <div className="space-y-4">
                  <FieldTitle tab="sell" isActive={condition_sell !== null}>
                    조건 매도
                  </FieldTitle>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <div>
                      <div className={`text-[1rem] font-normal ${condition_sell && sellConditionsUI.length > 0 && sellConditionsUI.some(c => c.factorName) ? "" : "text-tag-neutral"}`}>
                        매도 조건식
                      </div>
                      <div className={`font-semibold text-[1rem] ${condition_sell && sellConditionsUI.length > 0 && sellConditionsUI.some(c => c.factorName) ? "" : "text-tag-neutral"}`}>
                        {condition_sell && sellConditionsUI.length > 0 && sellConditionsUI.some(c => c.factorName) ? (
                          <div className="space-y-1">
                            {sellConditionsUI.filter(c => c.factorName).map((c) => {
                              let expression = '';
                              if (c.subFactorName) {
                                expression = c.argument
                                  ? `${c.subFactorName}({${c.factorName}},{${c.argument}})`
                                  : `${c.subFactorName}({${c.factorName}})`;
                              } else {
                                expression = `{${c.factorName}}`;
                              }
                              return (
                                <div key={c.id} className="flex gap-2">
                                  <span className="font-semibold">{c.id}:</span>
                                  <span>{expression} {c.operator} {c.value}</span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          "미설정"
                        )}
                      </div>
                    </div>
                    <SummaryItem
                      label="논리 조건식"
                      value={condition_sell?.sell_logic || "미설정"}
                      disabled={!condition_sell?.sell_logic}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label="매도 가격 기준"
                        value={condition_sell
                          ? `${condition_sell.sell_price_basis} 기준, ${condition_sell.sell_price_offset > 0 ? "+" : ""}${condition_sell.sell_price_offset}%`
                          : "미설정"}
                        disabled={!condition_sell?.sell_price_basis}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {selectedSummaryTab === "target" && (
              <>
                {/* 매매 대상 */}
                <div className="space-y-7">
                  {/* 종목 개수 표시 */}
                  <div className="space-y-5">
                    <FieldTitle tab="target">매매 대상 종목</FieldTitle>
                    {trade_targets.total_stock_count !== undefined && (
                      <div className="space-y-5">
                        <div className="flex flex-col gap-1">
                          <span>선택한 매매 대상 종목</span>
                          <span className="font-semibold">{trade_targets.selected_stock_count || 0} 종목</span>
                        </div>

                        <div className="flex flex-col gap-1">
                          <span>전체 종목</span>
                          <span className="font-semibold">{trade_targets.total_stock_count} 종목</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-5">
                    <FieldTitle tab="target">선택한 테마</FieldTitle>
                    <div className="flex gap-[6.5625rem]">
                      <div className="flex flex-col gap-1">
                        <span>선택한 테마 수</span>
                        <span className="font-semibold">{trade_targets.selected_themes.length}개</span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span>전체 테마 수</span>
                        <span className="font-semibold">16개</span>
                      </div>
                    </div>
                    {
                      trade_targets.selected_themes.length > 0 ? (
                        <div className="grid grid-cols-3 gap-2">
                          {trade_targets.selected_themes.map((theme, index) => (
                            <div key={index} className="text-sm ">
                              {theme}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm ">선택 안 함</div>
                      )
                    }
                  </div>
                  <div className="space-y-5">
                    <FieldTitle tab="target">선택한 세부 종목 ({trade_targets.selected_stocks.length}개)</FieldTitle>
                    {
                      trade_targets.selected_stocks.length > 0 ? (
                        <ul className="list-disc list-inside text-sm  space-y-1">
                          {trade_targets.selected_stocks.map((stock, index) => (
                            <li key={index}>{stock}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-sm ">선택 안 함</div>
                      )
                    }
                  </div>
                </div >
              </>
            )
            }
          </div >
        </div >
      )}
    </div >
  );
}

/**
 * 1. 필드 제목 컴포넌트
 * - 일반 조건, 매수 조건, 매수 비중 설정 등의 큰 섹션 제목
 */
interface FieldTitleProps {
  children: React.ReactNode;
  tab: "buy" | "sell" | "target";
  isActive?: boolean; // 매도 조건 탭에서 활성화 여부
}

function FieldTitle({ children, tab, isActive = true }: FieldTitleProps) {
  let colorClass = "";

  if (tab === "buy") {
    colorClass = "text-brand-primary";
  } else if (tab === "sell") {
    colorClass = isActive ? "text-accent-primary" : "text-tag-neutral";
  } else {
    // target 탭은 색상 없음 (기본 text-strong)
    colorClass = "";
  }

  return (
    <h3 className={`font-semibold text-[1.25rem] ${colorClass}`}>
      {children}
    </h3>
  );
}

/**
 * 2. 세부 항목 제목 컴포넌트
 * - 백테스트 데이터, 투자금액, 매수 조건식 등의 항목 레이블
 */
interface ItemLabelProps {
  children: React.ReactNode;
  disabled?: boolean;
}

function ItemLabel({ children, disabled = false }: ItemLabelProps) {
  return (
    <div className={`font-normal text-[1rem] ${disabled ? "text-tag-neutral" : ""}`}>
      {children}
    </div>
  );
}

/**
 * 3. 세부 항목 내용 컴포넌트
 * - 일봉, 5000만원 등의 실제 값
 */
interface ItemValueProps {
  children: React.ReactNode;
  disabled?: boolean;
}

function ItemValue({ children, disabled = false }: ItemValueProps) {
  return (
    <div className={`font-semibold text-[1rem] ${disabled ? "text-tag-neutral" : ""}`}>
      {children}
    </div>
  );
}

/**
 * 요약 항목 컴포넌트 (label-value 쌍)
 * - ItemLabel과 ItemValue를 조합한 편의 컴포넌트
 */
interface SummaryItemProps {
  label: string;
  value: string;
  disabled?: boolean;
}

function SummaryItem({ label, value, disabled = false }: SummaryItemProps) {
  return (
    <div>
      <ItemLabel disabled={disabled}>
        {label}
      </ItemLabel>
      <ItemValue disabled={disabled}>
        {value}
      </ItemValue>
    </div>
  );
}
