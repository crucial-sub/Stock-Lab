"use client";

import Image from "next/image";
import { useState } from "react";

interface QuantStrategySidebarProps {
  activeTab: "buy" | "sell" | "target";
  onTabChange: (tab: "buy" | "sell" | "target") => void;
  isOpen: boolean;
  setIsOpen: (isOpen: boolean) => void;
}

/**
 * 퀀트 전략 생성 페이지의 좌측 사이드바
 * - 매수 조건, 매도 조건, 매매 대상 메뉴
 * - 화살표 버튼으로 열기/닫기 가능
 * - 닫혀도 완전히 사라지지 않고 화살표만 표시
 */
export default function QuantStrategySidebar({
  activeTab,
  onTabChange,
  isOpen,
  setIsOpen,
}: QuantStrategySidebarProps) {
  const [selectedSubItem, setSelectedSubItem] = useState<string>("일반 조건 설정");

  // 세부 항목 클릭 핸들러
  const handleSubItemClick = (tab: "buy" | "sell" | "target", subItem: string) => {
    setSelectedSubItem(subItem);
    onTabChange(tab);
  };

  return (
    <div
      className={`relative
        min-h-full
        transition-all duration-300 ease-in-out
        ${isOpen ? "w-[12.5rem]" : "w-10"}
      `}
    >
      {/* 화살표 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute right-3 top-6 z-10 hover:opacity-70 transition-opacity"
        aria-label={isOpen ? "사이드바 닫기" : "사이드바 열기"}
      >
        <Image
          src={isOpen ? "/icons/arrow_left.svg" : "/icons/arrow_right.svg"}
          alt={isOpen ? "닫기" : "열기"}
          width={20}
          height={20}
        />
      </button>

      {/* 사이드바 컨텐츠 - 열린 상태에서만 표시 */}
      {isOpen && (
        <div className="pt-16 px-6">
          {/* 매수 조건 섹션 */}
          <div className="mb-8">
            <h2 className="text-base font-semibold text-text-strong mb-3">
              매수 조건
            </h2>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => handleSubItemClick("buy", "일반 조건 설정")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "일반 조건 설정"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  일반 조건 설정
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleSubItemClick("buy", "매수 조건 설정")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "매수 조건 설정"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  매수 조건 설정
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleSubItemClick("buy", "매수 비중 설정")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "매수 비중 설정"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  매수 비중 설정
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleSubItemClick("buy", "매수 방법 선택")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "매수 방법 선택"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  매수 방법 선택
                </button>
              </li>
            </ul>
          </div>

          {/* 매도 조건 섹션 */}
          <div className="mb-8">
            <h2 className="text-base font-semibold text-text-strong mb-3">
              매도 조건
            </h2>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => handleSubItemClick("sell", "목표가 / 손절가")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "목표가 / 손절가"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  목표가 / 손절가
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleSubItemClick("sell", "보유 기간")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "보유 기간"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  보유 기간
                </button>
              </li>
              <li>
                <button
                  onClick={() => handleSubItemClick("sell", "조건 매도")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "조건 매도"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  조건 매도
                </button>
              </li>
            </ul>
          </div>

          {/* 매매 대상 설정 섹션 */}
          <div>
            <h2 className="text-base font-semibold text-text-strong mb-3">
              매매 대상 설정
            </h2>
            <ul className="space-y-2">
              <li>
                <button
                  onClick={() => handleSubItemClick("target", "매매 대상 선택")}
                  className={`
                    w-full text-left px-3 py-2 rounded text-sm
                    transition-colors
                    ${selectedSubItem === "매매 대상 선택"
                      ? "bg-brand-primary/10 text-brand-primary font-medium"
                      : "text-text-body hover:bg-bg-surface-hover"
                    }
                  `}
                >
                  매매 대상 선택
                </button>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
