"use client";

import { ConfirmModal } from "@/components/modal/ConfirmModal";
import {
  type AutoTradingStrategyResponse,
  type DeactivationConditions,
  autoTradingApi,
} from "@/lib/api/auto-trading";
import { kiwoomApi } from "@/lib/api/kiwoom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface AutoTradingSectionProps {
  sessionId: string;
  sessionStatus: string;
}

export function AutoTradingSection({
  sessionId,
  sessionStatus,
}: AutoTradingSectionProps) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [isActivating, setIsActivating] = useState(false);
  const [isDeactivating, setIsDeactivating] = useState(false);
  const [showCapitalInput, setShowCapitalInput] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [deactivationConditions, setDeactivationConditions] = useState<DeactivationConditions | null>(null);
  const [allocatedCapital, setAllocatedCapital] = useState<string>("50000000");
  const [strategyName, setStrategyName] = useState<string>("");
  const [isCheckingKiwoom, setIsCheckingKiwoom] = useState(false);
  // 증권 계좌 미연동 시 표시할 확인 모달 상태
  const [showKiwoomRequiredModal, setShowKiwoomRequiredModal] = useState(false);
  // 활성화/비활성화 성공 알림 모달 상태
  const [showActivateSuccess, setShowActivateSuccess] = useState(false);
  const [activateSuccessMessage, setActivateSuccessMessage] = useState("");
  const [showDeactivateSuccess, setShowDeactivateSuccess] = useState(false);
  const [deactivateSuccessMessage, setDeactivateSuccessMessage] = useState("");
  // 일반 알림 모달 상태
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    iconType: "info" | "warning" | "error" | "success" | "question";
  }>({ isOpen: false, title: "", message: "", iconType: "info" });

  // 알림 모달 표시 헬퍼
  const showAlert = (
    title: string,
    message: string,
    iconType: "info" | "warning" | "error" | "success" | "question" = "info"
  ) => {
    setAlertModal({ isOpen: true, title, message, iconType });
  };

  // 내 가상매매 전략 목록 조회
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
    mutationFn: (params: { capital: number; name?: string }) =>
      autoTradingApi.activateAutoTrading({
        session_id: sessionId,
        // initial_capital 제거 - 백엔드에서 키움 계좌 잔고 자동 조회
        allocated_capital: params.capital,
        strategy_name: params.name,
      }),
    onSuccess: (data) => {
      // 커스텀 모달로 성공 메시지 표시
      setActivateSuccessMessage(data.message || "자동매매가 활성화되었습니다.");
      setShowActivateSuccess(true);
      queryClient.invalidateQueries({ queryKey: ["autoTradingStrategies"] });
      setIsActivating(false);
    },
    onError: (error: any) => {
      showAlert(
        "활성화 실패",
        error.response?.data?.detail || "가상매매 활성화에 실패했습니다.",
        "error"
      );
      setIsActivating(false);
    },
  });

  // 비활성화 mutation
  const deactivateMutation = useMutation({
    mutationFn: (params: { strategyId: string; mode: string }) =>
      autoTradingApi.deactivateAutoTrading(params.strategyId, {
        sell_all_positions: true,
        deactivation_mode: params.mode,
      }),
    onSuccess: (data) => {
      // 커스텀 모달로 성공 메시지 표시 (매도 정보 앞에 줄바꿈 추가)
      const message = (data.message || "자동매매가 비활성화되었습니다.").replace(" (매도:", "\n(매도:");
      setDeactivateSuccessMessage(message);
      setShowDeactivateSuccess(true);
      queryClient.invalidateQueries({ queryKey: ["autoTradingStrategies"] });
      setIsDeactivating(false);
      setShowDeactivateModal(false);
    },
    onError: (error: any) => {
      showAlert(
        "비활성화 실패",
        error.response?.data?.detail || "가상매매 비활성화에 실패했습니다.",
        "error"
      );
      setIsDeactivating(false);
    },
  });

  // 가상매매 활성화 버튼 클릭 시 키움증권 연동 상태 확인
  const handleActivate = async () => {
    if (sessionStatus?.toUpperCase() !== "COMPLETED") {
      showAlert("알림", "백테스트가 완료된 후에 활성화할 수 있습니다.", "warning");
      return;
    }

    // 키움증권 연동 상태 확인
    setIsCheckingKiwoom(true);
    try {
      const status = await kiwoomApi.getStatus();

      if (!status.is_connected) {
        // 증권 계좌 미연동 시 커스텀 모달 표시
        setShowKiwoomRequiredModal(true);
        return;
      }

      // 연동되어 있으면 기존 로직대로 모달창 열기
      setShowCapitalInput(true);
    } catch (error) {
      console.error("키움증권 연동 상태 확인 실패:", error);
      showAlert("확인 실패", "증권 계좌 연동 상태 확인에 실패했습니다. 다시 시도해주세요.", "error");
    } finally {
      setIsCheckingKiwoom(false);
    }
  };

  // 키움증권 연동 필요 모달에서 확인 클릭 시 마이페이지로 이동
  const handleKiwoomRequiredConfirm = () => {
    router.push("/mypage");
  };

  const handleConfirmActivate = () => {
    const capital = Number.parseFloat(allocatedCapital);

    if (Number.isNaN(capital) || capital <= 0) {
      showAlert("알림", "유효한 금액을 입력해주세요.", "warning");
      return;
    }

    if (capital < 1000000) {
      showAlert("알림", "최소 100만원 이상의 금액을 입력해주세요.", "warning");
      return;
    }

    setIsActivating(true);
    setShowCapitalInput(false);
    activateMutation.mutate({
      capital,
      name: strategyName.trim() || undefined
    });
  };

  const handleCancelInput = () => {
    setShowCapitalInput(false);
    setAllocatedCapital("50000000");
    setStrategyName("");
  };

  const handleDeactivate = async () => {
    if (!activeStrategy) return;

    try {
      // 비활성화 조건 확인
      const conditions = await autoTradingApi.checkDeactivationConditions(activeStrategy.strategy_id);
      setDeactivationConditions(conditions);
      setShowDeactivateModal(true);
    } catch (error: any) {
      showAlert(
        "확인 실패",
        error.response?.data?.detail || "비활성화 조건 확인에 실패했습니다.",
        "error"
      );
    }
  };

  const handleConfirmDeactivate = (mode: string) => {
    if (!activeStrategy) return;
    setIsDeactivating(true);
    deactivateMutation.mutate({ strategyId: activeStrategy.strategy_id, mode });
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
              증권사 연동 가상매매 {activeStrategy ? "(활성화됨)" : ""}
            </h2>
            <p className="text-sm text-text-muted mt-1">
              {activeStrategy
                ? "백테스트 전략을 기반으로 증권사 계좌와 연동되어 가상매매가 실행됩니다. (모의투자 전용)"
                : "백테스트 전략을 증권사와 연동하여 가상매매로 전환하세요. (모의투자 전용)"}
            </p>
          </div>

          {/* 오른쪽: 버튼 */}
          <div>
            {!activeStrategy ? (
              <button
                onClick={handleActivate}
                disabled={
                  isActivating || isCheckingKiwoom || sessionStatus?.toUpperCase() !== "COMPLETED"
                }
                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${sessionStatus?.toUpperCase() !== "COMPLETED"
                  ? "bg-gray-300 cursor-not-allowed"
                  : isActivating || isCheckingKiwoom
                    ? "bg-red-400 cursor-wait"
                    : "bg-red-500 hover:bg-red-600"
                  }`}
              >
                {isCheckingKiwoom ? "확인 중..." : isActivating ? "활성화 중..." : "가상매매 활성화"}
              </button>
            ) : (
              <button
                onClick={handleDeactivate}
                disabled={isDeactivating}
                className={`px-6 py-3 rounded-lg font-semibold text-white transition-colors ${isDeactivating
                  ? "bg-gray-400 cursor-wait"
                  : "bg-gray-500 hover:bg-gray-600"
                  }`}
              >
                {isDeactivating ? "비활성화 중..." : "가상매매 비활성화"}
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
              백테스트 전략에 할당할 가상매매 금액과 전략 이름을 입력해주세요.
            </p>

            <div className="mb-4">
              <label
                htmlFor="strategyName"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                전략 이름 (선택)
              </label>
              <input
                id="strategyName"
                type="text"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                placeholder="예: 꿀단지, 모멘텀전략 (미입력시 자동 생성)"
                maxLength={50}
              />
              <p className="text-xs text-gray-500 mt-1">
                미입력 시 &quot;전략명-날짜시간&quot; 형식으로 자동 생성됩니다
              </p>
            </div>

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

      {/* 비활성화 모달 */}
      {showDeactivateModal && deactivationConditions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              가상매매 비활성화
            </h3>

            {/* 현재 상태 표시 */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">보유 종목:</span>
                <span className="font-semibold">{deactivationConditions.position_count}개</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">장 상태:</span>
                <span className="font-semibold">
                  {deactivationConditions.is_market_hours ? "장 시간" : "장 마감"}
                </span>
              </div>
            </div>

            {/* 케이스 1: 보유 종목 0개 - 즉시 비활성화 */}
            {deactivationConditions.can_deactivate_immediately && (
              <>
                <p className="text-sm text-gray-700 mb-6">
                  현재 보유 중인 종목이 없습니다. 즉시 비활성화할 수 있습니다.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowDeactivateModal(false)}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => handleConfirmDeactivate("immediate")}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors disabled:bg-gray-400"
                  >
                    {isDeactivating ? "처리 중..." : "즉시 비활성화"}
                  </button>
                </div>
              </>
            )}

            {/* 케이스 2: 장 시간 + 보유 종목 있음 - 매도 후 비활성화 */}
            {deactivationConditions.can_sell_and_deactivate && (
              <>
                <p className="text-sm text-gray-700 mb-6">
                  현재 장 시간입니다. 보유 중인 {deactivationConditions.position_count}개 종목을 전량 매도하고 비활성화할 수 있습니다.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowDeactivateModal(false)}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => handleConfirmDeactivate("sell_and_deactivate")}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-red-500 text-white rounded-lg font-semibold hover:bg-red-600 transition-colors disabled:bg-gray-400"
                  >
                    {isDeactivating ? "매도 중..." : "매도 후 비활성화"}
                  </button>
                </div>
              </>
            )}

            {/* 케이스 3: 장 마감 + 보유 종목 있음 - 예약 매도 또는 보유 */}
            {deactivationConditions.needs_scheduled_sell && (
              <>
                <p className="text-sm text-gray-700 mb-4">
                  현재 장 마감 시간입니다. 보유 중인 {deactivationConditions.position_count}개 종목이 있습니다.
                </p>
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                  <p className="text-sm text-yellow-800">
                    <strong>주의:</strong> 장 마감 시간에는 즉시 매도할 수 없습니다. 예약 매도를 선택하면 다음 장 시작 시(09:00) 자동으로 매도 후 비활성화됩니다.
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowDeactivateModal(false)}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => handleConfirmDeactivate("scheduled_sell")}
                    disabled={isDeactivating}
                    className="flex-1 px-4 py-3 bg-orange-500 text-white rounded-lg font-semibold hover:bg-orange-600 transition-colors disabled:bg-gray-400"
                  >
                    {isDeactivating ? "예약 중..." : "매도 예약"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* 키움증권 연동 필요 모달 */}
      <ConfirmModal
        isOpen={showKiwoomRequiredModal}
        onClose={() => setShowKiwoomRequiredModal(false)}
        onConfirm={handleKiwoomRequiredConfirm}
        title="증권 계좌 등록 필요"
        message={`가상매매를 활성화하려면 키움증권 계좌 연동이 필요합니다.\n마이페이지에서 증권 계좌를 등록하시겠습니까?`}
        confirmText="계좌 등록하기"
        cancelText="취소"
        iconType="warning"
      />

      {/* 가상매매 활성화 성공 모달 */}
      <ConfirmModal
        isOpen={showActivateSuccess}
        onClose={() => setShowActivateSuccess(false)}
        onConfirm={() => setShowActivateSuccess(false)}
        title={activateSuccessMessage || "자동매매가 활성화되었습니다."}
        message=""
        confirmText="확인"
        iconType="success"
        alertOnly
      />

      {/* 가상매매 비활성화 성공 모달 */}
      <ConfirmModal
        isOpen={showDeactivateSuccess}
        onClose={() => setShowDeactivateSuccess(false)}
        onConfirm={() => setShowDeactivateSuccess(false)}
        title={deactivateSuccessMessage || "자동매매가 비활성화되었습니다."}
        message=""
        confirmText="확인"
        iconType="success"
        alertOnly
      />

      {/* 일반 알림 모달 */}
      <ConfirmModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        onConfirm={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        title={alertModal.title}
        message={alertModal.message}
        confirmText="확인"
        iconType={alertModal.iconType}
        alertOnly
      />
    </>
  );
}
