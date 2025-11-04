/**
 * 팩터 선택 모달에서 사용할 팩터 데이터 구조
 * 각 팩터는 카테고리별로 분류되며, 이름과 계산 공식을 포함
 */

export interface Factor {
  id: string;
  name: string;
  formula: string;
  category: FactorCategory;
}

export type FactorCategory = "가치" | "퀄리티" | "성장" | "모멘텀" | "규모";

/**
 * 카테고리별 팩터 목록
 * factor-list.png 디자인 시안을 기반으로 정의
 */
export const FACTORS: Factor[] = [
  // 가치 (Value)
  {
    id: "per",
    name: "주가 수익률 (PER)",
    formula: "주가 / 주당순이익(EPS)",
    category: "가치",
  },
  {
    id: "pbr",
    name: "주가순자산률 (PBR)",
    formula: "주가 / ((총자산 - 총부채) / 발행주식수)",
    category: "가치",
  },
  {
    id: "psr",
    name: "주가매출비율 (PSR)",
    formula: "시가 총액 / 매출액",
    category: "가치",
  },
  {
    id: "pcr",
    name: "주가현금흐름비율 (PCR)",
    formula: "주가 / 주당현금흐름 = 시가총액 / 영업활동현금흐름",
    category: "가치",
  },
  {
    id: "dividend_yield",
    name: "배당수익률",
    formula: "(배당금총액 / 발행주식수) / 전일종가 * 100",
    category: "가치",
  },

  // 퀄리티 (Quality)
  {
    id: "roe",
    name: "ROE (자기자본이익률)",
    formula: "당기순이익 / 자본총계",
    category: "퀄리티",
  },
  {
    id: "roa",
    name: "ROA (총자산이익률)",
    formula: "당기순이익 / 자산총계",
    category: "퀄리티",
  },
  {
    id: "operating_margin",
    name: "영업이익률",
    formula: "(매출액 - 매출원가) / 매출액 * 100",
    category: "퀄리티",
  },
  {
    id: "debt_ratio",
    name: "부채비율",
    formula: "부채총계 / 자본총계",
    category: "퀄리티",
  },
  {
    id: "current_ratio",
    name: "유동비율",
    formula: "유동자산 / 유동부채",
    category: "퀄리티",
  },

  // 성장 (Growth)
  {
    id: "revenue_growth",
    name: "매출액증가율",
    formula: "(당기매출액 - 전기매출액) / 전기매출액",
    category: "성장",
  },
  {
    id: "operating_income_growth",
    name: "영업이익증가율",
    formula: "(당기영업이익 - 전기영업이익) / 전기영업이익",
    category: "성장",
  },
  {
    id: "eps_growth",
    name: "EPS증가율",
    formula: "(당기EPS - 전기EPS) / 전기EPS",
    category: "성장",
  },
  {
    id: "asset_growth",
    name: "자산증가율",
    formula: "(당기총자산 - 전기총자산) / 전기총자산",
    category: "성장",
  },

  // 모멘텀 (Momentum)
  {
    id: "return_3m",
    name: "3개월 수익률",
    formula: "(현재가 - 3개월전 종가) / 3개월전 종가",
    category: "모멘텀",
  },
  {
    id: "return_12m",
    name: "12개월 수익률",
    formula: "(현재가 - 12개월전 종가) / 12개월전 종가",
    category: "모멘텀",
  },
  {
    id: "volume",
    name: "거래량",
    formula: "최근 20일 평균 거래량",
    category: "모멘텀",
  },
  {
    id: "trading_value",
    name: "거래대금",
    formula: "최근 20일 평균 거래대금",
    category: "모멘텀",
  },
  {
    id: "high_52w_ratio",
    name: "52주 최고가 대비",
    formula: "현재가 / 52주 최고가",
    category: "모멘텀",
  },

  // 규모 (Size)
  {
    id: "market_cap",
    name: "시가총액",
    formula: "시가총액",
    category: "규모",
  },
  {
    id: "revenue",
    name: "매출액",
    formula: "매출액",
    category: "규모",
  },
  {
    id: "total_assets",
    name: "총자산",
    formula: "자산총계",
    category: "규모",
  },
];

/**
 * 카테고리 순서 정의
 */
export const CATEGORY_ORDER: FactorCategory[] = [
  "가치",
  "퀄리티",
  "성장",
  "모멘텀",
  "규모",
];

/**
 * 카테고리별로 팩터를 그룹화하는 헬퍼 함수
 */
export function getFactorsByCategory(): Record<FactorCategory, Factor[]> {
  return FACTORS.reduce(
    (acc, factor) => {
      if (!acc[factor.category]) {
        acc[factor.category] = [];
      }
      acc[factor.category].push(factor);
      return acc;
    },
    {} as Record<FactorCategory, Factor[]>,
  );
}

/**
 * 팩터 ID로 팩터 찾기
 */
export function getFactorById(id: string): Factor | undefined {
  return FACTORS.find((factor) => factor.id === id);
}

/**
 * 검색어로 팩터 필터링
 * 팩터 이름에 검색어가 포함되는지 확인
 */
export function searchFactors(query: string): Factor[] {
  if (!query.trim()) {
    return FACTORS;
  }

  const lowerQuery = query.toLowerCase();
  return FACTORS.filter((factor) =>
    factor.name.toLowerCase().includes(lowerQuery),
  );
}
