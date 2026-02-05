/**
 * useChatStream 커스텀 훅
 *
 * Fetch API + ReadableStream을 사용하여 SSE 기반 채팅 스트리밍을 처리합니다.
 * - EventSource 대신 Fetch API 사용으로 인증 헤더 지원
 * - AbortController를 통한 요청 중단 기능
 * - 지수 백오프 + Jitter 기반 자동 재연결
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
  /** 기본 재연결 간격 (ms) */
  reconnectInterval?: number;
  /** 최대 재연결 간격 (ms) */
  maxReconnectInterval?: number;
  /** 타임아웃 (ms) */
  timeout?: number;
  /** 인증 토큰 (선택) */
  authToken?: string;
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
 * SSE 라인 파서
 * - "data: {...}\n\n" 형식의 SSE 메시지를 파싱
 */
function parseSSELine(line: string): SSEEventUnion | null {
  // SSE 형식: "data: {...}"
  if (line.startsWith("data: ")) {
    const jsonStr = line.slice(6); // "data: " 제거
    if (jsonStr.trim() === "[DONE]") {
      return { type: "stream_end" };
    }
    try {
      return JSON.parse(jsonStr);
    } catch {
      console.warn("[useChatStream] JSON 파싱 실패:", jsonStr);
      return null;
    }
  }
  return null;
}

/**
 * 지수 백오프 + Jitter 계산
 * - 재시도 간격을 지수적으로 증가 (1초 → 2초 → 4초...)
 * - Jitter를 추가하여 동시 재접속으로 인한 서버 과부하 방지
 *
 * @param attempt - 현재 재시도 횟수 (1부터 시작)
 * @param baseInterval - 기본 재시도 간격 (ms)
 * @param maxInterval - 최대 재시도 간격 (ms)
 * @returns 실제 대기 시간 (ms)
 */
function calculateBackoffWithJitter(
  attempt: number,
  baseInterval: number,
  maxInterval: number
): number {
  // 지수 백오프: baseInterval * 2^(attempt-1)
  const exponentialDelay = baseInterval * Math.pow(2, attempt - 1);
  // 최대 간격 제한
  const cappedDelay = Math.min(exponentialDelay, maxInterval);
  // Jitter: 0 ~ 1초 랜덤 추가
  const jitter = Math.random() * 1000;
  return cappedDelay + jitter;
}

