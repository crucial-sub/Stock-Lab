"use client";

import { useState, useCallback, useEffect } from "react";
import { KiwoomConnectModal } from "@/components/modal/KiwoomConnectModal";
import { kiwoomApi } from "@/lib/api/kiwoom";

export function AccountSection() {
  const [isKiwoomConnected, setIsKiwoomConnected] = useState(false);
  const [isKiwoomModalOpen, setIsKiwoomModalOpen] = useState(false);
  const [accountBalance, setAccountBalance] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccountBalance = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await kiwoomApi.getAccountBalance();
      setAccountBalance(response.data);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "계좌 잔고 조회에 실패했습니다.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const checkKiwoomStatus = useCallback(async () => {
    try {
      const status = await kiwoomApi.getStatus();
      setIsKiwoomConnected(status.is_connected);

      if (status.is_connected) {
        fetchAccountBalance();
      }
    } catch (error) {
      console.error("키움증권 연동 상태 확인 실패:", error);
    }
  }, []);

  useEffect(() => {
    checkKiwoomStatus();
  }, [checkKiwoomStatus]);

  const handleKiwoomSuccess = () => {
    setIsKiwoomConnected(true);
    fetchAccountBalance();
  };

  const formatAmount = (value: string | number): string => {
    const num = typeof value === "string" ? Number.parseInt(value, 10) : value;
    if (Number.isNaN(num)) return "0";
    return num.toLocaleString("ko-KR");
  };

  const formatPercent = (value: string | number): string => {
    const num = typeof value === "string" ? Number.parseFloat(value) : value;
    if (Number.isNaN(num)) return "0.00";
    return num.toFixed(2);
  };

  const getProfitColor = (value: string | number): string => {
    const num = typeof value === "string" ? Number.parseFloat(value) : value;
    if (num > 0) return "text-price-up";
    if (num < 0) return "text-price-down";
    return "text-text-muted";
  };

  return (
    <div className="quant-shell mb-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-body">연동 계좌 관리</h2>

        {!isKiwoomConnected && (
          <button
            onClick={() => setIsKiwoomModalOpen(true)}
            className="px-6 py-2 bg-button-primary-soft text-brand rounded-md hover:bg-brand hover:text-base-0 transition-colors"
          >
            계좌 연동하기
          </button>
        )}
      </div>

      {!isKiwoomConnected ? (
        <div className="p-12 text-center">
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-text-muted"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <p className="text-text-muted text-lg mb-4">
            키움증권 연동이 필요합니다
          </p>
          <p className="text-text-muted text-sm">
            증권사 연동 후 실시간 계좌 잔고를 확인할 수 있습니다
          </p>
        </div>
      ) : (
        <div className="p-6">
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              <span className="text-sm text-text-body font-medium">
                키움증권 연동됨 (모의투자)
              </span>
            </div>
            <button
              onClick={fetchAccountBalance}
              disabled={isLoading}
              className="px-4 py-2 bg-button-primary-soft text-brand text-sm rounded-md hover:bg-brand hover:text-base-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "조회 중..." : "새로고침"}
            </button>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-price-up border border-price-down rounded-md">
              <p className="text-sm text-price-down">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="py-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto" />
              <p className="mt-4 text-text-muted">잔고 정보를 불러오는 중...</p>
            </div>
          ) : accountBalance ? (
            <div className="space-y-6">
              {/* 예수금 섹션 */}
              <div className="bg-base-soft-blue p-6 rounded-lg border border-brand-soft">
                <h3 className="text-lg font-bold text-text-body mb-4">예수금</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-base-0 p-4 rounded-md shadow-elev-card-soft">
                    <p className="text-xs text-text-muted mb-1">예수금</p>
                    <p className="text-xl font-bold text-text-body">
                      {formatAmount((accountBalance as { cash?: { balance?: string | number } }).cash?.balance || 0)}원
                    </p>
                  </div>
                  <div className="bg-base-0 p-4 rounded-md shadow-elev-card-soft">
                    <p className="text-xs text-text-muted mb-1">출금가능금액</p>
                    <p className="text-xl font-bold text-positive">
                      {formatAmount((accountBalance as { cash?: { withdrawable?: string | number } }).cash?.withdrawable || 0)}원
                    </p>
                  </div>
                  <div className="bg-base-0 p-4 rounded-md shadow-elev-card-soft">
                    <p className="text-xs text-text-muted mb-1">주문가능금액</p>
                    <p className="text-xl font-bold text-brand">
                      {formatAmount((accountBalance as { cash?: { orderable?: string | number } }).cash?.orderable || 0)}원
                    </p>
                  </div>
                </div>
              </div>

              {/* 보유 종목 요약 */}
              <div className="bg-base-0 p-6 rounded-lg border border-surface shadow-elev-card-soft">
                <h3 className="text-lg font-bold text-text-body mb-4">보유 종목 요약</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 bg-surface rounded-md">
                    <p className="text-xs text-text-muted mb-1">총 평가금액</p>
                    <p className="text-lg font-bold text-text-body">
                      {formatAmount((accountBalance as { holdings?: { tot_evlt_amt?: string | number } }).holdings?.tot_evlt_amt || 0)}원
                    </p>
                  </div>
                  <div className="p-3 bg-surface rounded-md">
                    <p className="text-xs text-text-muted mb-1">총 평가손익</p>
                    <p className={`text-lg font-bold ${getProfitColor((accountBalance as { holdings?: { tot_evlt_pl?: string | number } }).holdings?.tot_evlt_pl || 0)}`}>
                      {formatAmount((accountBalance as { holdings?: { tot_evlt_pl?: string | number } }).holdings?.tot_evlt_pl || 0)}원
                    </p>
                  </div>
                  <div className="p-3 bg-surface rounded-md">
                    <p className="text-xs text-text-muted mb-1">총 수익률</p>
                    <p className={`text-lg font-bold ${getProfitColor((accountBalance as { holdings?: { tot_prft_rt?: string | number } }).holdings?.tot_prft_rt || 0)}`}>
                      {formatPercent((accountBalance as { holdings?: { tot_prft_rt?: string | number } }).holdings?.tot_prft_rt || 0)}%
                    </p>
                  </div>
                  <div className="p-3 bg-surface rounded-md">
                    <p className="text-xs text-text-muted mb-1">총 매입금액</p>
                    <p className="text-lg font-bold text-text-body">
                      {formatAmount((accountBalance as { holdings?: { tot_pur_amt?: string | number } }).holdings?.tot_pur_amt || 0)}원
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center">
              <p className="text-text-muted">
                잔고 정보를 불러오려면 새로고침 버튼을 클릭하세요
              </p>
            </div>
          )}
        </div>
      )}

      <KiwoomConnectModal
        isOpen={isKiwoomModalOpen}
        onClose={() => setIsKiwoomModalOpen(false)}
        onSuccess={handleKiwoomSuccess}
      />
    </div>
  );
}
