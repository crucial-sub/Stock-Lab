"use client";

/**
 * 백테스트 로딩 상태 컴포넌트
 * - 백테스트가 실행 중일 때 표시되는 UI
 * - 진행률, 통계, 차트 표시
 * - TradingActivityChart 재사용
 * - WebSocket으로 실시간 데이터 수신
 */

import { useBacktestWebSocket, type PreparationStage } from "@/hooks/useBacktestWebSocket";
import { useRouter } from "next/navigation";
import { TradingActivityChart } from "./TradingActivityChart";

/**
 * 준비 단계 라벨 매핑
 * - 서버에서 전송하는 단계 코드를 한국어 라벨로 변환
 */
const STAGE_LABELS: Record<PreparationStage["stage"], string> = {
  LOADING_PRICE_DATA: "가격 데이터 로딩",
  LOADING_FINANCIAL_DATA: "재무 데이터 로딩",
  CALCULATING_FACTORS: "팩터 계산",
  PREPARING_SIMULATION: "시뮬레이션 준비",
};

/**
 * 준비 단계 순서 (UI 표시용)
 */
const STAGE_ORDER: PreparationStage["stage"][] = [
  "LOADING_PRICE_DATA",
  "LOADING_FINANCIAL_DATA",
  "CALCULATING_FACTORS",
  "PREPARING_SIMULATION",
];

interface BacktestLoadingStateProps {
  backtestId: string;
  strategyName?: string;
  status: "pending" | "running";
  progress: number;
  webSocketEnabled?: boolean;
  buyCount?: number;
  sellCount?: number;
  currentReturn?: number;
  currentCapital?: number;
  currentDate?: string;
  currentMdd?: number;
  initialCapital?: number; // 초기 투자 금액
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
  elapsedTime?: number; // 경과 시간 (milliseconds)
  yieldPoints?: Array<{
    date: string;
    buyCount?: number;
    sellCount?: number;
    cumulativeReturn?: number;
  }>;
}

