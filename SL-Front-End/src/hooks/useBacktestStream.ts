/**
 * useBacktestStream 커스텀 훅
 *
 * EventSource API를 사용하여 SSE 기반 백테스트 실시간 스트리밍을 처리합니다.
 * - 10%마다 진행 상황 및 증분 데이터 수신
 * - 데이터 누적 로직
 * - 자동 재연결 및 에러 처리
 */

"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type {
  SSEEventUnion,
  SSEBacktestProgressEvent,
  SSEBacktestCompleteEvent,
  YieldPoint,
  BacktestStatistics,
  PeriodReturn,
  SSEConnectionState,
  SSEConnectionError,
} from "@/types/sse";

/**
 * 백테스트 설정
 */
export interface BacktestConfig {
  /** 전략 ID */
  strategyId: string;
  /** 투자 설정 */
  config: {
    /** 투자 금액 */
    initialCapital: number;
    /** 시작일 (ISO 8601) */
    startDate: string;
    /** 종료일 (ISO 8601) */
    endDate: string;
  };
}

/**
 * 백테스트 실행 상태
 */
export type BacktestPhase = "idle" | "loading" | "completed" | "error";

/**
 * 누적 데이터
 */
export interface AccumulatedData {
  /** 누적된 수익률 데이터 포인트 */
  yieldPoints: YieldPoint[];
  /** 현재 통계 */
  statistics: {
    currentReturn: number;
    elapsedTime: number;
    estimatedRemainingTime: number;
  };
}

/**
 * 백테스트 완료 데이터
 */
export interface BacktestCompleteData {
  /** 백테스트 ID */
  backtestId: string;
  /** 최종 통계 */
  statistics: BacktestStatistics;
  /** 전체 수익률 데이터 */
  allYieldPoints: YieldPoint[];
  /** 기간별 수익률 */
  periodReturns: PeriodReturn[];
  /** 연도별 수익률 */
  yearlyReturns?: Array<{ year: number; return: number }>;
  /** 월별 수익률 */
  monthlyReturns?: Array<{ month: string; return: number }>;
  /** 종목별 수익률 */
  stockWiseReturns?: Array<{ stockName: string; return: number; weight: number }>;
  /** 총 자산 데이터 */
  totalAssetsData?: Array<{ date: string; assets: number }>;
  /** 마크다운 요약 */
  summary: string;
}

/**
 * 백테스트 실행 상태
 */
export interface ExecutionState {
  /** 실행 단계 */
  phase: BacktestPhase;
  /** 진행률 (0-100) */
  progress: number;
  /** 누적 데이터 */
  accumulatedData: AccumulatedData;
  /** 최종 결과 (완료 시) */
  finalResult: BacktestCompleteData | null;
  /** 에러 */
  error: Error | null;
}

/**
 * useBacktestStream 반환 타입
 */
interface UseBacktestStreamReturn {
  /** 실행 상태 */
  state: ExecutionState;
  /** 백테스트 시작 함수 */
  start: () => void;
  /** 백테스트 중단 함수 */
  abort: () => void;
  /** 재시도 함수 */
  retry: () => void;
}

/**
 * SSE 기반 백테스트 스트리밍 커스텀 훅
 *
 * @param backtestConfig - 백테스트 설정
 * @returns 실행 상태 및 제어 함수
 *
 * @example
 * ```tsx
 * function BacktestComponent() {
 *   const { state, start, abort } = useBacktestStream({
 *     strategyId: "strategy_123",
 *     config: {
 *       initialCapital: 10000000,
 *       startDate: "2024-01-01",
 *       endDate: "2024-12-31"
 *     }
 *   });
 *
 *   useEffect(() => {
 *     start(); // 마운트 시 자동 시작
 *   }, [start]);
 *
 *   if (state.phase === 'loading') {
 *     return <LoadingView progress={state.progress} data={state.accumulatedData} />;
 *   }
 *
 *   if (state.phase === 'completed') {
 *     return <ResultView result={state.finalResult} />;
 *   }
 *
 *   return null;
 * }
 * ```
 */
