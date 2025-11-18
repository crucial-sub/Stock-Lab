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
 * - error: 에러 발생
 */
export type SSEEventType =
  | "stream_start"
  | "stream_chunk"
  | "stream_end"
  | "ui_language"
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
 * 모든 SSE 이벤트의 유니온 타입
 */
export type SSEEventUnion =
  | SSEStreamStartEvent
  | SSEStreamChunkEvent
  | SSEStreamEndEvent
  | SSEUILanguageEvent
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
