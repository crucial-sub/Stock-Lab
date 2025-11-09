/**
 * 팩터 카테고리 표시 정보
 * - 백엔드 카테고리 슬러그를 한글 라벨로 매핑
 * - 모달에서 노출 순서를 제어
 */

export const FACTOR_CATEGORY_LABELS: Record<string, string> = {
  value: "가치",
  quality: "퀄리티",
  profitability: "수익성",
  growth: "성장",
  momentum: "모멘텀",
  size: "규모",
  stability: "안정성",
  risk: "리스크",
  liquidity: "유동성",
  technical: "기술적",
};

export const FACTOR_CATEGORY_DISPLAY_ORDER = [
  "가치",
  "퀄리티",
  "수익성",
  "성장",
  "모멘텀",
  "규모",
  "안정성",
  "리스크",
  "유동성",
  "기술적",
] as const;

export const getFactorCategoryLabel = (category: string) =>
  FACTOR_CATEGORY_LABELS[category.toLowerCase()] ?? category;

export const compareFactorCategoryOrder = (a: string, b: string) => {
  const order = FACTOR_CATEGORY_DISPLAY_ORDER;
  const indexA = order.indexOf(a as (typeof order)[number]);
  const indexB = order.indexOf(b as (typeof order)[number]);

  if (indexA === -1 && indexB === -1) {
    return a.localeCompare(b);
  }
  if (indexA === -1) {
    return 1;
  }
  if (indexB === -1) {
    return -1;
  }
  return indexA - indexB;
};
