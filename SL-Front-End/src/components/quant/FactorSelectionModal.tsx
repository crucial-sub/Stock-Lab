"use client";

import Image from "next/image";
import { useState } from "react";

interface FactorSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm?: (selectedFactor: string, selectedSubfactor?: string) => void;
  onSelect?: (factorId: string, factorName: string, subFactorId: string) => void;
  initialValues?: {
    factorId: string;
    subFactorId: string;
  };
}

/**
 * 팩터 선택 모달
 * Figma 디자인: 03-01.quant_page_new_strategy_buy_select_factor.png, 03-02.quant_page_new_strategy_buy_select_subfactor.png
 */
export function FactorSelectionModal({
  isOpen,
  onClose,
  onConfirm,
  onSelect,
  initialValues,
}: FactorSelectionModalProps) {
  const [currentTab, setCurrentTab] = useState<"factor" | "subfactor">("factor");
  const [selectedFactor, setSelectedFactor] = useState<string>("");
  const [selectedSubfactor, setSelectedSubfactor] = useState<string>("");
  const [nValue, setNValue] = useState<number>(1);
  const [conditionInput, setConditionInput] = useState<string>("");

  if (!isOpen) return null;

  // 팩터 목록
  const factors = [
    {
      name: "종합 점수",
      items: ["종합 점수", "종합 점수 순위"],
    },
    {
      name: "업종 종합 점수",
      items: [
        "업종 종합 점수",
        "업종 종합 점수 순위",
        "업종별 종합 순위 점수",
      ],
    },
    {
      name: "모멘텀",
      items: [
        "모멘텀 점수",
        "모멘텀 점수 순위",
        "업종 모멘텀 점수",
        "업종 모멘텀 점수 순위",
        "업종별 모멘텀 순위 점수",
        "모멘텀 질 A",
      ],
    },
  ];

  // 서브팩터 목록
  const subfactors = [
    {
      name: "전체 팩터 목록",
      items: [
        "기본",
        "과거값",
        "이동 평균",
        "비율",
        "순위",
        "최고값",
        "최저값",
        "변화율_기간",
        "변화율_기간",
      ],
    },
  ];

  const handleFactorSelect = (factor: string) => {
    setSelectedFactor(factor);
    setCurrentTab("subfactor");
  };

  const handleSubfactorSelect = (subfactor: string) => {
    setSelectedSubfactor(subfactor);
  };

  const handleConfirm = () => {
    if (onSelect) {
      // onSelect가 있으면 factorId, factorName, subFactorId 형태로 호출
      if (selectedFactor) {
        onSelect(selectedFactor, selectedFactor, selectedSubfactor || "");
        onClose();
      }
    } else if (onConfirm) {
      // onConfirm이 있으면 기존 방식대로 호출
      if (currentTab === "factor" && selectedFactor) {
        onConfirm(selectedFactor);
        onClose();
      } else if (currentTab === "subfactor" && selectedFactor) {
        onConfirm(selectedFactor, selectedSubfactor);
        onClose();
      }
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999]"
      onClick={onClose}
    >
      <div
        className="bg-bg-surface rounded-lg shadow-xl w-[800px] max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 모달 헤더 */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between bg-white">
          <div className="flex gap-6">
            <button
              onClick={() => setCurrentTab("factor")}
              className={`text-lg font-bold pb-1 border-b-2 transition-colors ${currentTab === "factor"
                ? "text-accent-danger border-accent-danger"
                : "text-gray-600 border-transparent hover:text-gray-900"
                }`}
            >
              팩터 선택하기
            </button>
            <button
              onClick={() => setCurrentTab("subfactor")}
              disabled={!selectedFactor}
              className={`text-lg font-bold pb-1 border-b-2 transition-colors ${currentTab === "subfactor" && selectedFactor
                ? "text-accent-danger border-accent-danger"
                : "text-gray-600 border-transparent hover:text-gray-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                }`}
            >
              함수 선택하기
            </button>
          </div>
          <button
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900"
          >
            <Image src="/icons/close.svg" alt="닫기" width={24} height={24} />
          </button>
        </div>

        {/* 모달 컨텐츠 */}
        <div className="p-6">
          {currentTab === "factor" ? (
            <div className="grid grid-cols-2 gap-6">
              {/* 좌측: 팩터 목록 */}
              <div>
                <h3 className="text-base font-bold text-gray-900 mb-3">
                  종합 점수
                </h3>
                <ul className="space-y-1 mb-6">
                  {factors[0].items.map((item) => (
                    <li key={item}>
                      <button
                        onClick={() => handleFactorSelect(item)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedFactor === item
                          ? "bg-accent-danger text-white font-medium"
                          : "text-gray-800 hover:bg-gray-100"
                          }`}
                      >
                        • {item}
                      </button>
                    </li>
                  ))}
                </ul>

                <h3 className="text-base font-bold text-gray-900 mb-3">
                  업종 종합 점수
                </h3>
                <ul className="space-y-1 mb-6">
                  {factors[1].items.map((item) => (
                    <li key={item}>
                      <button
                        onClick={() => handleFactorSelect(item)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedFactor === item
                          ? "bg-accent-danger text-white font-medium"
                          : "text-gray-800 hover:bg-gray-100"
                          }`}
                      >
                        • {item}
                      </button>
                    </li>
                  ))}
                </ul>

                <h3 className="text-base font-bold text-gray-900 mb-3">
                  모멘텀
                </h3>
                <ul className="space-y-1">
                  {factors[2].items.map((item) => (
                    <li key={item}>
                      <button
                        onClick={() => handleFactorSelect(item)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedFactor === item
                          ? "bg-accent-danger text-white font-medium"
                          : "text-gray-800 hover:bg-gray-100"
                          }`}
                      >
                        • {item}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 우측: 선택된 팩터 정보 */}
              <div>
                <h3 className="text-base font-bold text-gray-900 mb-3">
                  선택된 팩터 :{" "}
                  <span className="text-accent-danger">
                    {selectedFactor || "-"}
                  </span>
                </h3>
                {selectedFactor && (
                  <div className="text-sm text-text-body mb-4">
                    <p>
                      시장 전체를의 팩터 값을 반대별로 웰르 점수의 평균
                      점수
                    </p>
                    <p className="mt-2">
                      입력 방법 : 0 ~ 100점 (높을수록 높음)
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-6">
              {/* 좌측: 서브팩터 목록 */}
              <div>
                <h3 className="text-base font-bold text-gray-900 mb-3">
                  전체 팩터 목록
                </h3>
                <ul className="space-y-1">
                  {subfactors[0].items.map((item) => (
                    <li key={item}>
                      <button
                        onClick={() => handleSubfactorSelect(item)}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedSubfactor === item
                          ? "bg-accent-danger text-white font-medium"
                          : "text-gray-800 hover:bg-gray-100"
                          }`}
                      >
                        • {item}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 우측: 선택된 서브팩터 정보 */}
              <div>
                <h3 className="text-base font-bold text-gray-900 mb-3">
                  선택된 팩터 :{" "}
                  <span className="text-accent-danger">
                    {selectedSubfactor || "-"}
                  </span>
                </h3>
                {selectedSubfactor && (
                  <div>
                    <p className="text-sm text-gray-700 mb-4">
                      N일 이전의 팩터 값을 사용합니다.
                    </p>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="flex items-center gap-2">
                        <input
                          type="radio"
                          name="n-type"
                          value="n-1"
                          checked={nValue === 1}
                          onChange={() => setNValue(1)}
                          className="w-4 h-4"
                        />
                        <label className="text-sm text-gray-700 font-medium">
                          안 n i
                        </label>
                      </div>
                      <select className="border border-gray-300 rounded px-3 py-1 text-sm bg-white text-gray-800">
                        <option>1일</option>
                        <option>7일</option>
                        <option>30일</option>
                      </select>
                    </div>
                    <div className="mb-4">
                      <h4 className="text-sm font-bold text-gray-900 mb-2">
                        조건식 미리보기
                      </h4>
                      <input
                        type="text"
                        value={conditionInput}
                        onChange={(e) => setConditionInput(e.target.value)}
                        placeholder="과거값((종합점수),(1일))"
                        className="w-full border border-gray-300 rounded px-3 py-2 text-sm bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-primary"
                      />
                      <p className="text-xs text-gray-600 mt-1">
                        1일 전 종합점수 팩터 값입니다.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div className="border-t border-border-default px-6 py-4 flex justify-end gap-3">
          {currentTab === "subfactor" && (
            <button
              onClick={() => setCurrentTab("factor")}
              className="px-6 py-2 bg-bg-surface text-text-body rounded-lg font-medium hover:bg-bg-surface-hover transition-colors"
            >
              이전 단계
            </button>
          )}
          <button
            onClick={handleConfirm}
            disabled={!selectedFactor}
            className="px-6 py-2 bg-accent-danger text-white rounded-lg font-medium hover:bg-accent-danger/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {currentTab === "factor" ? "선택 완료" : "입력 완료"}
          </button>
        </div>
      </div>
    </div>
  );
}
