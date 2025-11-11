"use client";

import { getCurrentDate, getOneYearAgo } from "@/lib/date-utils";
import { useBacktestConfigStore } from "@/stores/backtestConfigStore";
import Image from "next/image";
import { useEffect, useState } from "react";

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

  // store에서 필요한 값들 가져오기
  const {
    is_day_or_month,
    initial_investment,
    start_date,
    end_date,
    commission_rate,
    slippage,
    buy_conditions,
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
    condition_sell,
    trade_targets,
    setStartDate,
    setEndDate,
  } = useBacktestConfigStore();

  // 날짜 초기화 (클라이언트 사이드에서만 실행)
  useEffect(() => {
    if (!start_date || !end_date) {
      setStartDate(getOneYearAgo());
      setEndDate(getCurrentDate());
    }
  }, [start_date, end_date, setStartDate, setEndDate]);

  // 탭 동기화
  useEffect(() => {
    setSelectedSummaryTab(activeTab);
  }, [activeTab]);

  return (
    <div className={`relative
        min-h-full
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
        <div className="">
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
                  <h3 className="text-base font-bold text-brand-primary">일반 조건</h3>
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
                      value={`${start_date.slice(0, 4)}.${start_date.slice(4, 6)}.${start_date.slice(6, 8)}`}
                    />
                    <SummaryItem
                      label="투자 종료일"
                      value={`${end_date.slice(0, 4)}.${end_date.slice(4, 6)}.${end_date.slice(6, 8)}`}
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
                  <h3 className="text-base font-bold text-brand-primary">매수 조건</h3>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <div>
                      <div className="text-base mb-1 text-tag-neutral">매수 조건식</div>
                      <div className="text-sm ">
                        {buy_conditions.length > 0 ? (
                          <div className="space-y-1">
                            {buy_conditions.map((c, idx) => (
                              <div key={idx} className="flex gap-2">
                                <span className="font-semibold">{c.name}</span>
                                <span>{c.exp_left_side}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          "미설정"
                        )}
                      </div>
                    </div>
                    <SummaryItem
                      label="논리 조건식"
                      value={buy_logic || "미설정"}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label="매수 종목 선택 우선순위"
                        value={priority_factor ? `[${priority_order === "desc" ? "높은 값부터" : "낮은 값부터"}] ${priority_factor}` : "미설정"}
                      />
                    </div>
                  </div>
                </div>

                {/* 매수 비중 설정 */}
                <div className="space-y-4">
                  <h3 className="text-base font-bold text-brand-primary">매수 비중 설정</h3>
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
                  <h3 className="text-base font-bold text-brand-primary">매수 방법 설정</h3>
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
                  <h3 className={`text-base font-bold ${target_and_loss ? "text-accent-primary" : "text-tag-neutral"}`}>
                    목표가 / 손절가 설정
                  </h3>
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
                  <h3 className={`text-base font-bold ${hold_days ? "text-accent-primary" : "text-tag-neutral"}`}>
                    보유 기간
                  </h3>
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
                  <h3 className={`text-base font-bold ${condition_sell ? "text-accent-primary" : "text-tag-neutral"}`}>
                    조건 매도
                  </h3>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-4">
                    <div>
                      <div className={`text-base mb-1 ${!condition_sell ? "text-tag-neutral" : "text-tag-neutral"}`}>
                        매도 조건식
                      </div>
                      <div className={`text-base ${!condition_sell ? "text-tag-neutral" : ""}`}>
                        {condition_sell && condition_sell.sell_conditions.length > 0 ? (
                          <div className="space-y-1">
                            {condition_sell.sell_conditions.map((c, idx) => (
                              <div key={idx} className="flex gap-2">
                                <span className="font-semibold">{c.name}</span>
                                <span>{c.exp_left_side}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          "미설정"
                        )}
                      </div>
                    </div>
                    <SummaryItem
                      label="논리 조건식"
                      value={condition_sell?.sell_logic || "미설정"}
                      disabled={!condition_sell}
                    />
                    <div className="col-span-2">
                      <SummaryItem
                        label="매도 가격 기준"
                        value={condition_sell
                          ? `${condition_sell.sell_price_basis} 기준, ${condition_sell.sell_price_offset > 0 ? "+" : ""}${condition_sell.sell_price_offset}%`
                          : "미설정"}
                        disabled={!condition_sell}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {selectedSummaryTab === "target" && (
              <>
                {/* 매매 대상 */}
                <div className="space-y-4">
                  <h3 className="text-base font-bold">매매 대상</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="text-xs text-tag-neutral mb-2">유니버스</div>
                      {trade_targets.selected_universes.length > 0 ? (
                        <ul className="list-disc list-inside text-sm  space-y-1">
                          {trade_targets.selected_universes.map((universe, index) => (
                            <li key={index}>{universe}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-sm ">선택 안 함</div>
                      )}
                    </div>
                    <div>
                      <div className="text-xs text-tag-neutral mb-2">테마</div>
                      {trade_targets.selected_themes.length > 0 ? (
                        <div className="grid grid-cols-3 gap-2">
                          {trade_targets.selected_themes.map((theme, index) => (
                            <div key={index} className="text-sm ">
                              {theme}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm ">선택 안 함</div>
                      )}
                    </div>
                    <div>
                      <div className="text-xs text-tag-neutral mb-2">개별 종목</div>
                      {trade_targets.selected_stocks.length > 0 ? (
                        <ul className="list-disc list-inside text-sm  space-y-1">
                          {trade_targets.selected_stocks.map((stock, index) => (
                            <li key={index}>{stock}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-sm ">선택 안 함</div>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 요약 항목 컴포넌트 (Figma 디자인에 맞춘 label-value 쌍)
 */
interface SummaryItemProps {
  label: string;
  value: string;
  disabled?: boolean;
}

function SummaryItem({ label, value, disabled = false }: SummaryItemProps) {
  return (
    <div>
      <div className={`mb-1 ${disabled ? "text-tag-neutral" : "text-text-strong"}`}>
        {label}
      </div>
      <div className={`font-semibold ${disabled ? "text-tag-neutral" : "text-text-strong"} whitespace-pre-line`}>
        {value}
      </div>
    </div>
  );
}
