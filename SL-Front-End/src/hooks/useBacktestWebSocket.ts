/**
 * 백테스트 실시간 WebSocket 훅
 * - 백테스트 진행 상황을 WebSocket으로 실시간 수신
 * - 차트 데이터 실시간 업데이트
 * - Delta 프로토콜 지원: 변경된 필드만 수신하여 네트워크 효율성 향상
 */

import { useEffect, useRef, useState, useCallback } from "react";

/**
 * WebSocket 메시지 타입 - 전체 데이터 전송 (기존 방식)
 */
export interface ProgressMessage {
  type: "progress";
  date: string;
  portfolio_value: number;
  cash: number;
  position_value: number;
  daily_return: number;
  cumulative_return: number;
  progress_percent: number;
  current_mdd: number;
  buy_count: number;
  sell_count: number;
}

/**
 * Delta 메시지 타입 - 변경된 필드만 전송 (최적화 방식)
 * - 매번 전체 데이터를 보내는 대신, 변경된 필드만 전송하는 Delta 프로토콜
 * - 네트워크 전송량 감소 및 불필요한 리렌더 방지
 */
export interface DeltaMessage {
  type: "delta";
  date: string;
  /** 변경된 필드만 포함 (Partial) */
  changes: Partial<{
    portfolio_value: number;
    cash: number;
    position_value: number;
    daily_return: number;
    cumulative_return: number;
    progress_percent: number;
    current_mdd: number;
    buy_count: number;
    sell_count: number;
  }>;
}

