"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import type { Factor, SubFactor } from "@/types/api";

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
 * 팩터 선택 모달 - 디자인 시안 기반 재구현
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
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center"
      style={{ zIndex: 99999 }}
      onClick={handleClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-[700px] max-h-[90vh] overflow-hidden flex flex-col relative"
        style={{ zIndex: 100000 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 모달 헤더 */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex gap-8">
            <button
              onClick={() => setCurrentTab("factor")}
              className={`text-base font-semibold pb-1 transition-colors ${
                currentTab === "factor" ? "text-brand-primary" : "text-gray-400"
              }`}
            >
              팩터 선택하기
            </button>
            <button
              onClick={() => setCurrentTab("subfactor")}
              disabled={!selectedFactor}
              className={`text-base font-semibold pb-1 transition-colors ${
                currentTab === "subfactor" && selectedFactor
                  ? "text-brand-primary"
                  : "text-gray-400 disabled:cursor-not-allowed"
              }`}
            >
              함수 선택하기
            </button>
          </div>
        </div>

        {/* 모달 컨텐츠 */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoadingFactors || isLoadingSubFactors ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-600">데이터를 불러오는 중...</div>
            </div>
          ) : currentTab === "factor" ? (
            /* === 팩터 선택 탭 === */
            <div className="grid grid-cols-2 gap-6">
              {/* 좌측: 팩터 목록 (카테고리별 그룹화) */}
              <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2">
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
                              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                                selectedFactor?.id === factor.id
                                  ? "bg-brand-primary text-white font-medium"
                                  : "text-gray-700 hover:bg-gray-50"
                              }`}
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
              <div className="pl-6 border-l border-gray-200">
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
            <div className="grid grid-cols-2 gap-6">
              {/* 좌측: 서브팩터 목록 (라디오 버튼 스타일) */}
              <div>
                <h3 className="text-sm font-bold text-gray-900 mb-3">
                  전년된 함수 목록
                </h3>
                <ul className="space-y-2">
                  {subFactors.map((subFactor) => (
                    <li key={subFactor.id}>
                      <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                          type="radio"
                          name="subfactor"
                          checked={selectedSubFactor?.id === subFactor.id}
                          onChange={() => handleSubFactorSelect(subFactor)}
                          className="w-4 h-4 text-brand-primary focus:ring-brand-primary"
                        />
                        <span
                          className={`text-sm ${
                            selectedSubFactor?.id === subFactor.id
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
              <div className="pl-6 border-l border-gray-200">
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
                                className="flex items-center gap-2 cursor-pointer group"
                              >
                                <input
                                  type="radio"
                                  name="argument"
                                  checked={selectedArgument === arg}
                                  onChange={() => setSelectedArgument(arg)}
                                  className="w-4 h-4 text-brand-primary focus:ring-brand-primary"
                                />
                                <span
                                  className={`text-sm ${
                                    selectedArgument === arg
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
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">
                          조건식 미리보기
                        </h4>
                        <div className="bg-gray-50 p-3 rounded">
                          <p className="text-sm font-mono text-brand-primary mb-1">
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
        <div className="border-t border-gray-200 px-6 py-4 flex justify-center gap-3">
          <button
            onClick={
              currentTab === "factor"
                ? handleClose
                : () => setCurrentTab("factor")
            }
            className="px-6 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
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
            className="px-6 py-2 bg-brand-purple text-white rounded font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {currentTab === "factor" ? "다음 단계" : "선택 완료"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
