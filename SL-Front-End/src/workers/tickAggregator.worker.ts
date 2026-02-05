/**
 * Tick 데이터 집계 Web Worker
 * - WebSocket tick 데이터를 받아서 집계
 * - 설정된 interval마다 배치로 메인 스레드에 전달
 */

export interface TickData {
  timestamp: string;
  client: string;
  code: string;
  data: {
    item: string;
    price: string;
    change: string;
    change_rate: string;
    volume: string;
    timestamp: string;
    strength?: string;
    net_buy_volume?: string;
  };
}

export interface AggregatedStockUpdate {
  code: string;
  price: string;
  change_rate: string;
  volume: number;
  tradingValue: number;
  strength?: string;
  lastUpdate: string;
}

export type WorkerMessage =
  | { type: "TICK"; data: TickData }
  | { type: "SET_BATCH_INTERVAL"; interval: number }
  | { type: "CLEAR" };

export type WorkerResponse =
  | { type: "BATCH_UPDATE"; updates: Record<string, AggregatedStockUpdate>; timestamp: number }
  | { type: "READY" };

// 내부 상태
const pendingUpdates = new Map<string, AggregatedStockUpdate>();
let batchInterval = 100; // 기본 100ms 배치
let flushTimeoutId: ReturnType<typeof setTimeout> | null = null;

/**
 * Tick 처리 함수
 */
function processTick(tick: TickData): void {
  const price = parseFloat(tick.data.price) || 0;
  const volume = parseFloat(tick.data.volume) || 0;

  pendingUpdates.set(tick.code, {
    code: tick.code,
    price: tick.data.price,
    change_rate: tick.data.change_rate,
    volume,
    tradingValue: price * volume,
    strength: tick.data.strength,
    lastUpdate: tick.data.timestamp,
  });
}

/**
 * 배치 전송 함수
 */
function flushUpdates(): void {
  if (pendingUpdates.size > 0) {
    const updates: Record<string, AggregatedStockUpdate> = {};
    pendingUpdates.forEach((value, key) => {
      updates[key] = value;
    });

    self.postMessage({
      type: "BATCH_UPDATE",
      updates,
      timestamp: Date.now(),
    } satisfies WorkerResponse);

    pendingUpdates.clear();
  }

  // 다음 배치 예약
  flushTimeoutId = setTimeout(flushUpdates, batchInterval);
}

/**
 * 메시지 핸들러
 */
self.onmessage = (event: MessageEvent<WorkerMessage>) => {
  const message = event.data;

  switch (message.type) {
    case "TICK":
      processTick(message.data);
      break;

    case "SET_BATCH_INTERVAL":
      batchInterval = message.interval;
      // 기존 타이머 취소하고 새 interval로 재시작
      if (flushTimeoutId) {
        clearTimeout(flushTimeoutId);
      }
      flushTimeoutId = setTimeout(flushUpdates, batchInterval);
      break;

    case "CLEAR":
      pendingUpdates.clear();
      break;
  }
};

// Worker 시작 시 배치 전송 시작
flushTimeoutId = setTimeout(flushUpdates, batchInterval);

// Ready 신호 전송
self.postMessage({ type: "READY" } satisfies WorkerResponse);
