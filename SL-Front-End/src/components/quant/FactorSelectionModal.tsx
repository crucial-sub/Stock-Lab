"use client";

import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import type { Factor, SubFactor } from "@/types/api";
import { useState } from "react";
import { createPortal } from "react-dom";

interface FactorSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (
    factorId: string,
    factorName: string,
    subFactorId: string,
    argument?: string,
  ) => void;
  initialValues?: {
    factorId: string;
    subFactorId: string;
    argument?: string;
  };
}

/**
 * 팩터 선택 모달 (반응형)
 *
 * @features
 * - 모바일: 전체 화면 모달
 * - 태블릿/데스크톱: 중앙 정렬 모달 (최대 700px)
 * - 터치 친화적인 버튼 크기 (44px 이상)
 * - 스크롤 가능한 콘텐츠 영역
 *
 * 1단계: 팩터 선택
 * 2단계: 서브팩터(함수) 선택
 * 3단계: 인자(argument) 선택 (서브팩터가 인자를 가진 경우)
 */
export function FactorSelectionModal({
  isOpen,
  onClose,
  onSelect,
  initialValues,
}: FactorSelectionModalProps) {
  // 서버 데이터 가져오기
  const { data: factors = [], isLoading: isLoadingFactors } = useFactorsQuery();
  const { data: subFactors = [], isLoading: isLoadingSubFactors } =
    useSubFactorsQuery();

  const [currentTab, setCurrentTab] = useState<"factor" | "subfactor">(
    "factor",
  );
  const [selectedFactor, setSelectedFactor] = useState<Factor | null>(null);
  const [selectedSubFactor, setSelectedSubFactor] = useState<SubFactor | null>(
    null,
  );
  const [selectedArgument, setSelectedArgument] = useState<string>("");

  if (!isOpen) return null;

  // SSR 환경에서 document가 없을 수 있음
  if (typeof window === "undefined") return null;

  // 카테고리별로 팩터 그룹화
  const groupedFactors = factors.reduce(
    (acc, factor) => {
      if (!acc[factor.category]) {
        acc[factor.category] = [];
      }
      acc[factor.category].push(factor);
      return acc;
    },
    {} as Record<string, Factor[]>,
  );

  const handleFactorSelect = (factor: Factor) => {
    setSelectedFactor(factor);
    // 바로 서브팩터 탭으로 이동하지 않음 (사용자가 "선택 완료" 버튼 클릭 시 이동)
  };

  const handleFactorConfirm = () => {
    if (!selectedFactor) return;
    setCurrentTab("subfactor");
  };

  const handleSubFactorSelect = (subFactor: SubFactor) => {
    setSelectedSubFactor(subFactor);
    // arguments가 있으면 첫 번째를 기본 선택
    if (subFactor.arguments && subFactor.arguments.length > 0) {
      setSelectedArgument(subFactor.arguments[0]);
    } else {
      setSelectedArgument("");
    }
  };

  const handleConfirm = () => {
    if (!selectedFactor || !selectedSubFactor) return;

    // 서브팩터가 arguments를 가지고 있으면 argument도 함께 전달
    const hasArguments =
      selectedSubFactor.arguments && selectedSubFactor.arguments.length > 0;

    onSelect(
      String(selectedFactor.id),
      selectedFactor.name,
      String(selectedSubFactor.id),
      hasArguments ? selectedArgument : undefined,
    );

    handleClose();
  };

  const handleClose = () => {
    // 초기화
    setSelectedFactor(null);
    setSelectedSubFactor(null);
    setSelectedArgument("");
    setCurrentTab("factor");
    onClose();
  };

  // 확인 버튼 활성화 조건
  const isConfirmEnabled = () => {
    if (!selectedFactor || !selectedSubFactor) return false;

    // 서브팩터가 arguments를 가지고 있으면 argument도 선택되어야 함
    if (selectedSubFactor.arguments && selectedSubFactor.arguments.length > 0) {
      return selectedArgument !== "";
    }

    return true;
  };

  // 조건식 미리보기 생성
  const getPreviewExpression = () => {
    if (!selectedFactor || !selectedSubFactor) return "";

    const factorName = selectedFactor.display_name;
    const subFactorName = selectedSubFactor.display_name;

    if (selectedArgument) {
      return `${subFactorName}(${factorName}, ${selectedArgument})`;
    } else {
      return `${subFactorName}(${factorName})`;
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-end sm:items-center justify-center"
      style={{ zIndex: 99999 }}
      onClick={handleClose}
    >
      <div
        className={[
          "bg-white shadow-2xl flex flex-col relative",
          // 모바일: 전체 화면 (하단에서 올라오는 시트)
          "w-full h-[90vh] rounded-t-2xl",
          // 태블릿/데스크톱: 중앙 모달
          "sm:w-[90vw] sm:max-w-[700px] sm:h-auto sm:max-h-[90vh] sm:rounded-lg",
        ].join(" ")}
        style={{ zIndex: 100000 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 모바일 드래그 핸들 */}
        <div className="sm:hidden flex justify-center pt-3 pb-2">
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
        </div>

        {/* 모달 헤더 */}
        <div className="border-b border-gray-200 px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between">
          <div className="flex gap-4 sm:gap-8 overflow-x-auto">
            <button
              onClick={() => setCurrentTab("factor")}
              className={[
                "text-sm sm:text-base font-semibold pb-1 transition-colors whitespace-nowrap",
                "min-h-[2.75rem] flex items-center",
                currentTab === "factor" ? "text-brand-purple" : "text-gray-400",
              ].join(" ")}
            >
              팩터 선택하기
            </button>
            <button
              onClick={() => setCurrentTab("subfactor")}
              disabled={!selectedFactor}
              className={[
                "text-sm sm:text-base font-semibold pb-1 transition-colors whitespace-nowrap",
                "min-h-[2.75rem] flex items-center",
                currentTab === "subfactor" && selectedFactor
                  ? "text-brand-purple"
                  : "text-gray-400 disabled:cursor-not-allowed",
              ].join(" ")}
            >
              함수 선택하기
            </button>
          </div>
          {/* 데스크톱 닫기 버튼 */}
          <button
            onClick={handleClose}
            className="hidden sm:flex items-center justify-center w-10 h-10 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="닫기"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* 모달 컨텐츠 */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {isLoadingFactors || isLoadingSubFactors ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-600">데이터를 불러오는 중...</div>
            </div>
          ) : currentTab === "factor" ? (
            /* === 팩터 선택 탭 === */
            <div className="flex flex-col sm:grid sm:grid-cols-2 gap-4 sm:gap-6">
              {/* 좌측: 팩터 목록 (카테고리별 그룹화) */}
              <div className="space-y-4 max-h-[40vh] sm:max-h-[500px] overflow-y-auto pr-2">
                {Object.entries(groupedFactors).map(
                  ([category, categoryFactors]) => (
                    <div key={category}>
                      <h3 className="text-sm font-bold text-gray-900 mb-2 sticky top-0 bg-white py-1">
                        {category}
                      </h3>
                      <ul className="space-y-1">
                        {categoryFactors.map((factor) => (
                          <li key={factor.id}>
                            <button
                              onClick={() => handleFactorSelect(factor)}
                              className={[
                                "w-full text-left px-3 py-3 sm:py-2 rounded text-sm transition-colors",
                                "min-h-[2.75rem]",
                                selectedFactor?.id === factor.id
                                  ? "bg-brand-primary text-white font-medium"
                                  : "text-gray-700 hover:bg-gray-50",
                              ].join(" ")}
                            >
                              • {factor.display_name}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ),
                )}
              </div>

              {/* 우측: 선택된 팩터 정보 */}
              <div className="pt-4 sm:pt-0 sm:pl-6 border-t sm:border-t-0 sm:border-l border-gray-200">
                <h3 className="text-sm font-bold text-gray-900 mb-4">
                  선택된 팩터:{" "}
                  <span className="text-brand-primary">
                    {selectedFactor ? selectedFactor.display_name : "-"}
                  </span>
                </h3>
                {selectedFactor ? (
                  <div className="space-y-3">
                    {selectedFactor.description && (
                      <div className="text-sm text-gray-700">
                        <p className="whitespace-pre-line">
                          {selectedFactor.description}
                        </p>
                      </div>
                    )}
                    <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                      <p className="font-medium text-gray-800 mb-1">
                        일반 범위:
                      </p>
                      <p>0 ~ 100점 (높을수록 좋음)</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">팩터를 선택해주세요</p>
                )}
              </div>
            </div>
          ) : (
            /* === 서브팩터(함수) 선택 탭 === */
            <div className="flex flex-col sm:grid sm:grid-cols-2 gap-4 sm:gap-6">
              {/* 좌측: 서브팩터 목록 (라디오 버튼 스타일) */}
              <div>
                <h3 className="text-sm font-bold text-gray-900 mb-3">
                  전년된 함수 목록
                </h3>
                <ul className="space-y-2">
                  {subFactors.map((subFactor) => (
                    <li key={subFactor.id}>
                      <label className="flex items-center gap-3 cursor-pointer group min-h-[2.75rem] py-2">
                        <input
                          type="radio"
                          name="subfactor"
                          checked={selectedSubFactor?.id === subFactor.id}
                          onChange={() => handleSubFactorSelect(subFactor)}
                          className="w-5 h-5 sm:w-4 sm:h-4 text-brand-primary focus:ring-brand-primary"
                        />
                        <span
                          className={`text-sm ${selectedSubFactor?.id === subFactor.id
                              ? "text-brand-primary font-medium"
                              : "text-gray-700 group-hover:text-gray-900"
                            }`}
                        >
                          {subFactor.display_name}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 우측: 선택된 서브팩터 정보 + 인자 선택 */}
              <div className="pt-4 sm:pt-0 sm:pl-6 border-t sm:border-t-0 sm:border-l border-gray-200">
                {selectedSubFactor ? (
                  <div className="space-y-4">
                    {/* 함수 설명 */}
                    <div>
                      <h3 className="text-sm font-bold text-gray-900 mb-2">
                        선택된 함수:{" "}
                        <span className="text-brand-primary">
                          {selectedSubFactor.display_name}
                        </span>
                      </h3>
                      <p className="text-sm text-gray-700 mb-3">
                        {selectedSubFactor.description}
                      </p>
                    </div>

                    {/* 인자 선택 (arguments가 있는 경우) - 라디오 버튼 스타일 */}
                    {selectedSubFactor.arguments &&
                      selectedSubFactor.arguments.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-sm font-semibold text-gray-800">
                            인자 선택{" "}
                            <span className="text-brand-primary">*</span>
                          </p>
                          <div className="space-y-2">
                            {selectedSubFactor.arguments.map((arg) => (
                              <label
                                key={arg}
                                className="flex items-center gap-3 cursor-pointer group min-h-[2.75rem] py-2"
                              >
                                <input
                                  type="radio"
                                  name="argument"
                                  checked={selectedArgument === arg}
                                  onChange={() => setSelectedArgument(arg)}
                                  className="w-5 h-5 sm:w-4 sm:h-4 text-brand-primary focus:ring-brand-primary"
                                />
                                <span
                                  className={`text-sm ${selectedArgument === arg
                                      ? "text-brand-primary font-medium"
                                      : "text-gray-700 group-hover:text-gray-900"
                                    }`}
                                >
                                  {arg}
                                </span>
                              </label>
                            ))}
                          </div>
                        </div>
                      )}

                    {/* 조건식 미리보기 */}
                    {selectedFactor && selectedSubFactor && (
                      <div className="mt-4 sm:mt-6 pt-4 border-t border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">
                          조건식 미리보기
                        </h4>
                        <div className="bg-gray-50 p-3 rounded">
                          <p className="text-sm font-mono text-brand-primary mb-1 break-all">
                            {getPreviewExpression()}
                          </p>
                          <p className="text-xs text-gray-600">
                            입력한 공식으로 팩터 값이 진행됩니다.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">함수를 선택해주세요</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 모달 푸터 */}
        <div className="border-t border-gray-200 px-4 sm:px-6 py-4 flex flex-col sm:flex-row justify-center gap-3">
          <button
            onClick={
              currentTab === "factor"
                ? handleClose
                : () => setCurrentTab("factor")
            }
            className={[
              "px-6 py-3 sm:py-2 border border-gray-300 rounded text-gray-700",
              "hover:bg-gray-50 transition-colors text-sm font-medium",
              "min-h-[2.75rem] order-2 sm:order-1",
            ].join(" ")}
          >
            {currentTab === "factor" ? "취소" : "이전 단계"}
          </button>
          <button
            onClick={
              currentTab === "factor" ? handleFactorConfirm : handleConfirm
            }
            disabled={
              currentTab === "factor" ? !selectedFactor : !isConfirmEnabled()
            }
            className={[
              "px-6 py-3 sm:py-2 bg-brand-purple text-white rounded font-medium",
              "hover:opacity-90 transition-opacity",
              "disabled:opacity-50 disabled:cursor-not-allowed text-sm",
              "min-h-[2.75rem] order-1 sm:order-2",
            ].join(" ")}
          >
            {currentTab === "factor" ? "다음 단계" : "선택 완료"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
