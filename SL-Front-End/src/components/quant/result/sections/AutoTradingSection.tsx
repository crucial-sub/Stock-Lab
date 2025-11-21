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
  const [showCapitalInput, setShowCapitalInput] = useState(false);
  const [allocatedCapital, setAllocatedCapital] = useState<string>("50000000");

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
    mutationFn: (capital: number) =>
      autoTradingApi.activateAutoTrading({
        session_id: sessionId,
        // initial_capital 제거 - 백엔드에서 키움 계좌 잔고 자동 조회
        allocated_capital: capital,
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
    setShowCapitalInput(true);
  };

  const handleConfirmActivate = () => {
    const capital = Number.parseFloat(allocatedCapital);

    if (Number.isNaN(capital) || capital <= 0) {
      alert("유효한 금액을 입력해주세요.");
      return;
    }

    if (capital < 1000000) {
      alert("최소 100만원 이상의 금액을 입력해주세요.");
      return;
    }

    setIsActivating(true);
    setShowCapitalInput(false);
    activateMutation.mutate(capital);
  };

  const handleCancelInput = () => {
    setShowCapitalInput(false);
    setAllocatedCapital("50000000");
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
    <>
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

      {/* 할당 자본 입력 모달 */}
      {showCapitalInput && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              가상매매 할당 금액 설정
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              백테스트 전략에 할당할 가상매매 금액을 입력해주세요. 입력한 금액만큼 가상매매가 진행됩니다.
            </p>

            <div className="mb-6">
              <label
                htmlFor="allocatedCapital"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                할당 금액 (원)
              </label>
              <input
                id="allocatedCapital"
                type="text"
                value={allocatedCapital}
                onChange={(e) => {
                  const value = e.target.value.replace(/[^\d]/g, "");
                  setAllocatedCapital(value);
                }}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="50000000"
              />
              <p className="text-xs text-gray-500 mt-2">
                입력 금액: {Number.parseFloat(allocatedCapital || "0").toLocaleString()}원
                (최소 100만원 이상)
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCancelInput}
                className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleConfirmActivate}
                className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors"
              >
                활성화
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
