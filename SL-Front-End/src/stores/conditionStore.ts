import { create } from "zustand";

/**
 * 조건식 데이터 구조
 * 각 조건식은 팩터, 함수, 부등호, 값을 포함
 */
export interface Condition {
  id: string; // 조건 ID (A, B, C, ...)
  factorId: string | null; // 선택된 팩터 ID
  factorName: string | null; // 선택된 팩터 이름
  subFactorId: string; // 선택된 함수 ID (기본값: "default")
  operator: ">=" | "<=" | ">" | "<" | "=" | "!="; // 부등호
  value: number; // 비교 값
}

/**
 * 조건식 스토어 상태
 */
interface ConditionStore {
  // 매수 조건 목록
  buyConditions: Condition[];

  // 매도 조건 목록
  sellConditions: Condition[];

  // 매수 조건 업데이트
  updateBuyCondition: (id: string, updates: Partial<Condition>) => void;

  // 매도 조건 업데이트
  updateSellCondition: (id: string, updates: Partial<Condition>) => void;

  // 매수 조건 추가
  addBuyCondition: () => void;

  // 매도 조건 추가
  addSellCondition: () => void;

  // 매수 조건 삭제
  removeBuyCondition: (id: string) => void;

  // 매도 조건 삭제
  removeSellCondition: (id: string) => void;

  // 조건식 문자열 생성
  getConditionExpression: (condition: Condition) => string;

  // 모든 조건 초기화
  reset: () => void;
}

/**
 * 기본 조건식 생성
 */
const createDefaultCondition = (id: string): Condition => ({
  id,
  factorId: null,
  factorName: null,
  subFactorId: "default",
  operator: ">=",
  value: 0,
});

/**
 * 조건식 문자열 생성 함수
 * "{팩터 이름} {부등호} {값}" 형식으로 반환
 *
 * 부등호 표시를 더 명확하게 하기 위해 공백 추가 및 유니코드 심볼 사용
 */
const generateExpression = (condition: Condition): string => {
  if (!condition.factorName) {
    return "조건식이 표시됩니다.";
  }

  // 부등호를 더 명확한 유니코드 심볼로 변환
  const operatorSymbol: Record<typeof condition.operator, string> = {
    ">=": "≥",
    "<=": "≤",
    ">": ">",
    "<": "<",
    "=": "=",
    "!=": "≠",
  };

  return `${condition.factorName} ${operatorSymbol[condition.operator]} ${condition.value}`;
};

/**
 * 조건식 전역 상태 관리 스토어
 *
 * 매수/매도 조건을 관리하며, 조건식 추가/수정/삭제 기능을 제공한다.
 * Zustand를 사용하여 전역 상태로 관리되므로 컴포넌트 간 공유가 용이하다.
 */
export const useConditionStore = create<ConditionStore>((set, get) => ({
  // 초기 매수 조건 (A)
  buyConditions: [createDefaultCondition("A")],

  // 초기 매도 조건 (빈 배열)
  sellConditions: [],

  /**
   * 매수 조건 업데이트
   */
  updateBuyCondition: (id, updates) =>
    set((state) => ({
      buyConditions: state.buyConditions.map((condition) =>
        condition.id === id ? { ...condition, ...updates } : condition,
      ),
    })),

  /**
   * 매도 조건 업데이트
   */
  updateSellCondition: (id, updates) =>
    set((state) => ({
      sellConditions: state.sellConditions.map((condition) =>
        condition.id === id ? { ...condition, ...updates } : condition,
      ),
    })),

  /**
   * 매수 조건 추가
   * 새 조건의 ID는 알파벳 순서로 자동 생성 (A, B, C, ...)
   */
  addBuyCondition: () =>
    set((state) => {
      const nextId = String.fromCharCode(
        65 + state.buyConditions.length, // 65 = 'A'
      );
      return {
        buyConditions: [...state.buyConditions, createDefaultCondition(nextId)],
      };
    }),

  /**
   * 매도 조건 추가
   */
  addSellCondition: () =>
    set((state) => {
      const nextId = String.fromCharCode(65 + state.sellConditions.length);
      return {
        sellConditions: [
          ...state.sellConditions,
          createDefaultCondition(nextId),
        ],
      };
    }),

  /**
   * 매수 조건 삭제
   */
  removeBuyCondition: (id) =>
    set((state) => ({
      buyConditions: state.buyConditions.filter(
        (condition) => condition.id !== id,
      ),
    })),

  /**
   * 매도 조건 삭제
   */
  removeSellCondition: (id) =>
    set((state) => ({
      sellConditions: state.sellConditions.filter(
        (condition) => condition.id !== id,
      ),
    })),

  /**
   * 조건식 문자열 반환
   */
  getConditionExpression: (condition) => generateExpression(condition),

  /**
   * 모든 조건 초기화
   */
  reset: () =>
    set({
      buyConditions: [createDefaultCondition("A")],
      sellConditions: [],
    }),
}));
