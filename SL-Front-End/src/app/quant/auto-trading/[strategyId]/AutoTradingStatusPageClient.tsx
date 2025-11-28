"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { autoTradingApi } from "@/lib/api/auto-trading";
import type { AutoTradingStatusResponse } from "@/lib/api/auto-trading";
import { getBacktestSettings } from "@/lib/api/backtest";
import {
  PageHeader,
  StatisticsSection,
  AutoTradingSection,
} from "@/components/quant/result/sections";
import { StatisticsTabWrapper } from "@/components/quant/result/StatisticsTabWrapper";
import { TradingHistoryTab } from "@/components/quant/result/TradingHistoryTab";
import { StockDetailModal } from "@/components/modal/StockDetailModal";

interface AutoTradingStatusPageClientProps {
  strategyId: string;
  initialData: AutoTradingStatusResponse | null;
}

type TabType = "stockInfo" | "statistics" | "history" | "settings";

// 전략 설정 용어 한국어 번역
const translateTerm = (term: string | undefined | null): string => {
  if (!term) return "-";

  const translations: Record<string, string> = {
    // 포지션 사이징
    "EQUAL_WEIGHT": "동일 비중",
    "equal_weight": "동일 비중",

    // 사용 방식
    "SCREENING": "스크리닝",
    "screening": "스크리닝",
    "SCORING": "점수화",
    "scoring": "점수화",

    // 방향
    "POSITIVE": "상승 방향",
    "positive": "상승 방향",
    "NEGATIVE": "하락 방향",
    "negative": "하락 방향",

    // 리밸런싱 주기
    "DAILY": "매일",
    "daily": "매일",
    "WEEKLY": "매주",
    "weekly": "매주",
    "MONTHLY": "매월",
    "monthly": "매월",
    "QUARTERLY": "분기별",
    "quarterly": "분기별",

    // 연산자
    ">": "초과",
    ">=": "이상",
    "<": "미만",
    "<=": "이하",
    "==": "같음",

    // 유니버스 타입
    "ALL": "전체",
    "KOSPI": "코스피",
    "KOSDAQ": "코스닥",

    // 시가총액 필터
    "LARGE": "대형주",
    "MID": "중형주",
    "SMALL": "소형주",
  };

  return translations[term] || term;
};

