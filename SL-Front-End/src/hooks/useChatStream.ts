/**
 * useChatStream 커스텀 훅
 *
 * EventSource API를 사용하여 SSE 기반 채팅 스트리밍을 처리합니다.
 * - 자동 재연결 로직 (연결 끊김 시 3회 재시도)
 * - 에러 처리 및 타임아웃 (60초)
 * - 스트리밍 상태 관리
 *
 * 참조: AI_assistant_feature_spec.md 섹션 3.1
 */

"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/**
 * SSE 이벤트 타입 정의
 */
type SSEEventUnion =
  | { type: "stream_start"; messageId: string }
  | { type: "stream_chunk"; content: string }
  | { type: "stream_end" }
  | { type: "ui_language"; data: any }
  | { type: "error"; message: string; code?: string };

/**
 * SSE 연결 상태
 */
type SSEConnectionState =
  | "idle"
  | "connecting"
  | "connected"
  | "streaming"
  | "complete"
  | "error"
  | "reconnecting";

/**
 * SSE 연결 옵션
 */
interface SSEConnectionOptions {
  /** 자동 재연결 여부 */
  autoReconnect?: boolean;
  /** 최대 재연결 시도 횟수 */
  maxReconnectAttempts?: number;
  /** 재연결 간격 (ms) */
  reconnectInterval?: number;
  /** 타임아웃 (ms) */
  timeout?: number;
}

/**
 * SSE 연결 에러
 */
interface SSEConnectionError extends Error {
  code?: string;
  retryable?: boolean;
}

/**
 * useChatStream 반환 타입
 */
interface UseChatStreamReturn {
  /** 누적된 응답 내용 (마크다운 형식) */
  content: string;
  /** 스트리밍 진행 중 여부 */
  isStreaming: boolean;
  /** 연결 상태 */
  connectionState: SSEConnectionState;
  /** 에러 객체 */
  error: Error | null;
  /** 메시지 전송 함수 */
  sendMessage: (message: string) => void;
  /** 스트리밍 중단 함수 */
  abort: () => void;
  /** 재시도 함수 (에러 발생 시 수동 재시도) */
  retry: () => void;
}

