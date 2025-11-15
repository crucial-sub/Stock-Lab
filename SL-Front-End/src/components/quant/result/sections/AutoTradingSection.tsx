"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { autoTradingApi, AutoTradingStrategyResponse } from "@/lib/api/auto-trading";

interface AutoTradingSectionProps {
  sessionId: string;
  sessionStatus: string;
}

export function AutoTradingSection({ sessionId, sessionStatus }: AutoTradingSectionProps) {
  const queryClient = useQueryClient();
  const [isActivating, setIsActivating] = useState(false);
  const [isDeactivating, setIsDeactivating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  // 내 자동매매 전략 목록 조회
  const { data: strategies, isLoading } = useQuery({
    queryKey: ["autoTradingStrategies"],
    queryFn: autoTradingApi.getMyAutoTradingStrategies,
    refetchInterval: 10000, // 10초마다 갱신
  });

  // 현재 세션에 해당하는 활성화된 전략 찾기
  const activeStrategy = strategies?.find(
    (s: AutoTradingStrategyResponse) =>
      s.simulation_session_id === sessionId && s.is_active
  );

  // 활성화 mutation
  const activateMutation = useMutation({
    mutationFn: () =>
      autoTradingApi.activateAutoTrading({
        session_id: sessionId,
        initial_capital: 50000000, // 5천만원 기본값
      }),
    onSuccess: (data) => {
      alert(data.message);
      queryClient.invalidateQueries({ queryKey: ["autoTradingStrategies"] });
      setIsActivating(false);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "자동매매 활성화에 실패했습니다.");
      setIsActivating(false);
    },
  });

  // 비활성화 mutation
  const deactivateMutation = useMutation({
    mutationFn: (strategyId: string) =>
      autoTradingApi.deactivateAutoTrading(strategyId, {
        sell_all_positions: true,
      }),
    onSuccess: (data) => {
      alert(data.message);
      queryClient.invalidateQueries({ queryKey: ["autoTradingStrategies"] });
      setIsDeactivating(false);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "자동매매 비활성화에 실패했습니다.");
      setIsDeactivating(false);
    },
  });

  // 수동 실행 mutation (테스트용)
  const executeMutation = useMutation({
    mutationFn: (strategyId: string) => autoTradingApi.executeAutoTrading(strategyId),
    onSuccess: (data) => {
      alert(
        `${data.message}\n선정: ${data.selected_count}개, 매수: ${data.bought_count}개`
      );
      setIsExecuting(false);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "자동매매 실행에 실패했습니다.");
      setIsExecuting(false);
    },
  });

  const handleActivate = () => {
    if (sessionStatus?.toUpperCase() !== "COMPLETED") {
      alert("백테스트가 완료된 후에 활성화할 수 있습니다.");
      return;
    }
    setIsActivating(true);
    activateMutation.mutate();
  };

  const handleDeactivate = () => {
    if (!activeStrategy) return;
    setIsDeactivating(true);
    deactivateMutation.mutate(activeStrategy.strategy_id);
  };

  const handleExecute = () => {
    if (!activeStrategy) return;
    setIsExecuting(true);
    executeMutation.mutate(activeStrategy.strategy_id);
  };

  if (isLoading) {
    return (
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6 mb-6">
      <div className="flex items-start justify-between">
        {/* 왼쪽: 정보 */}
        <div className="flex-1">
          <h2 className="text-lg font-bold text-text-strong mb-2">
            실전 자동매매 {activeStrategy ? "(활성화됨)" : ""}
          </h2>
          <p className="text-sm text-text-muted mb-4">
            {activeStrategy
              ? "백테스트 전략을 기반으로 자동매매가 실행됩니다. (모의투자 전용)"
              : "백테스트 전략을 실전 자동매매로 전환하세요. (모의투자 전용)"}
          </p>

          {/* 활성화된 전략 정보 */}
          {activeStrategy && (
            <div className="grid grid-cols-3 gap-6 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-4">
              <div>
                <p className="text-xs text-text-muted mb-1">초기 자본금</p>
                <p className="text-base font-semibold text-text-strong">
                  {Math.round(activeStrategy.initial_capital).toLocaleString('ko-KR')}원
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">현재 자본금</p>
                <p className="text-base font-semibold text-text-strong">
                  {Math.round(activeStrategy.current_capital).toLocaleString('ko-KR')}원
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">현금 잔고</p>
                <p className="text-base font-semibold text-text-strong">
                  {Math.round(activeStrategy.cash_balance).toLocaleString('ko-KR')}원
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">종목당 투자 비율</p>
                <p className="text-base font-semibold text-text-strong">
                  {activeStrategy.per_stock_ratio}%
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">최대 보유 종목</p>
                <p className="text-base font-semibold text-text-strong">
                  {activeStrategy.max_positions}개
                </p>
              </div>
              <div>
                <p className="text-xs text-text-muted mb-1">리밸런싱 주기</p>
                <p className="text-base font-semibold text-text-strong">
                  {activeStrategy.rebalance_frequency === "DAILY" ? "매일" : activeStrategy.rebalance_frequency}
                </p>
              </div>
            </div>
          )}

          {/* 안내 메시지 */}
          {activeStrategy && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                💡 매일 오전 8시에 종목을 선정하고, 오전 9시에 자동으로 매수/매도를 실행합니다.
                <br />
                실시간 수익률은 &quot;내 잔고&quot; 페이지에서 확인하세요.
              </p>
            </div>
          )}
        </div>

        {/* 오른쪽: 버튼 */}
        <div className="ml-6 flex flex-col gap-3">
          {!activeStrategy ? (
            <button
              onClick={handleActivate}
              disabled={isActivating || sessionStatus?.toUpperCase() !== "COMPLETED"}
              className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
                sessionStatus?.toUpperCase() !== "COMPLETED"
                  ? "bg-gray-300 cursor-not-allowed"
                  : isActivating
                  ? "bg-red-400 cursor-wait"
                  : "bg-red-500 hover:bg-red-600"
              }`}
            >
              {isActivating ? "활성화 중..." : "자동매매 활성화"}
            </button>
          ) : (
            <>
              <button
                onClick={handleExecute}
                disabled={isExecuting}
                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
                  isExecuting
                    ? "bg-blue-400 cursor-wait"
                    : "bg-blue-500 hover:bg-blue-600"
                }`}
              >
                {isExecuting ? "실행 중..." : "수동 실행 (테스트)"}
              </button>
              <button
                onClick={handleDeactivate}
                disabled={isDeactivating}
                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${
                  isDeactivating
                    ? "bg-gray-400 cursor-wait"
                    : "bg-gray-500 hover:bg-gray-600"
                }`}
              >
                {isDeactivating ? "비활성화 중..." : "자동매매 비활성화"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