export function useBacktestStream(
  backtestConfig: BacktestConfig
): UseBacktestStreamReturn {
  // 상태 관리
  const [state, setState] = useState<ExecutionState>({
    phase: "idle",
    progress: 0,
    accumulatedData: {
      yieldPoints: [],
      statistics: {
        currentReturn: 0,
        elapsedTime: 0,
        estimatedRemainingTime: 0,
      },
    },
    finalResult: null,
    error: null,
  });

  // Ref로 관리하는 값들 (리렌더링 방지)
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectCountRef = useRef<number>(0);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);

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
  }, []);

  /**
   * 에러 처리 함수
   */
  const handleError = useCallback(
    (err: Error | SSEConnectionError, retryable = true) => {
      console.error("[useBacktestStream] 에러 발생:", err);

      setState((prev) => ({
        ...prev,
        phase: "error",
        error: err,
      }));

      closeConnection();

      // 자동 재연결 로직 (최대 3회)
      if (retryable && reconnectCountRef.current < 3) {
        reconnectCountRef.current += 1;
        console.log(
          `[useBacktestStream] 재연결 시도 중 (${reconnectCountRef.current}/3)...`
        );

        setTimeout(() => {
          start();
        }, 1000 * reconnectCountRef.current); // 지수 백오프
      }
    },
    [closeConnection]
  );

  /**
   * 진행 상황 이벤트 처리
   */
  const handleProgress = useCallback((data: SSEBacktestProgressEvent) => {
    console.log(
      `[useBacktestStream] 진행률: ${data.data.progress}%`,
      `새 데이터 포인트: ${data.data.incremental.yieldPoints.length}개`
    );

    setState((prev) => ({
      ...prev,
      progress: data.data.progress,
      accumulatedData: {
        // 증분 데이터를 기존 데이터에 병합
        yieldPoints: [
          ...prev.accumulatedData.yieldPoints,
          ...data.data.incremental.yieldPoints,
        ],
        // 통계 업데이트
        statistics: data.data.cumulative,
      },
    }));
  }, []);

  /**
   * 완료 이벤트 처리
   */
  const handleComplete = useCallback(
    (data: SSEBacktestCompleteEvent) => {
      console.log("[useBacktestStream] 백테스트 완료:", data.data.backtestId);

      setState((prev) => ({
        ...prev,
        phase: "completed",
        progress: 100,
        finalResult: data.data,
      }));

      closeConnection();
    },
    [closeConnection]
  );

  /**
   * SSE 이벤트 처리 함수
   */
  const handleSSEEvent = useCallback(
    (event: MessageEvent) => {
      try {
        const data: SSEEventUnion = JSON.parse(event.data);

        switch (data.type) {
          case "backtest_progress":
            handleProgress(data as SSEBacktestProgressEvent);
            break;

          case "backtest_complete":
            handleComplete(data as SSEBacktestCompleteEvent);
            break;

          case "error":
            const sseError = new Error(data.message) as SSEConnectionError;
            sseError.code = data.code;
            sseError.retryable = false;
            handleError(sseError, false);
            break;

          default:
            console.warn("[useBacktestStream] 알 수 없는 이벤트 타입:", data);
        }
      } catch (parseError) {
        console.error("[useBacktestStream] JSON 파싱 에러:", parseError);
        handleError(
          new Error("서버 응답을 파싱하는 중 오류가 발생했습니다."),
          false
        );
      }
    },
    [handleProgress, handleComplete, handleError]
  );

  /**
   * 백테스트 시작 함수
   */
  const start = useCallback(() => {
    // 기존 연결 정리
    closeConnection();

    // 초기화
    setState({
      phase: "loading",
      progress: 0,
      accumulatedData: {
        yieldPoints: [],
        statistics: {
          currentReturn: 0,
          elapsedTime: 0,
          estimatedRemainingTime: 0,
        },
      },
      finalResult: null,
      error: null,
    });

    // SSE 엔드포인트 URL 생성
    const baseUrl =
      process.env.NEXT_PUBLIC_CHATBOT_API_URL || window.location.origin;
    const url = new URL("/api/v1/backtest/execute-stream", baseUrl);
    url.searchParams.set("strategyId", backtestConfig.strategyId);
    url.searchParams.set(
      "initialCapital",
      backtestConfig.config.initialCapital.toString()
    );
    url.searchParams.set("startDate", backtestConfig.config.startDate);
    url.searchParams.set("endDate", backtestConfig.config.endDate);

    try {
      // EventSource 생성
      const eventSource = new EventSource(url.toString());
      eventSourceRef.current = eventSource;

      console.log("[useBacktestStream] SSE 연결 시작:", url.toString());

      // 연결 성공
      eventSource.onopen = () => {
        console.log("[useBacktestStream] SSE 연결 성공");
        reconnectCountRef.current = 0; // 성공 시 재연결 카운트 리셋
      };

      // 메시지 수신
      eventSource.onmessage = handleSSEEvent;

      // 에러 처리
      eventSource.onerror = (event) => {
        console.error("[useBacktestStream] SSE 연결 에러:", event);
        const connectionError = new Error(
          "네트워크 연결이 불안정합니다. 인터넷 연결을 확인하고 다시 시도해주세요."
        ) as SSEConnectionError;
        connectionError.retryable = true;
        handleError(connectionError);
      };

      // 타임아웃 설정 (60초)
      timeoutIdRef.current = setTimeout(() => {
        console.error("[useBacktestStream] 타임아웃 발생");
        handleError(
          new Error(
            "백테스트 실행 시간이 초과되었습니다 (60초). 서버가 바쁘거나 데이터가 많을 수 있습니다. 잠시 후 다시 시도해주세요."
          ),
          false
        );
      }, 60000);
    } catch (err) {
      console.error("[useBacktestStream] EventSource 생성 에러:", err);
      handleError(
        new Error(
          "서버와 연결할 수 없습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요."
        ),
        false
      );
    }
  }, [backtestConfig, handleSSEEvent, handleError, closeConnection]);

  /**
   * 백테스트 중단 함수
   */
  const abort = useCallback(() => {
    console.log("[useBacktestStream] 사용자에 의한 중단");
    closeConnection();
    setState((prev) => ({
      ...prev,
      phase: "idle",
    }));
  }, [closeConnection]);

  /**
   * 재시도 함수
   */
  const retry = useCallback(() => {
    console.log("[useBacktestStream] 수동 재시도 시작");
    reconnectCountRef.current = 0;
    start();
  }, [start]);

  /**
   * 컴포넌트 언마운트 시 정리
   */
  useEffect(() => {
    return () => {
      closeConnection();
    };
  }, [closeConnection]);

  return {
    state,
    start,
    abort,
    retry,
  };
}