/**
 * SSE 기반 채팅 스트리밍 커스텀 훅
 *
 * @param sessionId - 현재 채팅 세션 ID
 * @param options - SSE 연결 설정 옵션
 * @returns 스트리밍 상태 및 제어 함수
 *
 * @example
 * ```tsx
 * function ChatComponent() {
 *   const { content, isStreaming, sendMessage, error } = useChatStream("session_123");
 *
 *   return (
 *     <div>
 *       <div>{content}</div>
 *       {isStreaming && <span>▌</span>}
 *       {error && <p>에러: {error.message}</p>}
 *       <button onClick={() => sendMessage("안녕하세요")}>전송</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useChatStream(
  sessionId: string,
  options: SSEConnectionOptions = {}
): UseChatStreamReturn {
  // 기본 옵션 설정
  const {
    autoReconnect = true,
    maxReconnectAttempts = 3,
    reconnectInterval = 1000,
    timeout = 60000, // 60초
  } = options;

  // 상태 관리
  const [content, setContent] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [connectionState, setConnectionState] =
    useState<SSEConnectionState>("idle");
  const [error, setError] = useState<Error | null>(null);

  // Ref로 관리하는 값들 (리렌더링 방지)
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectCountRef = useRef<number>(0);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessageRef = useRef<string>("");

  /**
   * EventSource 연결 종료
   */
  const closeConnection = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }

    setIsStreaming(false);
  }, []);

  /**
   * 에러 처리 함수
   */
  const handleError = useCallback(
    (err: Error | SSEConnectionError, retryable = true) => {
      console.error("[useChatStream] 에러 발생:", err);
      setError(err);
      setConnectionState("error");
      closeConnection();

      // 자동 재연결 로직
      if (
        autoReconnect &&
        retryable &&
        reconnectCountRef.current < maxReconnectAttempts
      ) {
        reconnectCountRef.current += 1;
        setConnectionState("reconnecting");

        setTimeout(() => {
          if (currentMessageRef.current) {
            sendMessage(currentMessageRef.current);
          }
        }, reconnectInterval * reconnectCountRef.current); // 지수 백오프
      }
    },
    [
      autoReconnect,
      maxReconnectAttempts,
      reconnectInterval,
      closeConnection,
    ]
  );

  /**
   * SSE 이벤트 처리 함수
   */
  const handleSSEEvent = useCallback(
    (event: MessageEvent) => {
      try {
        const data: SSEEventUnion = JSON.parse(event.data);

        switch (data.type) {
          case "stream_start":
            setContent("");
            setIsStreaming(true);
            setConnectionState("streaming");
            reconnectCountRef.current = 0; // 성공 시 재연결 카운트 리셋
            break;

          case "stream_chunk":
            // 즉시 렌더링 (인위적 딜레이 없음)
            setContent((prev) => prev + data.content);
            break;

          case "stream_end":
            setIsStreaming(false);
            setConnectionState("complete");
            closeConnection();
            break;

          case "ui_language":
            // UI Language 데이터는 별도 처리 필요 (상위 컴포넌트에서 처리)
            break;

          case "error":
            const sseError = new Error(data.message) as SSEConnectionError;
            sseError.code = data.code;
            sseError.retryable = false; // SSE 에러는 일반적으로 재시도 불가
            handleError(sseError, false);
            break;

          default:
            console.warn("[useChatStream] 알 수 없는 이벤트 타입:", data);
        }
      } catch (parseError) {
        console.error("[useChatStream] JSON 파싱 에러:", parseError);
        handleError(
          new Error("서버 응답을 파싱하는 중 오류가 발생했습니다."),
          false
        );
      }
    },
    [handleError, closeConnection]
  );

  /**
   * 메시지 전송 함수
   */
  const sendMessage = useCallback(
    (message: string) => {
      // 기존 연결 정리
      closeConnection();

      // 초기화
      setError(null);
      setContent("");
      setConnectionState("connecting");
      currentMessageRef.current = message;

      // SSE 엔드포인트 URL 생성
      const baseUrl = process.env.NEXT_PUBLIC_CHATBOT_API_URL ||
                      process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api/v1', '') ||
                      window.location.origin.replace(':3000', ':8003');
      const url = new URL("/api/v1/chat/stream", baseUrl);
      url.searchParams.set("sessionId", sessionId);
      url.searchParams.set("message", message);
      url.searchParams.set("clientType", "assistant");

      try {
        // EventSource 생성
        const eventSource = new EventSource(url.toString());
        eventSourceRef.current = eventSource;

        // 연결 성공
        eventSource.onopen = () => {
          setConnectionState("connected");
        };

        // 메시지 수신
        eventSource.onmessage = handleSSEEvent;

        // 에러 처리
        eventSource.onerror = (event) => {
          console.error("[useChatStream] SSE 연결 에러:", event);
          const connectionError = new Error(
            "네트워크 연결이 불안정합니다. 인터넷 연결을 확인하고 다시 시도해주세요."
          ) as SSEConnectionError;
          connectionError.retryable = true;
          handleError(connectionError);
        };

        // 타임아웃 설정
        timeoutIdRef.current = setTimeout(() => {
          console.error("[useChatStream] 타임아웃 발생");
          handleError(
            new Error(
              `AI 응답 시간이 초과되었습니다 (${timeout / 1000}초). 질문이 복잡하거나 서버가 바쁠 수 있습니다. 잠시 후 다시 시도해주세요.`
            ),
            false
          );
        }, timeout);
      } catch (err) {
        console.error("[useChatStream] EventSource 생성 에러:", err);
        handleError(
          new Error(
            "서버와 연결할 수 없습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요."
          ),
          false
        );
      }
    },
    [sessionId, timeout, handleSSEEvent, handleError, closeConnection]
  );

  /**
   * 스트리밍 중단 함수
   */
  const abort = useCallback(() => {
    closeConnection();
    setConnectionState("idle");
  }, [closeConnection]);

  /**
   * 재시도 함수 (수동)
   */
  const retry = useCallback(() => {
    if (currentMessageRef.current) {
      reconnectCountRef.current = 0;
      sendMessage(currentMessageRef.current);
    }
  }, [sendMessage]);

  /**
   * 컴포넌트 언마운트 시 정리
   */
  useEffect(() => {
    return () => {
      closeConnection();
    };
  }, [closeConnection]);

  return {
    content,
    isStreaming,
    connectionState,
    error,
    sendMessage,
    abort,
    retry,
  };
}
