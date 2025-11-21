"use client";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { autoTradingApi } from "@/lib/api/auto-trading";
import type { AutoTradingStatusResponse } from "@/lib/api/auto-trading";

interface AutoTradingStatusPageClientProps {
  strategyId: string;
  initialData: AutoTradingStatusResponse | null;
}

export function AutoTradingStatusPageClient({
  strategyId,
  initialData,
}: AutoTradingStatusPageClientProps) {
  const router = useRouter();

  // 자동매매 상태 조회 (5초마다 자동 갱신)
  const { data: statusData, isLoading } = useQuery({
    queryKey: ["autoTradingStatus", strategyId],
    queryFn: () => autoTradingApi.getAutoTradingStatus(strategyId),
    initialData: initialData || undefined,
    refetchInterval: 5000, // 5초마다 갱신
  });

  if (isLoading || !statusData) {
    return (
      <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
          <div className="h-64 bg-gray-200 rounded mb-6"></div>
        </div>
      </main>
    );
  }

  const { strategy, positions, today_trades, latest_performance } = statusData;

  // 키움 API 실제 데이터 우선 사용
  const useKiwoomData = strategy.kiwoom_total_eval != null;

  // 총 평가액 (키움 API 데이터 우선, 없으면 계산)
  const stockValue = useKiwoomData
    ? Number(strategy.kiwoom_total_eval)
    : positions.reduce(
        (sum, pos) => sum + Number(pos.current_price || pos.avg_buy_price) * pos.quantity,
        0
      ) + Number(strategy.cash_balance);

  // 총 매수금액 계산 (평단가 기준) - 할당 자본 사용
  const totalBuyValue = Number(strategy.allocated_capital);

  // 평가손익 (키움 API 데이터 우선)
  const totalProfit = useKiwoomData
    ? Number(strategy.kiwoom_total_profit || 0)
    : stockValue - totalBuyValue;

  // 수익률 (키움 API 데이터 우선)
  const totalReturn = useKiwoomData
    ? Number(strategy.kiwoom_total_profit_rate || 0)
    : totalBuyValue > 0
      ? (totalProfit / totalBuyValue) * 100
      : 0;

  return (
    <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <button
            onClick={() => router.back()}
            className="text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            ← 돌아가기
          </button>
          <h1 className="text-3xl font-bold">🤖 자동매매 실시간 모니터링</h1>
          <p className="text-sm text-gray-500 mt-1">
            마지막 실행: {strategy.last_executed_at || "없음"}
          </p>
        </div>
        <div
          className={`px-4 py-2 rounded-lg font-semibold ${
            strategy.is_active
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-700"
          }`}
        >
          {strategy.is_active ? "✅ 활성화" : "⏸️ 비활성화"}
        </div>
      </div>

      {/* 현재 상태 대시보드 */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">총 평가액</p>
          <p className="text-2xl font-bold">
            {Math.round(stockValue).toLocaleString()}원
          </p>
          <p
            className={`text-sm font-semibold ${totalProfit >= 0 ? "text-red-500" : "text-blue-500"}`}
          >
            {totalProfit >= 0 ? "+" : ""}
            {Math.round(totalProfit).toLocaleString()}원 ({totalReturn >= 0 ? "+" : ""}
            {totalReturn.toFixed(2)}%)
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">현금 잔고</p>
          <p className="text-2xl font-bold">
            {Math.round(strategy.cash_balance).toLocaleString()}원
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">보유 종목</p>
          <p className="text-2xl font-bold">{positions.length}개</p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">당일 매매</p>
          <p className="text-2xl font-bold">{today_trades.length}건</p>
        </div>
      </div>

      {/* 보유 종목 */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b">
          <h2 className="text-xl font-bold">💼 보유 종목</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  종목코드
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  종목명
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  수량
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  평단가
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  현재가
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  수익률
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  보유일
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    보유 종목이 없습니다.
                  </td>
                </tr>
              ) : (
                positions.map((pos) => {
                  const profitRate = Number(pos.unrealized_profit_pct || 0);
                  return (
                    <tr key={pos.position_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{pos.stock_code}</td>
                      <td className="px-4 py-3 text-sm">{pos.stock_name}</td>
                      <td className="px-4 py-3 text-sm text-right">
                        {pos.quantity.toLocaleString()}주
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        {Math.round(Number(pos.avg_buy_price)).toLocaleString()}원
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        {Math.round(
                          Number(pos.current_price || pos.avg_buy_price)
                        ).toLocaleString()}
                        원
                      </td>
                      <td
                        className={`px-4 py-3 text-sm text-right font-semibold ${
                          profitRate >= 0 ? "text-red-500" : "text-blue-500"
                        }`}
                      >
                        {profitRate >= 0 ? "+" : ""}
                        {profitRate.toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        {pos.hold_days}일
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 오늘의 매매 내역 */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b">
          <h2 className="text-xl font-bold">📝 오늘의 매매 내역</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  시간
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  구분
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  종목명
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  수량
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  가격
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  금액
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  손익
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {today_trades.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    오늘 매매 내역이 없습니다.
                  </td>
                </tr>
              ) : (
                today_trades.map((trade) => (
                  <tr key={trade.trade_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{trade.trade_time}</td>
                    <td className="px-4 py-3 text-sm">
                      <span
                        className={`px-2 py-1 rounded text-xs font-semibold ${
                          trade.trade_type === "BUY"
                            ? "bg-red-100 text-red-700"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {trade.trade_type === "BUY" ? "매수" : "매도"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{trade.stock_name}</td>
                    <td className="px-4 py-3 text-sm text-right">
                      {trade.quantity.toLocaleString()}주
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      {Math.round(trade.price).toLocaleString()}원
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      {Math.round(trade.amount).toLocaleString()}원
                    </td>
                    <td
                      className={`px-4 py-3 text-sm text-right font-semibold ${
                        trade.profit && trade.profit > 0
                          ? "text-red-500"
                          : trade.profit && trade.profit < 0
                            ? "text-blue-500"
                            : ""
                      }`}
                    >
                      {trade.profit
                        ? `${trade.profit > 0 ? "+" : ""}${Math.round(trade.profit).toLocaleString()}원`
                        : "-"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 다음 리밸런싱 일정 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-2">🎯 다음 리밸런싱 예정</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• 오전 7시: 매수/매도 종목 자동 선정</li>
          <li>• 오전 9시: 실제 매수/매도 주문 실행</li>
          <li>• 리밸런싱 주기: {strategy.rebalance_frequency}</li>
        </ul>
      </div>
    </main>
  );
}
