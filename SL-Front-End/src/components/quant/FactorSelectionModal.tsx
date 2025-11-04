"use client";

import { Button, Input } from "@/components/common";
import type { Factor, SubFactor } from "@/constants";
import {
  FACTORS,
  getFactorsByCategory,
  searchFactors,
  SUB_FACTORS,
} from "@/constants";
import { useDebounce } from "@/hooks";
import { useEffect, useState } from "react";

/**
 * 팩터 선택 모달 Props 인터페이스
 */
interface FactorSelectionModalProps {
  /** 모달 오픈 여부 */
  isOpen: boolean;
  /** 모달 닫기 핸들러 */
  onClose: () => void;
  /**
   * 팩터와 함수 선택 완료 핸들러
   * @param factorId 선택된 팩터 ID
   * @param factorName 선택된 팩터 이름
   * @param subFactorId 선택된 함수 ID (기본값: "default")
   */
  onSelect: (
    factorId: string,
    factorName: string,
    subFactorId: string,
  ) => void;
  /** 현재 조건 초기값 (편집 모드) */
  initialValues?: {
    factorId?: string;
    subFactorId?: string;
  };
}

/**
 * 팩터 선택 모달 컴포넌트
 *
 * 3분할 레이아웃으로 구성:
 * - 왼쪽: 검색 + 카테고리별 팩터 목록
 * - 중앙: 선택된 팩터 정보 (이름, 공식)
 * - 오른쪽: 함수 목록
 *
 * 주요 기능:
 * 1. 실시간 검색 (디바운스 적용, 250ms)
 * 2. 검색 결과의 첫 번째 팩터 자동 선택
 * 3. 카테고리별 팩터 그룹핑
 * 4. 팩터/함수 선택 후 "입력" 버튼으로 확정
 */