export function BacktestLoadingState({
  backtestId,
  strategyName,
  status,
  progress: initialProgress,
  buyCount: initialBuyCount,
  sellCount: initialSellCount,
  currentReturn: initialCurrentReturn,
  currentCapital: initialCurrentCapital,
  currentDate,
  currentMdd,
  initialCapital,
  startDate,
  endDate,
  elapsedTime,
  yieldPoints: initialYieldPoints,
  webSocketEnabled = true,
}: BacktestLoadingStateProps) {
  const router = useRouter();

  // 밀리초를 "X초" 형식으로 변환
  const formatTimeInSeconds = (milliseconds: number | undefined): string => {
    if (milliseconds === undefined || milliseconds === null) return "0초";
    const seconds = Math.floor(milliseconds / 1000);
    return `${seconds}초`;
  };

  // ✅ WebSocket으로 실시간 데이터 수신
  // pending과 running 상태 모두에서 WebSocket 연결
  const {
    isConnected,
    chartData,
    progress: wsProgress,
    isCompleted,
    error: wsError,
    preparationStage,
  } = useBacktestWebSocket(backtestId, webSocketEnabled);

  // WebSocket 데이터와 초기 props 데이터 병합
  const progress = wsProgress > 0 ? wsProgress : initialProgress;
  const yieldPoints = chartData.length > 0
    ? chartData.map(point => ({
      date: point.date,
      cumulativeReturn: point.cumulativeReturn,
      buyCount: point.buyCount,
      sellCount: point.sellCount,
    }))
    : initialYieldPoints;

  // WebSocket 데이터에서 현재 수익률 및 자본 계산
  const currentReturn = chartData.length > 0
    ? chartData[chartData.length - 1].cumulativeReturn
    : initialCurrentReturn;
  const currentCapital = chartData.length > 0
    ? chartData[chartData.length - 1].portfolioValue
    : initialCurrentCapital;

  console.log(`📡 [BacktestLoadingState] backtestId=${backtestId}, status=${status}`);
  console.log(`📡 [BacktestLoadingState] WebSocket enabled=${webSocketEnabled}`);
  console.log(`📡 [BacktestLoadingState] WebSocket 상태: connected=${isConnected}, progress=${wsProgress}%, dataPoints=${chartData.length}`);
  console.log(`📡 [BacktestLoadingState] chartData:`, chartData);
  console.log(`📡 [BacktestLoadingState] yieldPoints (최종):`, yieldPoints);
  console.log(`📡 [BacktestLoadingState] yieldPoints 길이: WS=${chartData.length}, Props=${initialYieldPoints?.length || 0}, 최종=${yieldPoints?.length || 0}`);
  console.log(`📡 [BacktestLoadingState] 차트 표시 조건: ${yieldPoints && yieldPoints.length > 0 ? '✅ 표시됨' : '❌ 숨겨짐'}`);
  if (wsError) {
    console.warn(`⚠️ [BacktestLoadingState] WebSocket 에러 (폴백 사용):`, wsError);
  }

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto space-y-6">
        {/* 헤더 영역 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-accent-error">
                    {strategyName || backtestId}
                  </h1>
                  <p className="text-sm text-text-body mt-1">
                    {status === "pending"
                      ? "백테스트 대기 중..."
                      : "백테스트 실행 중..."}
                  </p>
                  {currentDate && (
                    <p className="text-xs text-text-muted mt-1">
                      현재 처리 중: {currentDate}
                    </p>
                  )}
                </div>
                <div className="ml-4">
                  <button
                    onClick={() => router.push("/quant")}
                    className="px-4 py-2 bg-bg-app hover:bg-border-primary text-text-body rounded-lg transition-colors text-sm font-medium"
                  >
                    나중에 보기
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 안내 메시지 */}
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 백테스트는 백그라운드에서 계속 실행됩니다. 이 페이지를 벗어나도 괜찮습니다.
              <span className="font-semibold"> 포트폴리오 목록</span>에서 나중에 결과를 확인할 수 있습니다.
            </p>
          </div>

          {/* 진행률 바 */}
          <div className="mt-4">
            <div className="w-full bg-bg-app rounded-full h-2 overflow-hidden">
              <div
                className="bg-accent-primary h-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* 실시간 통계 */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6">
          <div className="grid grid-cols-5 gap-4">
            {/* 누적 수익률 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">누적 수익률</div>
              <div
                className={`text-2xl font-bold ${
                  (currentReturn ?? 0) >= 0 ? "text-red-500" : "text-blue-500"
                }`}
              >
                {currentReturn !== undefined && currentReturn !== null
                  ? `${currentReturn > 0 ? "+" : ""}${currentReturn.toFixed(2)}%`
                  : "0.00%"}
              </div>
            </div>

            {/* MDD */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">MDD</div>
              <div className="text-2xl font-bold text-accent-error">
                {currentMdd !== undefined && currentMdd !== null
                  ? `${currentMdd.toFixed(2)}%`
                  : "0.00%"}
              </div>
            </div>

            {/* 현재 자본금 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">현재 자본</div>
              <div className="text-2xl font-bold text-text-heading">
                {currentCapital !== undefined
                  ? `${Math.round(currentCapital).toLocaleString()}원`
                  : initialCapital
                    ? `${Math.round(initialCapital).toLocaleString()}원`
                    : "0원"}
              </div>
            </div>

            {/* 진행시간 */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">진행시간</div>
              <div className="text-2xl font-bold text-text-heading">
                {formatTimeInSeconds(elapsedTime)}
              </div>
            </div>

            {/* 진행률 (예상시간 자리 대체) */}
            <div className="text-center">
              <div className="text-sm text-text-body mb-1">진행률</div>
              <div className="text-2xl font-bold text-accent-primary">
                {progress}%
              </div>
            </div>
          </div>

          {/* 백테스트 준비 중 메시지 (progress === 0 AND 차트 데이터 없을 때만) - 수치 표시 아래로 이동 */}
          {progress === 0 && (!yieldPoints || yieldPoints.length === 0) && (
            <div className="mt-6 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-center gap-4 mb-4">
                {/* 로봇 아이콘 애니메이션 */}
                <div className="relative">
                  <div className="w-12 h-12 bg-accent-primary rounded-lg flex items-center justify-center animate-pulse">
                    <span className="text-2xl">🤖</span>
                  </div>
                  {/* 회전하는 로딩 링 */}
                  <div className="absolute inset-0 border-4 border-transparent border-t-accent-primary rounded-lg animate-spin" />
                </div>

                {/* 진행 중 메시지 */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-lg font-semibold text-blue-800 mb-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span>백테스트 데이터를 준비하고 있습니다</span>
                  </div>
                  <p className="text-sm text-blue-700">
                    {preparationStage?.message || "종목 데이터를 로드하고 전략 조건을 분석 중입니다..."}
                  </p>
                </div>
              </div>

              {/* 📡 실제 준비 단계별 진행 표시 (서버에서 실시간 수신) */}
              <div className="grid grid-cols-4 gap-3 text-xs">
                {STAGE_ORDER.map((stage, index) => {
                  const stageNumber = index + 1;
                  const currentStageNumber = preparationStage?.stageNumber || 0;

                  // 단계 상태 결정
                  const isCompleted = currentStageNumber > stageNumber;
                  const isActive = currentStageNumber === stageNumber;
                  const isPending = currentStageNumber < stageNumber;

                  return (
                    <div
                      key={stage}
                      className={`flex items-center gap-2 transition-all duration-300 ${
                        isCompleted
                          ? "text-green-700"
                          : isActive
                          ? "text-blue-700"
                          : "text-blue-500 opacity-50"
                      }`}
                    >
                      {/* 상태 아이콘 */}
                      {isCompleted ? (
                        <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      ) : isActive ? (
                        <div className="w-4 h-4 bg-blue-500 rounded-full animate-ping" />
                      ) : (
                        <div className="w-4 h-4 bg-blue-300 rounded-full" />
                      )}
                      {/* 단계 라벨 */}
                      <span className={isActive ? "font-semibold" : ""}>
                        {STAGE_LABELS[stage]}
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* 준비 단계 진행률 바 */}
              {preparationStage && (
                <div className="mt-4">
                  <div className="w-full bg-blue-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full transition-all duration-500 ease-out"
                      style={{
                        width: `${(preparationStage.stageNumber / preparationStage.totalStages) * 100}%`,
                      }}
                    />
                  </div>
                  <p className="text-xs text-blue-600 mt-1 text-center">
                    준비 단계 {preparationStage.stageNumber} / {preparationStage.totalStages}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 차트 영역 - yieldPoints가 있으면 차트 표시, 없으면 로봇 UI 표시하지 않음 (겹침 방지) */}
        {yieldPoints && yieldPoints.length > 0 && (
          <div className="bg-bg-surface rounded-lg shadow-card p-6">
            <h2 className="text-lg font-bold text-text-strong mb-4">
              매수/매도 활동
            </h2>
            <TradingActivityChart
              yieldPoints={yieldPoints}
              startDate={startDate}
              endDate={endDate}
            />
          </div>
        )}
      </div>
    </div>
  );
}
