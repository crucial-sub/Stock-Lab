/**
 * SSE (Server-Sent Events) 프로토콜 타입 정의
 *
 * AI 어시스턴트 채팅 스트리밍을 위한 SSE 이벤트 타입
 * 참조: AI_assistant_feature_spec.md 섹션 3.1
 */

/**
 * SSE 이벤트 타입
 * - stream_start: 스트리밍 시작 신호
 * - stream_chunk: 실시간 콘텐츠 청크
 * - stream_end: 스트리밍 종료 신호
 * - ui_language: 구조화된 UI 데이터 (설문, 전략 추천, 백테스트 결과 등)
 * - backtest_progress: 백테스트 진행 상황 (10%마다 전송)
 * - backtest_complete: 백테스트 완료 및 최종 결과
 * - error: 에러 발생
 */
export type SSEEventType =
  | "stream_start"
  | "stream_chunk"
  | "stream_end"
  | "ui_language"
  | "backtest_progress"
  | "backtest_complete"
  | "error";

/**
 * 기본 SSE 이벤트 인터페이스
 */
export interface SSEEvent {
  /** 이벤트 타입 */
  type: SSEEventType;
  /** 메시지 ID (스트리밍 세션 식별) */
  messageId?: string;
}

/**
 * 스트리밍 시작 이벤트
 */
export interface SSEStreamStartEvent extends SSEEvent {
  type: "stream_start";
  messageId: string;
  /** 스트리밍 시작 시각 (타임스탬프) */
  timestamp?: number;
}

/**
 * 스트리밍 청크 이벤트
 * - 실시간으로 전송되는 텍스트 조각
 * - 마크다운 형식 지원
 */
export interface SSEStreamChunkEvent extends SSEEvent {
  type: "stream_chunk";
  /** 청크 콘텐츠 (마크다운 형식) */
  content: string;
  /** 콘텐츠 형식 (기본값: "markdown") */
  format?: "markdown" | "text";
}

/**
 * 스트리밍 종료 이벤트
 */
export interface SSEStreamEndEvent extends SSEEvent {
  type: "stream_end";
  /** 스트리밍 종료 시각 (타임스탬프) */
  timestamp?: number;
  /** 완료된 전체 콘텐츠 (선택사항) */
  fullContent?: string;
}

/**
 * UI Language 이벤트
 * - 설문 질문, 전략 추천, 백테스트 결과 등 구조화된 UI 데이터
 */
export interface SSEUILanguageEvent extends SSEEvent {
  type: "ui_language";
  /** UI Language 데이터 (JSON 형식) */
  data: any; // ui-language.ts의 UILanguage 타입 참조
}

/**
 * 에러 이벤트
 */
export interface SSEErrorEvent extends SSEEvent {
  type: "error";
  /** 에러 메시지 */
  message: string;
  /** 에러 코드 (HTTP 상태 코드 또는 커스텀 코드) */
  code?: string | number;
  /** 에러 상세 정보 */
  details?: any;
}

/**
 * 백테스트 수익률 데이터 포인트
 */
export interface YieldPoint {
  /** 날짜 (ISO 8601 형식, e.g., "2024-01-15T00:00:00Z") */
  date: string;
  /** 누적 수익률 (%) */
  cumulativeReturn: number;
  /** 매수 횟수 */
  buyCount: number;
  /** 매도 횟수 */
  sellCount: number;
}

/**
 * 백테스트 진행 상황 이벤트 (10%마다 전송)
 */
export interface SSEBacktestProgressEvent extends SSEEvent {
  type: "backtest_progress";
  data: {
    /** 진행률 (0, 10, 20, ..., 100) */
    progress: number;

    /** 증분 데이터 (이번 10% 구간의 새 데이터) */
    incremental: {
      /** 수익률 데이터 포인트 배열 */
      yieldPoints: YieldPoint[];
    };

    /** 누적 통계 (체크포인트) */
    cumulative: {
      /** 현재 누적 수익률 (%) */
      currentReturn: number;
      /** 경과 시간 (밀리초) */
      elapsedTime: number;
      /** 예상 남은 시간 (밀리초) */
      estimatedRemainingTime: number;
    };
  };
}

/**
 * 백테스트 통계 데이터
 */
export interface BacktestStatistics {
  /** 총 수익률 (%) */
  totalReturn: number;
  /** 연환산 수익률 CAGR (%) */
  annualizedReturn: number;
  /** 최대 낙폭 MDD (%) */
  maxDrawdown: number;
  /** 샤프 비율 */
  sharpeRatio: number;
  /** 승률 (%) */
  winRate: number;
  /** 일 평균 수익률 (%) */
  dailyAvgReturn?: number;
  /** 투자 원금 */
  initialCapital: number;
  /** 총 손익 */
  totalProfit: number;
  /** 현재 총 자산 */
  currentAssets: number;
}

/**
 * 기간별 수익률 데이터
 */
export interface PeriodReturn {
  /** 기간 레이블 (예: "1M", "3M", "6M", "1Y") */
  label: string;
  /** 수익률 (%) */
  value: number;
}

/**
 * 백테스트 완료 이벤트
 */
export interface SSEBacktestCompleteEvent extends SSEEvent {
  type: "backtest_complete";
  data: {
    /** 백테스트 ID */
    backtestId: string;

    /** 최종 통계 */
    statistics: BacktestStatistics;

    /** 전체 수익률 데이터 (결과 UI용) */
    allYieldPoints: YieldPoint[];

    /** 기간별 수익률 (StatisticsSection용) */
    periodReturns: PeriodReturn[];

    /** 연도별 수익률 데이터 */
    yearlyReturns?: Array<{
      year: number;
      return: number;
    }>;

    /** 월별 수익률 데이터 */
    monthlyReturns?: Array<{
      month: string; // "2024-01"
      return: number;
    }>;

    /** 종목별 수익률 데이터 */
    stockWiseReturns?: Array<{
      stockName: string;
      return: number;
      weight: number;
    }>;

    /** 총 자산 데이터 */
    totalAssetsData?: Array<{
      date: string;
      assets: number;
    }>;

    /** 마크다운 요약 */
    summary: string;
  };
}

/**
 * 모든 SSE 이벤트의 유니온 타입
 */
export type SSEEventUnion =
  | SSEStreamStartEvent
  | SSEStreamChunkEvent
  | SSEStreamEndEvent
  | SSEUILanguageEvent
  | SSEBacktestProgressEvent
  | SSEBacktestCompleteEvent
  | SSEErrorEvent;

/**
 * SSE 연결 상태
 */
export type SSEConnectionState =
  | "idle" // 연결 전 또는 종료됨
  | "connecting" // 연결 시도 중
  | "connected" // 연결 성공
  | "streaming" // 스트리밍 진행 중
  | "complete" // 스트리밍 완료
  | "error" // 에러 발생
  | "reconnecting"; // 재연결 시도 중

/**
 * SSE 연결 설정 옵션
 */
export interface SSEConnectionOptions {
  /** 자동 재연결 활성화 (기본값: true) */
  autoReconnect?: boolean;
  /** 최대 재연결 시도 횟수 (기본값: 3) */
  maxReconnectAttempts?: number;
  /** 재연결 간격 (밀리초, 기본값: 1000) */
  reconnectInterval?: number;
  /** 타임아웃 시간 (밀리초, 기본값: 60000 = 60초) */
  timeout?: number;
}

/**
 * SSE 연결 에러 타입
 */
export interface SSEConnectionError extends Error {
  /** 에러 코드 */
  code?: string | number;
  /** 재연결 가능 여부 */
  retryable?: boolean;
}