export function FactorSelectionModal({
  isOpen,
  onClose,
  onSelect,
  initialValues,
}: FactorSelectionModalProps) {
  // ===== 상태 관리 =====

  /** 검색어 입력 상태 */
  const [searchQuery, setSearchQuery] = useState("");

  /** 디바운스가 적용된 검색어 (250ms 지연) */
  const debouncedQuery = useDebounce(searchQuery, 250);

  /** 현재 선택된 팩터 */
  const [selectedFactor, setSelectedFactor] = useState<Factor | null>(null);

  /** 현재 선택된 함수 ID (기본값: "default") */
  const [selectedSubFactorId, setSelectedSubFactorId] = useState(
    initialValues?.subFactorId || "default",
  );

  // ===== 검색 로직 및 자동 선택 =====

  /**
   * 디바운스된 검색어가 변경될 때 자동으로 첫 번째 결과 선택
   * - 검색어가 비어있으면: 모든 팩터 표시, 자동 선택 없음
   * - 검색 결과가 있으면: 첫 번째 팩터 자동 선택
   * - 검색 결과가 없으면: 선택 해제
   */
  useEffect(() => {
    if (debouncedQuery.trim() === "") {
      // 검색어가 없으면 선택 해제
      setSelectedFactor(null);
      return;
    }

    const results = searchFactors(debouncedQuery);
    if (results.length > 0) {
      // 첫 번째 검색 결과 자동 선택
      setSelectedFactor(results[0]);
    } else {
      // 검색 결과 없음
      setSelectedFactor(null);
    }
  }, [debouncedQuery]);

  /**
   * 모달이 열릴 때 상태 초기화 또는 초기값 설정
   */
  useEffect(() => {
    if (isOpen) {
      setSearchQuery("");

      // 초기값이 있으면 설정 (편집 모드)
      if (initialValues?.factorId) {
        const factor = FACTORS.find((f) => f.id === initialValues.factorId);
        setSelectedFactor(factor || null);
      } else {
        setSelectedFactor(null);
      }

      setSelectedSubFactorId(initialValues?.subFactorId || "default");
    }
  }, [isOpen, initialValues]);

  // ===== 이벤트 핸들러 =====

  /**
   * 팩터 선택 핸들러
   * @param factor 선택된 팩터 객체
   */
  const handleFactorSelect = (factor: Factor) => {
    setSelectedFactor(factor);
  };

  /**
   * 함수 선택 핸들러
   * @param subFactorId 선택된 함수 ID
   */
  const handleSubFactorSelect = (subFactorId: string) => {
    setSelectedSubFactorId(subFactorId);
  };

  /**
   * "입력" 버튼 클릭 핸들러
   * 선택된 팩터와 함수를 부모 컴포넌트로 전달
   */
  const handleSubmit = () => {
    if (!selectedFactor) return;

    onSelect(
      selectedFactor.id,
      selectedFactor.name,
      selectedSubFactorId,
    );
    onClose();
  };

  // ===== 데이터 준비 =====

  /** 카테고리별로 그룹핑된 팩터 목록 */
  const factorsByCategory = getFactorsByCategory();

  /**
   * 표시할 팩터 목록
   * - 검색어가 있으면: 검색 결과
   * - 검색어가 없으면: 카테고리별 전체 팩터
   */
  const displayFactors =
    debouncedQuery.trim() === ""
      ? factorsByCategory
      : { 검색결과: searchFactors(debouncedQuery) };

  // ===== 렌더링 =====

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 배경 오버레이 (클릭 시 모달 닫기) */}
      <button
        type="button"
        onClick={onClose}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        aria-label="Close modal"
      />

      {/* 모달 본체 */}
      <div className="relative z-10 w-[1000px] h-[769px] rounded-lg border border-border-default bg-[#1f1f1f] p-6 shadow-hard flex flex-col">
        {/* ===== 헤더 ===== */}
        <div className="mb-6 flex items-center justify-between border-b border-border-default pb-4">
          <div className="flex items-center gap-2">
            <span className="text-brand">⭐</span>
            <h2 className="text-lg font-semibold text-text-primary">
              팩터 선택
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-text-tertiary hover:text-text-primary"
          >
            ✕
          </button>
        </div>

        {/* ===== 3분할 레이아웃 (검색/팩터 목록 | 팩터 정보 | 함수 목록) ===== */}
        <div className="mb-6 grid grid-cols-[360px_1fr_360px] gap-4 flex-1 overflow-hidden">
          {/* ===== 왼쪽: 검색 + 팩터 목록 ===== */}
          <div className="flex flex-col">
            {/* 검색 입력 */}
            <div className="mb-3">
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="팩터 검색..."
                className="text-sm"
              />
            </div>

            {/* 팩터 목록 (카테고리별 그룹핑) */}
            <div className="flex-1 space-y-3 overflow-y-auto rounded-lg border border-border-default bg-[#232323] p-3">
              {Object.entries(displayFactors).map(
                ([category, factors]) =>
                  factors.length > 0 && (
                    <div key={category}>
                      {/* 카테고리 제목 */}
                      <h3 className="mb-2 text-xs font-semibold text-brand">
                        {category}
                      </h3>

                      {/* 팩터 목록 */}
                      <div className="space-y-1">
                        {factors.map((factor) => (
                          <button
                            key={factor.id}
                            type="button"
                            onClick={() => handleFactorSelect(factor)}
                            className={`w-full rounded px-2 py-1.5 text-left text-xs transition-colors ${
                              selectedFactor?.id === factor.id
                                ? "bg-brand/20 text-brand"
                                : "text-text-secondary hover:bg-bg-surface hover:text-text-primary"
                            }`}
                          >
                            {factor.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  ),
              )}

              {/* 검색 결과 없음 */}
              {debouncedQuery.trim() !== "" &&
                Object.values(displayFactors).every(
                  (factors) => factors.length === 0,
                ) && (
                  <div className="py-8 text-center text-sm text-text-tertiary">
                    검색 결과가 없습니다
                  </div>
                )}
            </div>
          </div>

          {/* ===== 중앙: 선택된 팩터 정보 및 조건식 설정 ===== */}
          <div className="flex flex-col rounded-lg border border-border-default bg-[#232323] p-4">
            {selectedFactor ? (
              <>
                {/* 팩터 이름 */}
                <div className="mb-4">
                  <h3 className="mb-1 text-sm font-medium text-brand">
                    팩터 이름
                  </h3>
                  <p className="text-base text-text-primary">
                    {selectedFactor.name}
                  </p>
                </div>

                {/* 팩터 카테고리 */}
                <div className="mb-4">
                  <h3 className="mb-1 text-sm font-medium text-brand">
                    카테고리
                  </h3>
                  <p className="text-sm text-text-secondary">
                    {selectedFactor.category}
                  </p>
                </div>

                {/* 계산 공식 */}
                <div className="flex-1">
                  <h3 className="mb-2 text-sm font-medium text-brand">
                    계산 공식
                  </h3>
                  <div className="rounded bg-bg-elevated p-3">
                    <code className="whitespace-pre-wrap text-xs text-text-primary">
                      {selectedFactor.formula}
                    </code>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-text-tertiary">
                팩터를 선택해주세요
              </div>
            )}
          </div>

          {/* ===== 오른쪽: 함수 목록 ===== */}
          <div className="flex flex-col">
            <h3 className="mb-3 text-sm font-medium text-text-secondary">
              함수 선택
            </h3>

            <div className="flex-1 space-y-1 overflow-y-auto rounded-lg border border-border-default bg-[#232323] p-3">
              {SUB_FACTORS.map((func: SubFactor) => (
                <button
                  key={func.id}
                  type="button"
                  onClick={() => handleSubFactorSelect(func.id)}
                  className={`w-full rounded px-2 py-1.5 text-left text-xs transition-colors ${
                    selectedSubFactorId === func.id
                      ? "bg-brand/20 text-brand"
                      : "text-text-secondary hover:bg-bg-surface hover:text-text-primary"
                  }`}
                >
                  <div className="font-medium">{func.name}</div>
                  {func.description && (
                    <div className="mt-0.5 text-xs text-text-tertiary">
                      {func.description}
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ===== 푸터: 입력 버튼 ===== */}
        <div className="flex justify-center">
          <Button onClick={handleSubmit} disabled={!selectedFactor}>
            입력
          </Button>
        </div>
      </div>
    </div>
  );
}
