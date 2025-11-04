/**
 * 팩터 선택 모달에서 사용할 함수 목록
 * factor-select.png 디자인 시안 기반
 * 현재는 모든 함수가 "기본"과 동일하게 동작
 */

export interface SubFactor {
  id: string;
  name: string;
  description?: string;
}

/**
 * 함수 목록
 * 디자인 시안의 "함수 목록" 섹션에 표시되는 항목들
 */
export const SUB_FACTORS: SubFactor[] = [
  {
    id: "default",
    name: "기본",
    description: "팩터 값을 그대로 사용",
  },
  {
    id: "percentile",
    name: "과거값",
    description: "과거 데이터와 비교",
  },
  {
    id: "moving_avg",
    name: "이동평균",
    description: "일정 기간의 평균값",
  },
  {
    id: "ratio",
    name: "비율",
    description: "기준값 대비 비율",
  },
  {
    id: "rank",
    name: "순위",
    description: "전체 종목 중 순위",
  },
  {
    id: "max",
    name: "최고값",
    description: "기간 내 최고값",
  },
  {
    id: "min",
    name: "최저값",
    description: "기간 내 최저값",
  },
  {
    id: "variation_period",
    name: "변화량_기간",
    description: "기간별 변화량",
  },
  {
    id: "variation_rate_period",
    name: "변화율_기간",
    description: "기간별 변화율",
  },
];

/**
 * 함수 ID로 함수 찾기
 */
export function getSubFactorById(id: string): SubFactor | undefined {
  return SUB_FACTORS.find((fn) => fn.id === id);
}

/**
 * 기본 함수 반환
 */
export function getDefaultSubFactor(): SubFactor {
  return SUB_FACTORS[0]; // "기본"
}
