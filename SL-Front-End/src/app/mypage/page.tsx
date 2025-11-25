"use client";

import { useCallback, useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { KiwoomConnectModal } from "@/components/modal/KiwoomConnectModal";
import { kiwoomApi } from "@/lib/api/kiwoom";

export default function MyPage() {
  const [isKiwoomConnected, setIsKiwoomConnected] = useState(false);
  const [isKiwoomModalOpen, setIsKiwoomModalOpen] = useState(false);
  const [accountBalance, setAccountBalance] = useState<any>(null);
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

      // 연동되어 있으면 자동으로 잔고 조회
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

  // 금액 포맷팅 함수
  const formatAmount = (value: string | number): string => {
    if (value === undefined || value === null) return "0";
    const num = typeof value === "string" ? parseInt(value, 10) : value;
    if (Number.isNaN(num)) return "0";
    return num.toLocaleString("ko-KR");
  };

  // 퍼센트 포맷팅 함수
  const formatPercent = (value: string | number): string => {
    if (value === undefined || value === null) return "0.00";
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (Number.isNaN(num)) return "0.00";
    return num.toFixed(2);
  };

  // 손익 색상 결정
  const getProfitColor = (value: string | number): string => {
    const num = typeof value === "string" ? parseFloat(value) : value;
    if (num > 0) return "text-red-500";
    if (num < 0) return "text-blue-500";
    return "text-gray-500";
  };

  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8 px-6">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-text-primary">나의 잔고</h1>

          {!isKiwoomConnected && (
            <button
              onClick={() => setIsKiwoomModalOpen(true)}
              className="px-6 py-2 bg-primary-main text-white rounded-md hover:bg-primary-dark transition-colors"
            >
              증권사 연동하기
            </button>
          )}
        </div>

        <div className="quant-shell">
          {!isKiwoomConnected ? (
            <div className="p-12 text-center">
              <div className="mb-4">
                <svg
                  className="mx-auto h-16 w-16 text-text-tertiary"
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
              <p className="text-text-tertiary text-lg mb-4">
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
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-text-secondary font-medium">
                    키움증권 연동됨 (모의투자)
                  </span>
                </div>
                <button
                  onClick={fetchAccountBalance}
                  disabled={isLoading}
                  className="px-4 py-2 bg-primary-main text-white text-sm rounded-md hover:bg-primary-dark transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isLoading ? "조회 중..." : "🔄 새로고침"}
                </button>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-600">❌ {error}</p>
                </div>
              )}

              {isLoading ? (
                <div className="py-12 text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-main mx-auto"></div>
                  <p className="mt-4 text-text-secondary">
                    잔고 정보를 불러오는 중...
                  </p>
                </div>
              ) : accountBalance ? (
                <div className="space-y-6">
                  {/* 예수금 섹션 */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                      💰 예수금
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-white p-4 rounded-md shadow-sm">
                        <p className="text-xs text-gray-500 mb-1">예수금</p>
                        <p className="text-xl font-bold text-gray-900">
                          {formatAmount(accountBalance.cash?.balance || 0)}원
                        </p>
                      </div>
                      <div className="bg-white p-4 rounded-md shadow-sm">
                        <p className="text-xs text-gray-500 mb-1">
                          출금가능금액
                        </p>
                        <p className="text-xl font-bold text-green-600">
                          {formatAmount(accountBalance.cash?.withdrawable || 0)}
                          원
                        </p>
                      </div>
                      <div className="bg-white p-4 rounded-md shadow-sm">
                        <p className="text-xs text-gray-500 mb-1">
                          주문가능금액
                        </p>
                        <p className="text-xl font-bold text-blue-600">
                          {formatAmount(accountBalance.cash?.orderable || 0)}원
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className="bg-white/50 p-3 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">D+1 예상</p>
                        <p className="text-sm font-semibold text-gray-700">
                          {formatAmount(accountBalance.cash?.d1_estimated || 0)}
                          원
                        </p>
                      </div>
                      <div className="bg-white/50 p-3 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">D+2 예상</p>
                        <p className="text-sm font-semibold text-gray-700">
                          {formatAmount(accountBalance.cash?.d2_estimated || 0)}
                          원
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 보유 종목 섹션 */}
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                      📊 보유 종목
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="p-3 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">
                          총 평가금액
                        </p>
                        <p className="text-lg font-bold text-gray-900">
                          {formatAmount(
                            accountBalance.holdings?.tot_evlt_amt || 0,
                          )}
                          원
                        </p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">
                          총 평가손익
                        </p>
                        <p
                          className={`text-lg font-bold ${getProfitColor(accountBalance.holdings?.tot_evlt_pl || 0)}`}
                        >
                          {formatAmount(
                            accountBalance.holdings?.tot_evlt_pl || 0,
                          )}
                          원
                        </p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">총 수익률</p>
                        <p
                          className={`text-lg font-bold ${getProfitColor(accountBalance.holdings?.tot_prft_rt || 0)}`}
                        >
                          {formatPercent(
                            accountBalance.holdings?.tot_prft_rt || 0,
                          )}
                          %
                        </p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded-md">
                        <p className="text-xs text-gray-500 mb-1">
                          총 매입금액
                        </p>
                        <p className="text-lg font-bold text-gray-900">
                          {formatAmount(
                            accountBalance.holdings?.tot_pur_amt || 0,
                          )}
                          원
                        </p>
                      </div>
                    </div>

                    {accountBalance.holdings?.acnt_evlt_remn_indv_tot?.length >
                    0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="p-2 text-left">종목명</th>
                              <th className="p-2 text-right">보유수량</th>
                              <th className="p-2 text-right">평균단가</th>
                              <th className="p-2 text-right">현재가</th>
                              <th className="p-2 text-right">평가금액</th>
                              <th className="p-2 text-right">손익</th>
                            </tr>
                          </thead>
                          <tbody>
                            {accountBalance.holdings.acnt_evlt_remn_indv_tot.map(
                              (stock: any, idx: number) => (
                                <tr key={idx} className="border-b">
                                  <td className="p-2">{stock.stk_nm}</td>
                                  <td className="p-2 text-right">
                                    {formatAmount(stock.qty)}
                                  </td>
                                  <td className="p-2 text-right">
                                    {formatAmount(stock.avg_pric)}
                                  </td>
                                  <td className="p-2 text-right">
                                    {formatAmount(stock.cur_pric)}
                                  </td>
                                  <td className="p-2 text-right">
                                    {formatAmount(stock.evlt_amt)}
                                  </td>
                                  <td
                                    className={`p-2 text-right font-semibold ${getProfitColor(stock.evlt_pl)}`}
                                  >
                                    {formatAmount(stock.evlt_pl)}
                                  </td>
                                </tr>
                              ),
                            )}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="py-8 text-center text-gray-500">
                        <p className="text-2xl mb-2">📭</p>
                        <p>보유 종목이 없습니다</p>
                      </div>
                    )}
                  </div>

                  {/* 미체결/체결 섹션 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        ⏳ 미체결
                      </h3>
                      {accountBalance.unexecuted?.oso?.length > 0 ? (
                        <div className="space-y-2">
                          {accountBalance.unexecuted.oso.map(
                            (order: any, idx: number) => (
                              <div
                                key={idx}
                                className="p-3 bg-gray-50 rounded-md text-sm"
                              >
                                <p className="font-semibold">{order.stk_nm}</p>
                                <p className="text-gray-600">
                                  수량: {formatAmount(order.qty)} / 가격:{" "}
                                  {formatAmount(order.pric)}원
                                </p>
                              </div>
                            ),
                          )}
                        </div>
                      ) : (
                        <div className="py-8 text-center text-gray-500">
                          <p>미체결 주문이 없습니다</p>
                        </div>
                      )}
                    </div>

                    <div className="bg-white p-6 rounded-lg border border-gray-200">
                      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        ✅ 체결
                      </h3>
                      {accountBalance.executed?.cntr?.length > 0 ? (
                        <div className="space-y-2">
                          {accountBalance.executed.cntr.map(
                            (order: any, idx: number) => (
                              <div
                                key={idx}
                                className="p-3 bg-gray-50 rounded-md text-sm"
                              >
                                <p className="font-semibold">{order.stk_nm}</p>
                                <p className="text-gray-600">
                                  수량: {formatAmount(order.qty)} / 가격:{" "}
                                  {formatAmount(order.pric)}원
                                </p>
                              </div>
                            ),
                          )}
                        </div>
                      ) : (
                        <div className="py-8 text-center text-gray-500">
                          <p>체결 내역이 없습니다</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center">
                  <p className="text-text-tertiary">
                    잔고 정보를 불러오려면 새로고침 버튼을 클릭하세요
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <KiwoomConnectModal
        isOpen={isKiwoomModalOpen}
        onClose={() => setIsKiwoomModalOpen(false)}
        onSuccess={handleKiwoomSuccess}
      />
    </ProtectedRoute>
  );
}
