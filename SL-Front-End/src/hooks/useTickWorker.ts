import { useEffect, useRef, useState, useCallback } from "react";
import type {
  TickData,
  AggregatedStockUpdate,
  WorkerMessage,
  WorkerResponse,
} from "@/workers/tickAggregator.worker";

export type { TickData, AggregatedStockUpdate };

interface UseTickWorkerOptions {
  batchInterval?: number;
  enabled?: boolean;
}

/**
 * Web Worker를 통한 tick 데이터 처리 훅
 * - tick 데이터를 Worker로 전달
 * - Worker에서 집계된 배치 업데이트 수신
 */
export function useTickWorker(options: UseTickWorkerOptions = {}) {
  const { batchInterval = 100, enabled = true } = options;

  const workerRef = useRef<Worker | null>(null);
  const [latestUpdates, setLatestUpdates] = useState<
    Record<string, AggregatedStockUpdate>
  >({});
  const [isReady, setIsReady] = useState(false);

  // Worker 초기화
  useEffect(() => {
    if (!enabled) {
      setIsReady(false);
      return;
    }

    // Worker 생성
    const worker = new Worker(
      new URL("../workers/tickAggregator.worker.ts", import.meta.url)
    );
    workerRef.current = worker;

    // 메시지 핸들러
    worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const message = event.data;

      if (message.type === "BATCH_UPDATE") {
        setLatestUpdates(message.updates);
      } else if (message.type === "READY") {
        setIsReady(true);
      }
    };

    worker.onerror = (error) => {
      console.error("Tick Worker error:", error);
    };

    // 초기 batch interval 설정
    worker.postMessage({
      type: "SET_BATCH_INTERVAL",
      interval: batchInterval,
    } satisfies WorkerMessage);

    // Cleanup
    return () => {
      worker.terminate();
      workerRef.current = null;
      setIsReady(false);
      setLatestUpdates({});
    };
  }, [enabled, batchInterval]);

  // batch interval 변경 시 Worker에 전달
  useEffect(() => {
    if (workerRef.current && isReady) {
      workerRef.current.postMessage({
        type: "SET_BATCH_INTERVAL",
        interval: batchInterval,
      } satisfies WorkerMessage);
    }
  }, [batchInterval, isReady]);

  /**
   * tick 데이터를 Worker로 전송
   */
  const sendTick = useCallback((tick: TickData) => {
    if (workerRef.current) {
      workerRef.current.postMessage({
        type: "TICK",
        data: tick,
      } satisfies WorkerMessage);
    }
  }, []);

  /**
   * 대기 중인 업데이트 클리어
   */
  const clearPending = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.postMessage({ type: "CLEAR" } satisfies WorkerMessage);
    }
    setLatestUpdates({});
  }, []);

  return {
    sendTick,
    latestUpdates,
    clearPending,
    isReady,
  };
}
