/**
 * 백테스트 실시간 WebSocket 훅
 * - 백테스트 진행 상황을 WebSocket으로 실시간 수신
 * - 차트 데이터 실시간 업데이트
 */

import { useEffect, useRef, useState } from "react";

/**
 * WebSocket 메시지 타입
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

            case "progress":
              console.log(
                `📊 진행률: ${message.progress_percent}% (수익률: ${message.cumulative_return.toFixed(2)}%)`,
              );

              // 시뮬레이션 시작됨 -> 준비 단계 완료
              setPreparationStage(null);

              const newDataPoint = {
                date: message.date,
                portfolioValue: message.portfolio_value,
                cumulativeReturn: message.cumulative_return,
                dailyReturn: message.daily_return,
                currentMdd: message.current_mdd,
                buyCount: message.buy_count,
                sellCount: message.sell_count,
              };
              console.log(`📊 [useBacktestWebSocket] 새 데이터 포인트 추가:`, newDataPoint);

              // 차트 데이터 추가
              setChartData((prev) => {
                const updated = [...prev, newDataPoint];
                console.log(`📊 [useBacktestWebSocket] chartData 업데이트: ${prev.length} → ${updated.length}개`);
                return updated;
              });

              // 진행률 업데이트
              setProgress(message.progress_percent);
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
  }, [backtestId, enabled, apiUrl]);

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
