"use client";

import {
  compareFactorCategoryOrder,
  getFactorCategoryLabel,
} from "@/constants/factorCategories";
import { useDebounce } from "@/hooks";
import { useFactorsQuery } from "@/hooks/useFactorsQuery";
import { useSubFactorsQuery } from "@/hooks/useSubFactorsQuery";
import type { Factor, SubFactor } from "@/types/api";
import { useEffect, useMemo, useState } from "react";

type ModalFactor = Factor & { formula?: string };

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
   * @param operator 선택된 부등호
   * @param value 비교 값
   */
  onSelect: (
    factorId: string,
    factorName: string,
    subFactorId: string,
    operator: ">=" | "<=" | ">" | "<" | "=" | "!=",
    value: number,
  ) => void;
  /** 현재 조건 초기값 (편집 모드) */
  initialValues?: {
    factorId?: string;
    subFactorId?: string;
    operator?: ">=" | "<=" | ">" | "<" | "=" | "!=";
    value?: number;
  };
}

// SVG 아이콘 컴포넌트
function CloseIcon() {
  return (
    <svg className="size-[32px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg className="size-[32px]" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg className="size-[20px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

/**
 * 팩터 선택 모달 컴포넌트
 *
 * 4분할 레이아웃으로 구성:
 * - 왼쪽 1: 검색 + 카테고리별 팩터 목록
 * - 왼쪽 2: 선택된 팩터 정보
 * - 오른쪽 1: 함수 목록
 * - 오른쪽 2: 선택된 함수 정보
 *
 * 주요 기능:
 * 1. 실시간 검색 (디바운스 적용, 250ms)
 * 2. 검색 결과의 첫 번째 팩터 자동 선택
 * 3. 카테고리별 팩터 그룹핑 및 확장/축소
 * 4. 팩터/함수 선택 후 "입력" 버튼으로 확정
 */
export function FactorSelectionModal({
  isOpen,
  onClose,
  onSelect,
  initialValues,
}: FactorSelectionModalProps) {
  const {
    data: fetchedFactors = [],
    isLoading: isLoadingFactors,
  } = useFactorsQuery();
  const factors = fetchedFactors as ModalFactor[];

  const {
    data: fetchedSubFactors = [],
    isLoading: isLoadingSubFactors,
  } = useSubFactorsQuery();
  const subFactors = fetchedSubFactors as SubFactor[];

  const factorsByCategory = useMemo(() => {
    if (!factors.length) {
      return {};
    }

    const grouped = factors.reduce((acc, factor) => {
      const categoryKey = getFactorCategoryLabel(factor.category);
      if (!acc[categoryKey]) {
        acc[categoryKey] = [];
      }
      acc[categoryKey].push(factor);
      return acc;
    }, {} as Record<string, ModalFactor[]>);

    return Object.keys(grouped)
      .sort(compareFactorCategoryOrder)
      .reduce((acc, key) => {
        acc[key] = grouped[key];
        return acc;
      }, {} as Record<string, ModalFactor[]>);
  }, [factors]);

  const categoryKeys = useMemo(
    () => Object.keys(factorsByCategory),
    [factorsByCategory],
  );
  const defaultFactor = useMemo(() => factors[0] ?? null, [factors]);
  const defaultSubFactorId = useMemo(
    () => subFactors[0]?.id ?? "default",
    [subFactors],
  );

  // ===== 상태 관리 =====

  /** 검색어 입력 상태 */
  const [searchQuery, setSearchQuery] = useState("");

  /** 디바운스가 적용된 검색어 (250ms 지연) */
  const debouncedQuery = useDebounce(searchQuery, 250);
  const trimmedQuery = debouncedQuery.trim();

  /** 현재 선택된 팩터 */
  const [selectedFactor, setSelectedFactor] = useState<ModalFactor | null>(
    defaultFactor,
  );

  /** 현재 선택된 함수 ID (기본값: "default") */
  const [selectedSubFactorId, setSelectedSubFactorId] = useState(
    initialValues?.subFactorId || defaultSubFactorId,
  );

  /** 현재 선택된 부등호 (기본값: ">=") */
  const [selectedOperator, setSelectedOperator] = useState<
    ">=" | "<=" | ">" | "<" | "=" | "!="
  >(initialValues?.operator || ">=");

  /** 비교 값 (기본값: 0) */
  const [comparisonValue, setComparisonValue] = useState<number>(
    initialValues?.value ?? 0,
  );

  /** 확장된 카테고리 목록 */
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);

  // ===== body 스크롤 막기 =====
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const { body, documentElement } = document;
    const previousBodyOverflow = body.style.overflow;
    const previousHtmlOverflow = documentElement.style.overflow;

    body.style.overflow = "hidden";
    documentElement.style.overflow = "hidden";

    return () => {
      body.style.overflow = previousBodyOverflow;
      documentElement.style.overflow = previousHtmlOverflow;
    };
  }, [isOpen]);

  // ===== 검색 로직 및 자동 선택 =====

  const searchResults = useMemo(() => {
    if (trimmedQuery === "" || !factors.length) {
      return [];
    }

    const lowerQuery = trimmedQuery.toLowerCase();
    return factors.filter((factor) =>
      factor.name.toLowerCase().includes(lowerQuery),
    );
  }, [factors, trimmedQuery]);

  /**
   * 디바운스된 검색어가 변경될 때 자동으로 첫 번째 결과 선택
   */
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    if (trimmedQuery === "") {
      setExpandedCategories(categoryKeys);
      setSelectedFactor((prev) => prev ?? defaultFactor);
      return;
    }

    setExpandedCategories(["검색결과"]);

    if (searchResults.length > 0) {
      setSelectedFactor(searchResults[0]);
    } else {
      setSelectedFactor(null);
    }
  }, [
    categoryKeys,
    defaultFactor,
    isOpen,
    searchResults,
    trimmedQuery,
  ]);

  /**
   * 모달이 열릴 때 상태 초기화 또는 초기값 설정
   */
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setSearchQuery("");

    const factorFromInitial = initialValues?.factorId
      ? factors.find((f) => f.id === initialValues.factorId) || null
      : null;
    setSelectedFactor(factorFromInitial ?? defaultFactor);

    setSelectedSubFactorId(initialValues?.subFactorId || defaultSubFactorId);
    setSelectedOperator(initialValues?.operator || ">=");
    setComparisonValue(initialValues?.value ?? 0);

    // 모든 카테고리 확장
    setExpandedCategories(categoryKeys);
  }, [
    categoryKeys,
    defaultFactor,
    defaultSubFactorId,
    initialValues,
    isOpen,
    factors,
  ]);

  // ===== 이벤트 핸들러 =====

  /**
   * 팩터 선택 핸들러
   */
  const handleFactorSelect = (factor: ModalFactor) => {
    setSelectedFactor(factor);
  };

  /**
   * 함수 선택 핸들러
   */
  const handleSubFactorSelect = (subFactorId: string) => {
    setSelectedSubFactorId(subFactorId);
  };

  /**
   * "입력" 버튼 클릭 핸들러
   */
  const handleSubmit = () => {
    if (!selectedFactor) return;
    const resolvedSubFactorId =
      subFactors.find((sf) => sf.id === selectedSubFactorId)?.id ??
      defaultSubFactorId ??
      "default";

    onSelect(
      selectedFactor.id,
      selectedFactor.name,
      resolvedSubFactorId,
      selectedOperator,
      comparisonValue,
    );
    onClose();
  };

  /**
   * 카테고리 확장/축소 토글
   */
  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  // ===== 데이터 준비 =====

  /**
   * 표시할 팩터 목록
   */
  const displayFactors = useMemo(
    () =>
      trimmedQuery === ""
        ? factorsByCategory
        : { 검색결과: searchResults },
    [factorsByCategory, searchResults, trimmedQuery],
  );

  /** 선택된 함수 정보 */
  const selectedSubFactor =
    subFactors.find((sf) => sf.id === selectedSubFactorId) ??
    subFactors.find((sf) => sf.id === defaultSubFactorId);

  // ===== 렌더링 =====

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Background blur layer - 덜 어둡게 */}
      <div
        className="absolute inset-0 backdrop-blur-sm bg-[rgba(0,0,0,0.3)]"
        onClick={onClose}
      />

      {/* Modal - 뷰포트 비율 사용 (1920x1200 기준: 1000/1920 ≈ 52vw, 769/1200 ≈ 64vh) */}
      <div className="relative z-10 backdrop-blur-[50px] backdrop-filter bg-[rgba(255,255,255,0.2)] rounded-[8px] w-[min(52vw,1000px)] h-[min(64vh,769px)] max-h-[90vh]">
        <div className="h-full overflow-clip relative rounded-[inherit] flex flex-col">
          {/* Header */}
          <div className="relative h-[60px] flex-shrink-0">
            <button
              onClick={onClose}
              className="absolute right-[14px] top-1/2 -translate-y-1/2 cursor-pointer hover:opacity-80 transition-opacity z-10"
              type="button"
            >
              <CloseIcon />
            </button>
            <div className="absolute left-[14px] top-1/2 -translate-y-1/2">
              <StarIcon />
            </div>
            <div className="absolute flex flex-col font-['Pretendard',sans-serif] font-medium justify-center leading-[0] left-1/2 not-italic text-[20px] text-center text-nowrap text-white top-1/2 tracking-[-0.6px] -translate-x-1/2 -translate-y-1/2">
              <p className="leading-[normal] whitespace-pre">팩터 선택</p>
            </div>
            <div aria-hidden="true" className="absolute border-b border-white/50 inset-x-0 bottom-0 pointer-events-none" />
          </div>

          {/* Content - flexible height */}
          <div className="flex-1 flex gap-[13px] px-[28px] pt-[28px] pb-[20px] overflow-hidden">
            {/* Left Panel - Factors (513px relative to 1000px modal = 51.3%) */}
            <div className="bg-[rgba(0,0,0,0.2)] rounded-[8px] w-[51.3%] border border-white/80 flex flex-col">
              <div className="flex-shrink-0 px-[16px] pt-[16px] pb-[12px]">
                {/* Search */}
                <div className="flex items-center gap-[16px]">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="조건 검색"
                    className="flex-1 h-[36px] bg-transparent border-b border-text-muted text-white font-['Pretendard',sans-serif] font-medium text-[14px] tracking-[-0.42px] px-0 outline-none placeholder:text-text-muted"
                  />
                  <button
                    className="backdrop-blur-[50px] backdrop-filter bg-[rgba(255,255,255,0.2)] rounded-[8px] p-[8px] border-[0.5px] border-white shadow-[0px_0px_4px_1px_rgba(255,255,255,0.3)] hover:bg-[rgba(255,255,255,0.3)] transition-colors flex-shrink-0"
                    type="button"
                  >
                    <SearchIcon />
                  </button>
                </div>
              </div>

              {/* Content area */}
              <div className="flex-1 flex gap-[12px] px-[16px] pb-[16px] overflow-hidden min-h-0">
                {/* Factor List - 39% of panel width */}
                <div className="w-[43%] border border-white rounded-[8px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent p-[12px]">
                  {isLoadingFactors ? (
                    <div className="text-center text-sm text-tag-neutral py-[40px]">
                      팩터 데이터를 불러오는 중입니다...
                    </div>
                  ) : (
                    <>
                      {Object.entries(displayFactors).map(([category, factors], categoryIndex) => (
                        <div key={category} className="mb-[24px] last:mb-0">
                          {/* Category Header */}
                          <button
                            onClick={() => toggleCategory(category)}
                            className="flex flex-col font-['Pretendard',sans-serif] font-medium justify-center text-[18px] text-white tracking-[-0.54px] cursor-pointer hover:text-[#d68c45] transition-colors mb-[8px] w-full text-left"
                            type="button"
                          >
                            <p className="leading-[normal] whitespace-pre">{category}</p>
                          </button>

                          {/* Factor Items */}
                          {expandedCategories.includes(category) && (
                            <div className="space-y-[4px]">
                              {factors.map((factor) => (
                                <button
                                  key={factor.id}
                                  onClick={() => handleFactorSelect(factor)}
                                  className={`flex items-center text-[16px] tracking-[-0.48px] cursor-pointer transition-colors w-full text-left ${selectedFactor?.id === factor.id
                                    ? "text-[#d68c45] font-['Pretendard',sans-serif] font-bold"
                                    : "text-tag-neutral font-['Pretendard',sans-serif] font-normal hover:text-white"
                                    }`}
                                  type="button"
                                >
                                  <span className="mr-[8px]">•</span>
                                  <span className="leading-[normal]">{factor.name}</span>
                                </button>
                              ))}
                            </div>
                          )}

                          {/* Category Divider */}
                          {categoryIndex < Object.keys(displayFactors).length - 1 && (
                            <div className="mt-[16px] h-[1px]">
                              <svg className="block w-full h-full" fill="none" preserveAspectRatio="none" viewBox="0 0 200 1">
                                <line stroke="url(#paint0_linear_divider)" strokeOpacity="0.4" x2="200" y1="0.5" y2="0.5" />
                                <defs>
                                  <linearGradient gradientUnits="userSpaceOnUse" id="paint0_linear_divider" x1="0" x2="200" y1="1.5" y2="1.5">
                                    <stop stopColor="#282828" />
                                    <stop offset="0.2" stopColor="#737373" />
                                    <stop offset="0.8" stopColor="#737373" />
                                    <stop offset="1" stopColor="#282828" />
                                  </linearGradient>
                                </defs>
                              </svg>
                            </div>
                          )}
                        </div>
                      ))}

                      {/* 검색 결과 없음 */}
                      {trimmedQuery !== "" &&
                        Object.values(displayFactors).every((factors) => factors.length === 0) && (
                          <div className="text-center text-sm text-tag-neutral py-[40px]">
                            검색 결과가 없습니다
                          </div>
                        )}

                      {/* 전체 데이터 없음 */}
                      {trimmedQuery === "" && categoryKeys.length === 0 && (
                        <div className="text-center text-sm text-tag-neutral py-[40px]">
                          사용할 수 있는 팩터가 없습니다
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* Factor Info Panel - 61% of panel width */}
                <div className="flex-1 border border-white rounded-[8px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent p-[12px]">
                  {isLoadingFactors ? (
                    <div className="flex h-full items-center justify-center text-sm text-tag-neutral">
                      팩터 정보를 불러오는 중입니다...
                    </div>
                  ) : selectedFactor ? (
                    <>
                      <div className="flex flex-col font-['Pretendard',sans-serif] font-bold justify-center text-[18px] tracking-[-0.54px] mb-[18.5px]">
                        <p className="leading-[normal] text-white whitespace-pre">{selectedFactor.name}</p>
                      </div>
                      <div className="font-['Pretendard',sans-serif] font-normal leading-[normal] text-[16px] tracking-[-0.48px] whitespace-pre-wrap text-white">
                        <p>{selectedFactor.description ?? selectedFactor.formula ?? "설명이 제공되지 않았습니다."}</p>
                      </div>
                    </>
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-tag-neutral">
                      팩터를 선택해주세요
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Panel - Functions (421px relative to 1000px = 42.1%) */}
            <div className="bg-[rgba(0,0,0,0.2)] rounded-[8px] flex-1 border border-white/80 flex flex-col">
              <div className="flex-1 flex gap-[12px] p-[12px] overflow-hidden min-h-0">
                {/* Function List - 33% of panel */}
                <div className="w-[33%] border border-white rounded-[8px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent p-[12px]">
                  <div className="flex flex-col font-['Pretendard',sans-serif] font-medium justify-center text-[18px] text-white tracking-[-0.54px] mb-[16px]">
                    <p className="leading-[normal]">함수 목록</p>
                  </div>

                  {/* Function Items */}
                  {isLoadingSubFactors ? (
                    <div className="text-center text-sm text-tag-neutral py-[40px]">
                      함수 데이터를 불러오는 중입니다...
                    </div>
                  ) : subFactors.length === 0 ? (
                    <div className="text-center text-sm text-tag-neutral py-[40px]">
                      사용할 수 있는 함수가 없습니다
                    </div>
                  ) : (
                    <div className="space-y-[4px]">
                      {subFactors.map((func) => (
                        <button
                          key={func.id}
                          onClick={() => handleSubFactorSelect(func.id)}
                          className={`flex items-center text-[16px] tracking-[-0.48px] cursor-pointer transition-colors w-full text-left ${selectedSubFactorId === func.id
                            ? "text-white font-['Pretendard',sans-serif] font-bold"
                            : "text-tag-neutral font-['Pretendard',sans-serif] font-normal hover:text-white"
                            }`}
                          type="button"
                        >
                          <span className="mr-[8px]">•</span>
                          <span className="leading-[normal]">{func.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Function Info Panel - 67% of panel */}
                <div className="flex-1 border border-white rounded-[8px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent p-[12px]">
                  {isLoadingSubFactors ? (
                    <div className="flex h-full items-center justify-center text-sm text-tag-neutral">
                      함수 정보를 불러오는 중입니다...
                    </div>
                  ) : selectedSubFactor ? (
                    <>
                      <div className="flex flex-col font-['Pretendard',sans-serif] font-bold justify-center text-[18px] tracking-[-0.54px] mb-[18.5px]">
                        <p className="leading-[normal] text-white whitespace-pre">{selectedSubFactor.name}</p>
                      </div>
                      <div className="font-['Pretendard',sans-serif] font-normal leading-[normal] text-[16px] tracking-[-0.48px] text-white">
                        <p>{selectedSubFactor.description ?? "설명이 제공되지 않았습니다."}</p>
                      </div>
                    </>
                  ) : (
                    <div className="flex h-full items-center justify-center text-sm text-tag-neutral">
                      함수를 선택해주세요
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          {/* Submit Button */}
          <div className="flex-shrink-0 pb-[20px] flex justify-center">
            <button
              onClick={handleSubmit}
              disabled={!selectedFactor}
              className="backdrop-blur-[50px] backdrop-filter bg-[rgba(255,255,255,0.2)] rounded-[8px] border border-white shadow-[0px_0px_8px_2px_rgba(255,255,255,0.3)] px-[24px] py-[8px] cursor-pointer hover:bg-[rgba(255,255,255,0.3)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              type="button"
            >
              <div className="flex flex-col font-['Pretendard',sans-serif] font-medium justify-center leading-[0] not-italic text-[20px] text-center text-nowrap text-white tracking-[-0.6px]">
                <p className="leading-[normal] whitespace-pre">입력</p>
              </div>
            </button>
          </div>
        </div>
        <div aria-hidden="true" className="absolute border-[0.5px] border-solid border-white inset-0 pointer-events-none rounded-[8px] shadow-[0px_0px_8px_2px_rgba(255,255,255,0.3)]" />
      </div>
    </div>
  );
}