export function AutoTradingStatusPageClient({
  strategyId,
  initialData,
}: AutoTradingStatusPageClientProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("stockInfo");
  const [selectedStock, setSelectedStock] = useState<{
    name: string;
    code: string;
  } | null>(null);

  // 가상매매 상태 조회 (5초마다 자동 갱신)
  const { data: statusData, isLoading } = useQuery({
    queryKey: ["autoTradingStatus", strategyId],
    queryFn: () => autoTradingApi.getAutoTradingStatus(strategyId),
    initialData: initialData || undefined,
    refetchInterval: 5000, // 5초마다 갱신
  });

  // 백테스트 설정 조회 (원본 시뮬레이션의 설정 정보)
  const { data: backtestSettings } = useQuery({
    queryKey: ["backtestSettings", statusData?.strategy.simulation_session_id],
    queryFn: () => getBacktestSettings(statusData!.strategy.simulation_session_id),
    enabled: !!statusData?.strategy.simulation_session_id,
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

  // 할당 자본 (초기 투자금)
  const allocatedCapital = Number(strategy.allocated_capital);

  // 매수금액 합계 계산
  const totalBuyValue = positions.reduce(
    (sum, pos) => sum + pos.avg_buy_price * pos.quantity,
    0
  );

  // 평가손익 합산 (DB의 unrealized_profit 사용 - 가장 정확)
  const totalUnrealizedProfit = positions.reduce(
    (sum, pos) => sum + Number(pos.unrealized_profit || 0),
    0
  );

  // 현재 주식 평가금액 = 매수금액 + 평가손익
  const stockEvaluation = totalBuyValue + totalUnrealizedProfit;

  // 현금 잔고
  const cashBalance = Number(strategy.cash_balance || 0);

  // 총 자산 = 주식 평가금액 + 현금 잔고
  const totalAssets = stockEvaluation + cashBalance;

  // 총 평가손익 = 주식 평가손익 (현금은 그대로이므로 손익에 영향 없음)
  const totalProfit = totalUnrealizedProfit;

  // 수익률 = 평가손익 / 할당 자본 × 100
  const totalReturn = allocatedCapital > 0
    ? (totalProfit / allocatedCapital) * 100
    : 0;

  // 백테스트 결과 형식으로 데이터 변환 (기존 컴포넌트 재사용)
  const resultData = {
    session_id: strategy.simulation_session_id,
    user_id: strategy.user_id,
    status: "completed" as const,
    total_return: totalReturn,
    final_balance: totalAssets,
    initial_capital: allocatedCapital,
    max_drawdown: 0, // TODO: 계산 필요
    sharpe_ratio: 0, // TODO: 계산 필요
    win_rate: 0, // TODO: 계산 필요
    total_trades: today_trades.length,
    total_positions: positions.length,
    start_date: strategy.created_at,
    end_date: new Date().toISOString(),
    created_at: strategy.created_at,
  };

  // StatisticsSection용 통계 데이터
  const statisticsSectionData = {
    totalReturn: totalReturn,
    annualizedReturn: totalReturn, // TODO: 연율화 필요
    maxDrawdown: 0,
    finalCapital: totalAssets,
  };

  // StatisticsTab용 완전한 통계 데이터 (BacktestResult["statistics"] 타입)
  const fullStatistics = {
    totalReturn: totalReturn,
    annualizedReturn: totalReturn, // TODO: 연율화 필요
    sharpeRatio: 0, // TODO: 계산 필요
    maxDrawdown: 0, // TODO: 계산 필요
    winRate: 0, // TODO: 계산 필요
    profitFactor: 1, // TODO: 계산 필요
    volatility: 0, // TODO: 계산 필요
    totalTrades: today_trades.length,
    winningTrades: today_trades.filter(t => (t.profit || 0) > 0).length,
    losingTrades: today_trades.filter(t => (t.profit || 0) < 0).length,
    initialCapital: allocatedCapital,
    finalCapital: totalAssets,
  };

  // 기간별 수익률 (임시 - TODO: 실제 데이터)
  const periodReturns = [
    { label: "1개월", value: 0 },
    { label: "3개월", value: 0 },
    { label: "6개월", value: 0 },
    { label: "1년", value: totalReturn },
  ];

  // 가상매매 거래 내역을 백테스트 형식으로 변환
  const convertedTrades = today_trades.map((trade) => ({
    stockName: trade.stock_name || trade.stock_code,
    stockCode: trade.stock_code,
    buyPrice: trade.trade_type === "BUY" ? trade.price : 0,
    sellPrice: trade.trade_type === "SELL" ? trade.price : 0,
    profit: trade.profit || 0,
    profitRate: trade.profit_rate || 0,
    buyDate: trade.trade_date,
    sellDate: trade.trade_type === "SELL" ? trade.trade_date : "", // BUY 거래는 아직 청산되지 않음
    weight: 0, // TODO: 비중 계산
    valuation: trade.amount,
    quantity: trade.quantity,
  }));

  return (
    <main className="flex-1 px-[18.75rem] py-[3.75rem] overflow-auto">
      {/* 헤더 */}
      <PageHeader
        title="📈 키움증권 연동 실시간 가상매매"
        subtitle={`${strategy.strategy_name || "가상매매 전략"} • ${strategy.is_active ? "활성화" : "비활성화"}`}
        onBack={() => router.push("/quant")}
      />

      {/* 통계 섹션 */}
      <StatisticsSection
        statistics={statisticsSectionData}
        initialCapital={allocatedCapital}
        periodReturns={periodReturns}
      />

      {/* 탭 네비게이션 */}
      <div className="flex gap-3 mb-6">
        {[
          { id: "stockInfo" as const, label: "보유 종목" },
          { id: "statistics" as const, label: "매매결과" },
          { id: "history" as const, label: "매매 내역" },
          { id: "settings" as const, label: "전략 설정" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-2 rounded-lg font-semibold text-[1.25rem] transition-colors ${
              activeTab === tab.id ? "bg-brand-purple text-white" : "hover:bg-brand-soft"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 탭 컨텐츠 */}
      <div className="mt-8">
        {activeTab === "stockInfo" && (
          <div className="space-y-6">
            {/* 보유 종목 테이블 */}
            <div className="bg-white rounded-lg shadow">
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
                            <td className="px-4 py-3 text-sm">
                              <button
                                type="button"
                                onClick={() =>
                                  setSelectedStock({
                                    name: pos.stock_name ?? pos.stock_code,
                                    code: pos.stock_code,
                                  })
                                }
                                className="text-left hover:text-brand-purple hover:underline transition-colors cursor-pointer"
                              >
                                {pos.stock_name ?? pos.stock_code}
                              </button>
                            </td>
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
          </div>
        )}

        {activeTab === "statistics" && (
          <StatisticsTabWrapper statistics={fullStatistics} />
        )}

        {activeTab === "history" && (
          <TradingHistoryTab trades={convertedTrades} />
        )}

        {activeTab === "settings" && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-6">⚙️ 전략 설정</h2>

            {!backtestSettings ? (
              <div className="text-gray-500">설정 정보를 불러오는 중...</div>
            ) : (
              <div className="space-y-6">
                {/* 기본 정보 */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">기본 정보</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">전략명</p>
                      <p className="font-semibold">{strategy.strategy_name || backtestSettings.strategyName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">백테스트 기간</p>
                      <p className="font-semibold">{backtestSettings.startDate} ~ {backtestSettings.endDate}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">초기 자본</p>
                      <p className="font-semibold">{backtestSettings.initialCapital.toLocaleString()}원</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">할당 자본</p>
                      <p className="font-semibold">{Math.round(strategy.allocated_capital).toLocaleString()}원</p>
                    </div>
                  </div>
                </div>

                {/* 유니버스 설정 */}
                <div>
                  <h3 className="text-lg font-semibold mb-3">선택 종목 (유니버스)</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">유니버스 타입</p>
                      <p className="font-semibold">{translateTerm(backtestSettings.universeType) || "전체"}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">시가총액 필터</p>
                      <p className="font-semibold">{translateTerm(backtestSettings.marketCapFilter) || "없음"}</p>
                    </div>
                    {backtestSettings.sectorFilter && backtestSettings.sectorFilter.length > 0 && (
                      <div className="col-span-2">
                        <p className="text-sm text-gray-500">섹터 필터</p>
                        <p className="font-semibold">{backtestSettings.sectorFilter.join(", ")}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* 팩터 설정 */}
                {backtestSettings.factors && backtestSettings.factors.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">팩터 설정</h3>
                    <div className="space-y-2">
                      {backtestSettings.factors.map((factor, idx) => (
                        <div key={idx} className="bg-gray-50 p-3 rounded">
                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <p className="text-xs text-gray-500">팩터명</p>
                              <p className="font-semibold text-sm">{factor.factorName}</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">사용 방식</p>
                              <p className="font-semibold text-sm">{translateTerm(factor.usageType)}</p>
                            </div>
                            {factor.operator && factor.thresholdValue && (
                              <div>
                                <p className="text-xs text-gray-500">조건</p>
                                <p className="font-semibold text-sm">{translateTerm(factor.operator)} {factor.thresholdValue}</p>
                              </div>
                            )}
                            {factor.weight && (
                              <div>
                                <p className="text-xs text-gray-500">가중치</p>
                                <p className="font-semibold text-sm">{factor.weight}</p>
                              </div>
                            )}
                            {factor.direction && (
                              <div>
                                <p className="text-xs text-gray-500">방향</p>
                                <p className="font-semibold text-sm">{translateTerm(factor.direction)}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 매매 규칙 */}
                {backtestSettings.tradingRules && backtestSettings.tradingRules.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">매매 조건</h3>
                    {backtestSettings.tradingRules.map((rule, idx) => (
                      <div key={idx} className="space-y-3">
                        <div className="grid grid-cols-3 gap-4">
                          {rule.rebalanceFrequency && (
                            <div>
                              <p className="text-sm text-gray-500">리밸런싱 주기</p>
                              <p className="font-semibold">{translateTerm(rule.rebalanceFrequency)}</p>
                            </div>
                          )}
                          {rule.maxPositions && (
                            <div>
                              <p className="text-sm text-gray-500">최대 보유 종목</p>
                              <p className="font-semibold">{rule.maxPositions}개</p>
                            </div>
                          )}
                          {rule.positionSizing && (
                            <div>
                              <p className="text-sm text-gray-500">포지션 사이징</p>
                              <p className="font-semibold">{translateTerm(rule.positionSizing)}</p>
                            </div>
                          )}
                          {rule.minHoldDays !== undefined && (
                            <div>
                              <p className="text-sm text-gray-500">최소 보유일</p>
                              <p className="font-semibold">{rule.minHoldDays}일</p>
                            </div>
                          )}
                          {rule.stopLossPct && (
                            <div>
                              <p className="text-sm text-gray-500">손절가</p>
                              <p className="font-semibold text-blue-600">-{rule.stopLossPct}%</p>
                            </div>
                          )}
                          {rule.takeProfitPct && (
                            <div>
                              <p className="text-sm text-gray-500">목표가</p>
                              <p className="font-semibold text-red-600">+{rule.takeProfitPct}%</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 가상매매 실행 정보 */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
                  <h3 className="font-semibold text-blue-900 mb-2">📈 가상매매 실행 정보</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm text-blue-700 mb-3">
                    <div>
                      <span className="text-gray-600">종목당 비중:</span> <span className="font-semibold">{strategy.per_stock_ratio}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">활성화 시각:</span> <span className="font-semibold">{strategy.activated_at || "-"}</span>
                    </div>
                  </div>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• 오전 7시: 매수/매도 종목 자동 선정</li>
                    <li>• 오전 9시: 실제 매수/매도 주문 실행</li>
                    <li>• 리밸런싱 주기: {translateTerm(strategy.rebalance_frequency)}</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 가상매매 비활성화 섹션 (하단 고정) */}
      <div className="mt-8">
        <AutoTradingSection
          sessionId={strategy.simulation_session_id}
          sessionStatus="completed"
        />
      </div>

      {/* 종목 상세 모달 */}
      <StockDetailModal
        isOpen={!!selectedStock}
        onClose={() => setSelectedStock(null)}
        stockName={selectedStock?.name || ""}
        stockCode={selectedStock?.code || ""}
      />
    </main>
  );
}
