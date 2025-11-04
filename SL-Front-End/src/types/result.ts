/** 백테스트 지표 항목 타입 */
export interface BacktestMetric {
  /** 지표 그룹 이름 */
  group: string;
  /** 지표 라벨 */
  label: string;
  /** 지표 값 */
  value: string;
  /** 지표 색상 키워드 */
  tone?: "positive" | "negative" | "neutral";
}

/** 백테스트 성과 바 차트 데이터 타입 */
export interface BacktestYieldPoint {
  /** 라벨 */
  label: string;
  /** 수익률 값(%) */
  value: number;
}

/** 백테스트 매매 종목 테이블 행 타입 */
export interface BacktestTradeRow {
  /** 종목명 */
  name: string;
  /** 거래 단가 */
  price: string;
  /** 수익 */
  profit: string;
  /** 수익률 */
  profitRate: string;
  /** 매수 일자 */
  buyDate: string;
  /** 매도 일자 */
  sellDate: string;
  /** 보유 비중 */
  weight: string;
  /** 평가 금액 */
  valuation: string;
}
