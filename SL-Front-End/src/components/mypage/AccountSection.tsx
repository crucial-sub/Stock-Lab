"use client";

import { ConfirmModal } from "@/components/modal/ConfirmModal";
import { KiwoomConnectModal } from "@/components/modal/KiwoomConnectModal";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { kiwoomApi } from "@/lib/api/kiwoom";
import { formatAmount, formatPercent, getProfitColor } from "@/lib/formatters";
import { useCallback, useEffect, useState } from "react";

export function AccountSection() {
  const [isKiwoomConnected, setIsKiwoomConnected] = useState(false);
  const [isKiwoomModalOpen, setIsKiwoomModalOpen] = useState(false);
  const [accountBalance, setAccountBalance] = useState<unknown>(null);
  const [allocatedCapital, setAllocatedCapital] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  // 연동 해제 관련 모달 상태
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [showDisconnectSuccess, setShowDisconnectSuccess] = useState(false);
  const [disconnectError, setDisconnectError] = useState<string | null>(null);
  // 연동 성공 모달 상태
  const [showConnectSuccess, setShowConnectSuccess] = useState(false);

  const fetchAccountBalance = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await kiwoomApi.getAccountBalance();
      setAccountBalance(response.data);

      // 키움증권 연동 할당 금액 조회
      try {
        const dashboardData = await autoTradingApi.getPortfolioDashboard();
        setAllocatedCapital(Number((dashboardData as any).total_allocated_capital) || 0);
      } catch (err) {
        console.warn("키움증권 연동 가상매매 할당 금액 조회 실패:", err);
      }
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
    // 연동 성공 모달 표시
    setShowConnectSuccess(true);
  };

  // 연동 해제 버튼 클릭 시 확인 모달 표시
  const handleDisconnect = () => {
    setShowDisconnectConfirm(true);
  };

  // 연동 해제 확인 모달에서 확인 클릭 시 실제 해제 수행
  const handleConfirmDisconnect = async () => {
    setShowDisconnectConfirm(false);

    try {
      setIsDisconnecting(true);
      await kiwoomApi.deleteCredentials();
      setIsKiwoomConnected(false);
      setAccountBalance(null);
      setAllocatedCapital(0);
      // 성공 모달 표시
      setShowDisconnectSuccess(true);
    } catch (err: unknown) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "연동 해제에 실패했습니다.";
      setDisconnectError(errorMessage);
    } finally {
      setIsDisconnecting(false);
    }
  };

  return (
    <section className="rounded-[12px] p-7 shadow-elev-card backdrop-blur bg-[#1822340D]">
      <div className="flex flex-wrap items-center justify-between">
        <div>
          <p className="text-[0.75rem] font-normal uppercase tracking-widest text-[#646464]">Account</p>
          <h2 className="text-[1.5rem] font-semibold text-[#000000]">연동 계좌 관리</h2>
        </div>
        {!isKiwoomConnected ? (
          <button
            onClick={() => setIsKiwoomModalOpen(true)}
            className="rounded-full bg-[#AC64FF] px-5 py-2 text-[0.875rem] font-semibold text-white transition hover:bg-brand-purple/80"
          >
            계좌 연동하기
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={fetchAccountBalance}
              disabled={isLoading || isDisconnecting}
              className="rounded-full bg-[#5d6bf5] px-5 py-2 text-[0.875rem] font-semibold text-white transition hover:bg-[#5d6bf5]/80 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "조회 중..." : "새로고침"}
            </button>
            <button
              onClick={handleDisconnect}
              disabled={isLoading || isDisconnecting}
              className="rounded-full bg-[#FF6464] px-5 py-2 text-[0.875rem] font-semibold text-white transition hover:bg-[#FF6464]/80 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isDisconnecting ? "해제 중..." : "연동 해제"}
            </button>
          </div>
        )}
      </div>

      {!isKiwoomConnected ? (
        <div className="mt-8 rounded-[12px] border border-dashed border-[#C8C8C8] bg-[#ffffffCC] p-10 text-center text-muted">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-elev-card-soft">
            <svg
              className="h-8 w-8 text-[#9097c2]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 7v4h4m1 0a8 8 0 11-8-8 8 8 0 018 8z"
              />
            </svg>
          </div>
          <p className="text-[1.125rem] font-semibold text-[#000000]">키움증권 연동이 필요합니다</p>
          <p className="mt-2 text-[0.875rem]">증권사 연동 후 실시간 계좌 잔고와 수익률을 한눈에 확인할 수 있습니다.</p>
        </div>
      ) : (
        <div className="mt-8 space-y-6">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded-full bg-[#eff2ff] px-4 py-1 font-semibold text-[#5d6bf5]">
              키움증권
            </span>
            <span className="rounded-full bg-[#e1fbef] px-4 py-1 font-semibold text-[#28b77c]">
              연동됨 (모의투자)
            </span>
          </div>

          {error && (
            <div className="rounded-2xl border border-[#ffb3be] bg-[#fff1f3] p-4 text-sm text-[#d8435d]">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="py-12 text-center">
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-2 border-[#c4cbff] border-t-[#6f7bff]" />
              <p className="mt-4 text-sm text-[#6d749b]">잔고 정보를 불러오는 중...</p>
            </div>
          ) : (
            <>
              <div className="rounded-3xl border border-[#dee4f6] bg-[#f8faff] p-5 shadow-[0_10px_30px_rgba(32,38,74,0.08)]">
                <p className="text-xs font-semibold uppercase tracking-wider text-[#98a0c6]">
                  예수금
                </p>
                <p className="mt-2 text-2xl font-bold text-[#1f2143]">
                  {formatAmount(
                    (accountBalance as { cash?: { balance?: string | number } }).cash?.balance || 0
                  )}
                  원
                </p>
              </div>

              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div className="rounded-3xl border border-[#d6def8] bg-white p-5 shadow-[0_10px_25px_rgba(32,38,74,0.08)]">
                  <p className="text-xs font-medium text-[#9da5c9]">평가액</p>
                  <p className="mt-2 text-xl font-bold text-[#1f2143]">
                    {(() => {
                      const totEvltAmt = (accountBalance as { holdings?: { tot_evlt_amt?: string | number } }).holdings?.tot_evlt_amt || 0;
                      const cashBalance = (accountBalance as { cash?: { balance?: string | number } }).cash?.balance || 0;

                      const parseValue = (val: string | number): number => {
                        if (typeof val === "string") {
                          return Number.parseInt(val.replace(/,/g, ""), 10) || 0;
                        }
                        return val || 0;
                      };

                      // 전체 평가액에서 키움증권 연동 가상매매 할당 금액 제외
                      const totalEval = parseValue(totEvltAmt) + parseValue(cashBalance);
                      return formatAmount(totalEval - allocatedCapital);
                    })()}
                    원
                  </p>
                </div>
                <div className="rounded-3xl border border-[#d6def8] bg-white p-5 shadow-[0_10px_25px_rgba(32,38,74,0.08)]">
                  <p className="text-xs font-medium text-[#9da5c9]">평가손익</p>
                  <p
                    className={`mt-2 text-xl font-bold ${getProfitColor(
                      (accountBalance as { holdings?: { tot_evlt_pl?: string | number } }).holdings
                        ?.tot_evlt_pl || 0
                    )}`}
                  >
                    {formatAmount(
                      (accountBalance as { holdings?: { tot_evlt_pl?: string | number } }).holdings
                        ?.tot_evlt_pl || 0
                    )}
                    원
                  </p>
                </div>
                <div className="rounded-3xl border border-[#d6def8] bg-white p-5 shadow-[0_10px_25px_rgba(32,38,74,0.08)]">
                  <p className="text-xs font-medium text-[#9da5c9]">수익률</p>
                  <p
                    className={`mt-2 text-xl font-bold ${getProfitColor(
                      (accountBalance as { holdings?: { tot_prft_rt?: string | number } }).holdings
                        ?.tot_prft_rt || 0
                    )}`}
                  >
                    {formatPercent(
                      (accountBalance as { holdings?: { tot_prft_rt?: string | number } }).holdings
                        ?.tot_prft_rt || 0
                    )}
                    %
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      <KiwoomConnectModal
        isOpen={isKiwoomModalOpen}
        onClose={() => setIsKiwoomModalOpen(false)}
        onSuccess={handleKiwoomSuccess}
      />

      {/* 연동 해제 확인 모달 */}
      <ConfirmModal
        isOpen={showDisconnectConfirm}
        onClose={() => setShowDisconnectConfirm(false)}
        onConfirm={handleConfirmDisconnect}
        title="키움증권 연동을 해제하시겠습니까?"
        message={`해제 시 가상매매 기능을 사용할 수 없습니다.\n활성화된 가상매매 전략이 있다면 먼저 비활성화해주세요.`}
        confirmText="확인"
        cancelText="취소"
        iconType="warning"
      />

      {/* 연동 해제 성공 모달 */}
      <ConfirmModal
        isOpen={showDisconnectSuccess}
        onClose={() => setShowDisconnectSuccess(false)}
        onConfirm={() => setShowDisconnectSuccess(false)}
        title="키움증권 연동이 해제되었습니다."
        message=""
        confirmText="확인"
        iconType="success"
        alertOnly
      />

      {/* 연동 해제 에러 모달 */}
      <ConfirmModal
        isOpen={!!disconnectError}
        onClose={() => setDisconnectError(null)}
        onConfirm={() => setDisconnectError(null)}
        title="연동 해제 실패"
        message={disconnectError || ""}
        confirmText="확인"
        iconType="error"
        alertOnly
      />

      {/* 연동 성공 모달 */}
      <ConfirmModal
        isOpen={showConnectSuccess}
        onClose={() => setShowConnectSuccess(false)}
        onConfirm={() => setShowConnectSuccess(false)}
        title="키움증권 연동이 완료되었습니다!"
        message=""
        confirmText="확인"
        iconType="success"
        alertOnly
      />
    </section>
  );
}