export interface CompletedMessage {
  type: "completed";
  statistics: {
    final_value: number;
    total_return: number;
    annualized_return: number;
    daily_avg_return: number;
    max_drawdown: number;
    total_trades: number;
    simulation_time: number;
  };
  summary?: string; // AI 생성 마크다운 요약
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

/**
 * 백테스트 준비 단계 메시지
 * - 서버에서 데이터 로딩, 팩터 계산 등 준비 과정 중 전송
 */
export interface PreparationMessage {
  type: "preparation";
  stage: "LOADING_PRICE_DATA" | "LOADING_FINANCIAL_DATA" | "CALCULATING_FACTORS" | "PREPARING_SIMULATION";
  stage_number: number;
  total_stages: number;
  message: string;
}

/**
 * 준비 단계 정보 타입
 */
export interface PreparationStage {
  stage: PreparationMessage["stage"];
  stageNumber: number;
  totalStages: number;
  message: string;
}

export type WebSocketMessage =
  | ProgressMessage
  | DeltaMessage
  | CompletedMessage
  | ErrorMessage
  | PreparationMessage;

/**
 * 차트 데이터 포인트
 */
export interface ChartDataPoint {
  date: string;
  portfolioValue: number;
  cumulativeReturn: number;
  dailyReturn: number;
  currentMdd: number;
  buyCount: number;
  sellCount: number;
}

/**
 * WebSocket 훅 반환 타입
 */
export interface UseBacktestWebSocketReturn {
  /** 연결 상태 */
  isConnected: boolean;
  /** 차트 데이터 */
  chartData: ChartDataPoint[];
  /** 진행률 (0-100) */
  progress: number;
  /** 완료 여부 */
  isCompleted: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 최종 통계 */
  statistics: CompletedMessage["statistics"] | null;
  /** AI 요약 (마크다운) */
  summary: string | null;
  /** 현재 준비 단계 정보 (백테스트 시작 전) */
  preparationStage: PreparationStage | null;
}

/**
 * Delta 메시지를 ChartDataPoint로 변환
 * - 변경된 필드만 포함된 Delta 메시지를 기존 데이터와 병합
 */
function applyDeltaToDataPoint(
  existing: ChartDataPoint | undefined,
  delta: DeltaMessage
): ChartDataPoint {
  const base: ChartDataPoint = existing || {
    date: delta.date,
    portfolioValue: 0,
    cumulativeReturn: 0,
    dailyReturn: 0,
    currentMdd: 0,
    buyCount: 0,
    sellCount: 0,
  };

  return {
    date: delta.date,
    portfolioValue: delta.changes.portfolio_value ?? base.portfolioValue,
    cumulativeReturn: delta.changes.cumulative_return ?? base.cumulativeReturn,
    dailyReturn: delta.changes.daily_return ?? base.dailyReturn,
    currentMdd: delta.changes.current_mdd ?? base.currentMdd,
    buyCount: delta.changes.buy_count ?? base.buyCount,
    sellCount: delta.changes.sell_count ?? base.sellCount,
  };
}

/**
 * 백테스트 WebSocket 훅
 *
 * @param backtestId - 백테스트 ID
 * @param enabled - WebSocket 연결 활성화 여부
 * @param apiUrl - API 서버 URL (기본: process.env.NEXT_PUBLIC_API_BASE_URL)
 * @returns WebSocket 상태 및 데이터
 *
 * @example
 * ```tsx
 * const { chartData, progress, isCompleted, statistics } = useBacktestWebSocket(backtestId);
 *
 * return (
 *   <div>
 *     <ProgressBar value={progress} />
 *     <Chart data={chartData} />
 *     {isCompleted && <Statistics data={statistics} />}
 *   </div>
 * );
 * ```
 */
export function useBacktestWebSocket(
  backtestId: string | null,
  enabled = true,
  apiUrl?: string,
): UseBacktestWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [progress, setProgress] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statistics, setStatistics] =
    useState<CompletedMessage["statistics"] | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  // 📡 준비 단계 상태 추가
  const [preparationStage, setPreparationStage] = useState<PreparationStage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Progress 메시지 처리 (전체 데이터 전송 방식)
   * - 기존 방식과 호환성 유지
   */
  const handleProgressMessage = useCallback((message: ProgressMessage) => {
    console.log(
      `📊 진행률: ${message.progress_percent}% (수익률: ${message.cumulative_return.toFixed(2)}%)`,
    );

    // 시뮬레이션 시작됨 -> 준비 단계 완료
    setPreparationStage(null);

    const newDataPoint: ChartDataPoint = {
      date: message.date,
      portfolioValue: message.portfolio_value,
      cumulativeReturn: message.cumulative_return,
      dailyReturn: message.daily_return,
      currentMdd: message.current_mdd,
      buyCount: message.buy_count,
      sellCount: message.sell_count,
    };

    // 차트 데이터 추가
    setChartData((prev) => {
      const updated = [...prev, newDataPoint];
      return updated;
    });

    // 진행률 업데이트
    setProgress(message.progress_percent);
  }, []);

  /**
   * Delta 메시지 처리 (변경분만 전송 방식)
   * - 변경된 필드만 기존 데이터에 병합
   * - 불필요한 리렌더 방지
   */
  const handleDeltaMessage = useCallback((message: DeltaMessage) => {
    console.log(
      `📊 [Delta] 날짜: ${message.date}, 변경 필드: ${Object.keys(message.changes).join(", ")}`,
    );

    // 시뮬레이션 시작됨 -> 준비 단계 완료
    setPreparationStage(null);

    // 변경분만 캐시에 병합
    setChartData((prev) => {
      const existingIndex = prev.findIndex((p) => p.date === message.date);

      if (existingIndex !== -1) {
        // 기존 데이터가 있으면 변경분만 병합
        const existing = prev[existingIndex];
        const updated = applyDeltaToDataPoint(existing, message);

        // 불변성 유지하며 업데이트
        const newData = [...prev];
        newData[existingIndex] = updated;
        return newData;
      } else {
        // 새 데이터면 추가
        const newDataPoint = applyDeltaToDataPoint(undefined, message);
        return [...prev, newDataPoint];
      }
    });

    // 진행률 업데이트 (Delta에 포함된 경우)
    if (message.changes.progress_percent !== undefined) {
      setProgress(message.changes.progress_percent);
    }
  }, []);

  useEffect(() => {
    // WebSocket 연결 조건 확인
    if (!enabled || !backtestId) {
      return;
    }

    // WebSocket URL 구성
    const baseUrl =
      apiUrl ||
      process.env.NEXT_PUBLIC_API_BASE_URL?.replace('/api/v1', '') ||
      "http://localhost:8000";
    const wsUrl = baseUrl
      .replace("http://", "ws://")
      .replace("https://", "wss://");
    // ✅ 올바른 경로: /api/v1/ws/backtest/{backtestId}
    const url = `${wsUrl}/api/v1/ws/backtest/${backtestId}`;

    console.log("📡 WebSocket 연결 시도:", url);

    try {
      // WebSocket 연결
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("📡 WebSocket 연결 성공");
        setIsConnected(true);
        setError(null);

        // Ping 전송 (30초마다)
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          switch (message.type) {
            // 📡 준비 단계 메시지 처리
            case "preparation":
              console.log(
                `🔄 준비 단계: [${message.stage_number}/${message.total_stages}] ${message.stage} - ${message.message}`,
              );
              setPreparationStage({
                stage: message.stage,
                stageNumber: message.stage_number,
                totalStages: message.total_stages,
                message: message.message,
              });
              break;

            // 📊 전체 데이터 전송 방식 (기존 호환)
            case "progress":
              handleProgressMessage(message);
              break;

            // 📊 Delta 프로토콜: 변경분만 전송 (최적화)
            case "delta":
              handleDeltaMessage(message);
              break;

            case "completed":
              console.log("✅ 백테스트 완료:", message.statistics);
              console.log("📝 AI 요약 수신:", message.summary?.length || 0, "글자");
              setPreparationStage(null); // 준비 단계 초기화
              setStatistics(message.statistics);
              setSummary(message.summary || null);
              setIsCompleted(true);
              setProgress(100);
              ws.close();
              break;

            case "error":
              console.error("❌ 백테스트 에러:", message.message);
              setPreparationStage(null); // 준비 단계 초기화
              setError(message.message);
              ws.close();
              break;

            default:
              console.warn("알 수 없는 메시지 타입:", message);
          }
        } catch (err) {
          console.error("WebSocket 메시지 파싱 에러:", err);
        }
      };

      ws.onerror = (event) => {
        console.warn("⚠️ WebSocket 연결 실패 (폴백 모드 사용):", {
          readyState: ws.readyState,
          url,
        });
        // 저장된 포트폴리오나 완료된 백테스트의 경우 WebSocket 연결 실패가 정상이므로
        // 에러 메시지를 표시하지 않음 (API 폴백 사용)
        // setError("WebSocket 연결 오류 - 초기 데이터로 표시됩니다");
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log("📡 WebSocket 연결 종료");
        setIsConnected(false);

        // Ping interval 정리
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
      };
    } catch (err) {
      console.error("WebSocket 연결 실패:", err);
      setError("WebSocket 연결 실패");
    }

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };
  }, [backtestId, enabled, apiUrl, handleProgressMessage, handleDeltaMessage]);

  return {
    isConnected,
    chartData,
    progress,
    isCompleted,
    error,
    statistics,
    summary,
    preparationStage,
  };
}
