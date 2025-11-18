"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  type AutoTradingStrategyResponse,
  autoTradingApi,
} from "@/lib/api/auto-trading";

interface AutoTradingSectionProps {
  sessionId: string;
  sessionStatus: string;
}

export function AutoTradingSection({
  sessionId,
  sessionStatus,
}: AutoTradingSectionProps) {
  const queryClient = useQueryClient();
  const [isActivating, setIsActivating] = useState(false);
  const [isDeactivating, setIsDeactivating] = useState(false);

  // 내 자동매매 전략 목록 조회
  const { data: strategies, isLoading } = useQuery({
    queryKey: ["autoTradingStrategies"],
    queryFn: autoTradingApi.getMyAutoTradingStrategies,
    refetchInterval: 10000, // 10초마다 갱신
  });

  // 현재 세션에 해당하는 활성화된 전략 찾기
  const activeStrategy = strategies?.find(
    (s: AutoTradingStrategyResponse) =>
      s.simulation_session_id === sessionId && s.is_active,
  );

  // 활성화 mutation
  const activateMutation = useMutation({
    mutationFn: () =>
      autoTradingApi.activateAutoTrading({
        session_id: sessionId,
        // initial_capital 제거 - 백엔드에서 키움 계좌 잔고 자동 조회
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
      alert(
        error.response?.data?.detail || "자동매매 비활성화에 실패했습니다.",
      );
      setIsDeactivating(false);
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
      <div className="flex items-center justify-between">
        {/* 왼쪽: 제목 */}
        <div>
          <h2 className="text-lg font-bold text-text-strong">
            실전 자동매매 {activeStrategy ? "(활성화됨)" : ""}
          </h2>
          <p className="text-sm text-text-muted mt-1">
            {activeStrategy
              ? "백테스트 전략을 기반으로 자동매매가 실행됩니다. (모의투자 전용)"
              : "백테스트 전략을 실전 자동매매로 전환하세요. (모의투자 전용)"}
          </p>
        </div>

        {/* 오른쪽: 버튼 */}
        <div>
          {!activeStrategy ? (
            <button
              onClick={handleActivate}
              disabled={
                isActivating || sessionStatus?.toUpperCase() !== "COMPLETED"
              }
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
          )}
        </div>
      </div>
    </div>
  );
}