/**
 * Fetch API + ReadableStream 기반 SSE 채팅 스트리밍 커스텀 훅
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
    maxReconnectInterval = 30000,
    timeout = 120000,
    authToken,
  } = options;

  // 상태 관리
  const [content, setContent] = useState<string>("");
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [connectionState, setConnectionState] =
    useState<SSEConnectionState>("idle");
  const [error, setError] = useState<Error | null>(null);

  // Ref로 관리하는 값들 (리렌더링 방지)
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectCountRef = useRef<number>(0);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentMessageRef = useRef<string>("");

  /**
   * 연결 및 타이머 정리
   */
  const cleanup = useCallback(() => {
    // AbortController로 fetch 요청 중단
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    // 타임아웃 정리
    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current);
      timeoutIdRef.current = null;
    }

    // 재연결 타이머 정리
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setIsStreaming(false);
  }, []);

  /**
   * 에러 처리 및 자동 재연결
   */
  const handleError = useCallback(
    (err: Error | SSEConnectionError, retryable = true) => {
      console.error("[useChatStream] 에러 발생:", err);
      setError(err);
      setConnectionState("error");
      cleanup();

      // 자동 재연결 로직 (지수 백오프 + Jitter)
      if (
        autoReconnect &&
        retryable &&
        reconnectCountRef.current < maxReconnectAttempts
      ) {
        reconnectCountRef.current += 1;
        setConnectionState("reconnecting");

        // 지수 백오프 + Jitter 계산
        const delay = calculateBackoffWithJitter(
          reconnectCountRef.current,
          reconnectInterval,
          maxReconnectInterval
        );

        console.log(
          `[useChatStream] 재연결 시도 ${reconnectCountRef.current}/${maxReconnectAttempts}, 대기: ${Math.round(delay)}ms`
        );

        reconnectTimeoutRef.current = setTimeout(() => {
          if (currentMessageRef.current) {
            sendMessage(currentMessageRef.current);
          }
        }, delay);
      }
    },
    [
      autoReconnect,
      maxReconnectAttempts,
      reconnectInterval,
      maxReconnectInterval,
      cleanup,
    ]
  );

  /**
   * SSE 이벤트 처리
   */
  const handleSSEEvent = useCallback(
    (event: SSEEventUnion) => {
      switch (event.type) {
        case "stream_start":
          setContent("");
          setIsStreaming(true);
          setConnectionState("streaming");
          reconnectCountRef.current = 0; // 성공 시 재연결 카운트 리셋
          break;

        case "stream_chunk":
          setContent((prev) => prev + event.content);
          break;

        case "stream_end":
          setIsStreaming(false);
          setConnectionState("complete");
          cleanup();
          break;

        case "ui_language":
          // UI Language 데이터는 별도 처리 필요 (상위 컴포넌트에서 처리)
          break;

        case "error":
          const sseError = new Error(event.message) as SSEConnectionError;
          sseError.code = event.code;
          sseError.retryable = false;
          handleError(sseError, false);
          break;

        default:
          console.warn("[useChatStream] 알 수 없는 이벤트 타입:", event);
      }
    },
    [handleError, cleanup]
  );

  /**
   * ReadableStream을 통한 SSE 데이터 읽기
   */
  const readStream = useCallback(
    async (reader: ReadableStreamDefaultReader<Uint8Array>) => {
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // 스트림 종료
            if (connectionState === "streaming") {
              setIsStreaming(false);
              setConnectionState("complete");
            }
            break;
          }

          // 청크를 문자열로 디코딩하고 버퍼에 추가
          buffer += decoder.decode(value, { stream: true });

          // SSE 메시지는 "\n\n"으로 구분됨
          const messages = buffer.split("\n\n");
          // 마지막 불완전한 메시지는 버퍼에 유지
          buffer = messages.pop() || "";

          // 완전한 메시지들 처리
          for (const message of messages) {
            const lines = message.split("\n");
            for (const line of lines) {
              const event = parseSSELine(line);
              if (event) {
                handleSSEEvent(event);
              }
            }
          }
        }
      } catch (err) {
        // AbortError는 정상적인 중단이므로 무시
        if (err instanceof Error && err.name === "AbortError") {
          console.log("[useChatStream] 스트리밍 중단됨");
          return;
        }
        throw err;
      } finally {
        reader.releaseLock();
      }
    },
    [connectionState, handleSSEEvent]
  );

  /**
   * 메시지 전송 함수 (Fetch + ReadableStream 사용)
   */
  const sendMessage = useCallback(
    async (message: string) => {
      // 기존 연결 정리
      cleanup();

      // 초기화
      setError(null);
      setContent("");
      setConnectionState("connecting");
      currentMessageRef.current = message;

      // AbortController 생성 (요청 중단용)
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // SSE 엔드포인트 URL 생성
      const baseUrl =
        process.env.NEXT_PUBLIC_CHATBOT_API_URL ||
        process.env.NEXT_PUBLIC_API_BASE_URL?.replace("/api/v1", "") ||
        window.location.origin.replace(":3000", ":8003");
      const url = new URL("/api/v1/chat/stream", baseUrl);
      url.searchParams.set("sessionId", sessionId);
      url.searchParams.set("message", message);
      url.searchParams.set("clientType", "assistant");

      // 요청 헤더 구성 (인증 토큰 포함 가능)
      const headers: HeadersInit = {
        Accept: "text/event-stream",
        "Cache-Control": "no-cache",
      };

      // 인증 토큰이 있으면 Authorization 헤더 추가
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }

      try {
        // Fetch API로 SSE 스트림 요청
        const response = await fetch(url.toString(), {
          method: "GET",
          headers,
          signal: abortController.signal,
        });

        // 응답 상태 확인
        if (!response.ok) {
          throw new Error(
            `서버 응답 오류: ${response.status} ${response.statusText}`
          );
        }

        // 응답 본문이 없는 경우
        if (!response.body) {
          throw new Error("서버에서 스트림 응답을 받지 못했습니다.");
        }

        setConnectionState("connected");

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

        // ReadableStream을 통해 SSE 데이터 읽기
        const reader = response.body.getReader();
        await readStream(reader);
      } catch (err) {
        // AbortError는 정상적인 중단이므로 무시
        if (err instanceof Error && err.name === "AbortError") {
          console.log("[useChatStream] 요청이 중단되었습니다.");
          return;
        }

        console.error("[useChatStream] Fetch 에러:", err);
        handleError(
          err instanceof Error
            ? err
            : new Error(
                "서버와 연결할 수 없습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요."
              ),
          true
        );
      }
    },
    [sessionId, timeout, authToken, cleanup, handleError, readStream]
  );

  /**
   * 스트리밍 중단 함수 (AbortController 사용)
   */
  const abort = useCallback(() => {
    cleanup();
    setConnectionState("idle");
  }, [cleanup]);

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
      cleanup();
    };
  }, [cleanup]);

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
