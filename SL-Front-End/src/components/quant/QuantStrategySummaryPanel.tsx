"use client";

import Image from "next/image";
import { useState } from "react";

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
  >("buy");

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
          <div className="h-16 border-b border-tag-neutral">
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
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setSelectedSummaryTab("buy")}
              className={`
                px-4 py-2 rounded text-sm font-medium transition-colors
                ${selectedSummaryTab === "buy"
                  ? "bg-brand-primary text-white"
                  : "bg-bg-surface-hover text-text-body hover:bg-bg-surface-active"
                }
              `}
            >
              매수 조건
            </button>
            <button
              onClick={() => setSelectedSummaryTab("sell")}
              className={`
                px-4 py-2 rounded text-sm font-medium transition-colors
                ${selectedSummaryTab === "sell"
                  ? "bg-brand-primary text-white"
                  : "bg-bg-surface-hover text-text-body hover:bg-bg-surface-active"
                }
              `}
            >
              매도 조건
            </button>
            <button
              onClick={() => setSelectedSummaryTab("target")}
              className={`
                px-4 py-2 rounded text-sm font-medium transition-colors
                ${selectedSummaryTab === "target"
                  ? "bg-brand-primary text-white"
                  : "bg-bg-surface-hover text-text-body hover:bg-bg-surface-active"
                }
              `}
            >
              매매 대상
            </button>
          </div>

          {/* 요약 내용 */}
          <div className="space-y-6">
            {selectedSummaryTab === "buy" && (
              <>
                {/* 일반 조건 */}
                <SummarySection
                  title="일반 조건"
                  items={[
                    { label: "백테스트 데이터 일봉", value: "투자 금액\n5,000만원" },
                    { label: "투자 시작일", value: "투자 종료일\n2025.12.30\n2025.12.31" },
                    { label: "수수료율", value: "01%" },
                  ]}
                />

                {/* 매수 조건 */}
                <SummarySection
                  title="매수 조건"
                  titleColor="text-accent-primary"
                  items={[
                    { label: "매수 조건식", value: "논리 조건식\nA, B\nA and B" },
                    {
                      label: "매수 종목 선택 우선순위",
                      value: "[높은 값부터] [조건식]",
                    },
                  ]}
                />

                {/* 매수 비중 설정 */}
                <SummarySection
                  title="매수 비중 설정"
                  titleColor="text-accent-primary"
                  items={[
                    { label: "종목당 매수 비중", value: "최대 보유 종목 수\n10%\n10종목" },
                    { label: "종목당 최대 매수 금액 (평균값)", value: "0만원" },
                    {
                      label: "1일 최대 매수 종목 수 (미적용시)",
                      value: "0만원",
                    },
                  ]}
                />

                {/* 매수 방법 설정 */}
                <SummarySection
                  title="매수 방법 설정"
                  titleColor="text-accent-primary"
                  items={[
                    {
                      label: "종목당 매수 비중",
                      value: "전일 종가 기준, 10%",
                    },
                  ]}
                />
              </>
            )}

            {selectedSummaryTab === "sell" && (
              <>
                <SummarySection
                  title="매도 조건"
                  items={[
                    { label: "목표가/손절가 설정", value: "미설정" },
                    { label: "보유 기간", value: "미설정" },
                    { label: "조건 매도", value: "미설정" },
                  ]}
                />
              </>
            )}

            {selectedSummaryTab === "target" && (
              <>
                <SummarySection
                  title="매매 대상"
                  items={[{ label: "선택된 종목", value: "0개" }]}
                />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 요약 섹션 컴포넌트
 */
interface SummarySectionProps {
  title: string;
  titleColor?: string;
  items: Array<{ label: string; value: string }>;
}

function SummarySection({
  title,
  titleColor = "text-text-strong",
  items,
}: SummarySectionProps) {
  return (
    <div>
      <h3 className={`text-sm font-semibold ${titleColor} mb-3`}>{title}</h3>
      <div className="space-y-3">
        {items.map((item, index) => (
          <div key={index} className="text-xs">
            <div className="text-text-muted mb-1">{item.label}</div>
            <div className="text-text-body whitespace-pre-line">
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
