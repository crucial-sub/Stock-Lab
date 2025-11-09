"use client";

import { useState } from "react";
import { useBacktestResultQuery } from "@/hooks/useBacktestQuery";
import { TradingHistoryTab } from "@/components/quant/result/TradingHistoryTab";
import { ReturnsTab } from "@/components/quant/result/ReturnsTab";
import { StatisticsTabWrapper } from "@/components/quant/result/StatisticsTabWrapper";
import { SettingsTab } from "@/components/quant/result/SettingsTab";
import type { BacktestRunRequest } from "@/types/api";
import { mockBacktestResult } from "@/mocks/backtestResult";

/**
 * 백테스트 결과 페이지 - 클라이언트 컴포넌트 (최신 디자인)
 *
 * Figma 디자인에 따른 4-탭 레이아웃:
 * 1. 거래내역 (매매 종목 정보)
 * 2. 수익률 (누적 수익률 차트 - amCharts5)
 * 3. 매매결과 (통계 정보)
 * 4. 설정 조건 (매수/매도/매매대상 설정 요약)
 */

interface QuantResultPageClientProps {
  backtestId: string;
}

type TabType = "history" | "returns" | "statistics" | "settings";

export function QuantResultPageClient({
  backtestId,
}: QuantResultPageClientProps) {
  const [activeTab, setActiveTab] = useState<TabType>("history");

  // Mock 모드 체크 (backtestId가 "mock"으로 시작하면 Mock 데이터 사용)
  const isMockMode = backtestId.startsWith("mock");

  // React Query로 백테스트 결과 조회
  const { data: result, isLoading, error } = useBacktestResultQuery(
    backtestId,
    !isMockMode // Mock 모드면 API 호출 비활성화
  );

  // Mock 데이터 또는 실제 데이터 사용
  const finalResult = isMockMode ? mockBacktestResult : result;

  // 로딩 상태
  if (isLoading && !isMockMode) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-primary mx-auto" />
          <p className="text-text-secondary">백테스트 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태 (Mock 모드가 아닐 때만)
  if (!isMockMode && (error || !result)) {
    return (
      <div className="min-h-screen bg-bg-app flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-text-primary">
            백테스트 결과를 불러올 수 없습니다
          </h1>
          <p className="text-text-secondary">
            {error?.message || "알 수 없는 오류가 발생했습니다."}
          </p>
        </div>
      </div>
    );
  }

  // finalResult가 없으면 리턴 (타입 가드)
  if (!finalResult) {
    return null;
  }

  // 통계 데이터 계산
  const stats = finalResult.statistics;
  const initialCapital = 50000000; // 5천만원 (설정값에서 가져와야 함)
  const totalProfit = initialCapital * (stats.totalReturn / 100);
  const finalAssets = initialCapital + totalProfit;

  // 수익률 차트 데이터 (임시 - 실제 API 응답 구조에 따라 수정 필요)
  const periodReturns = [
    { label: "최근 거래일", value: -0.37 },
    { label: "최근 월주일", value: -2.13 },
    { label: "최근 1개월", value: -1.85 },
    { label: "최근 3개월", value: -2.38 },
    { label: "최근 6개월", value: 8.02 },
    { label: "최근 1년", value: 16.15 },
  ];

  return (
    <div className="min-h-screen bg-bg-app py-6 px-6">
      <div className="max-w-[1400px] mx-auto">
        {/* 페이지 제목 및 액션 버튼 */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-[2rem] font-bold text-text-strong">매매 결과</h1>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-accent-primary text-white rounded-sm font-medium hover:bg-accent-primary/90 transition-colors">
              백테스트 다시하기
            </button>
            <button className="px-4 py-2 bg-bg-surface text-text-body rounded-sm font-medium hover:bg-bg-muted transition-colors">
              로그아웃
            </button>
          </div>
        </div>

        {/* 통계 섹션 (상단 고정) */}
        <div className="bg-bg-surface rounded-lg shadow-card p-6 mb-6">
          <div className="flex justify-between items-start">
            {/* 왼쪽: 통계 지표 */}
            <div className="flex-1">
              <h2 className="text-lg font-bold text-text-strong mb-4">통계</h2>

              {/* 상단 주요 지표 */}
              <div className="grid grid-cols-4 gap-8 mb-6">
                <StatMetric
                  label="일 평균 수익률"
                  value={`${(stats.totalReturn / 365).toFixed(2)}%`}
                  color="text-accent-primary"
                  tooltip="일별 평균 수익률"
                />
                <StatMetric
                  label="누적 수익률"
                  value={`${stats.annualizedReturn.toFixed(2)}%`}
                  color="text-accent-primary"
                  tooltip="연간 수익률"
                />
                <StatMetric
                  label="CAGR"
                  value={`${stats.annualizedReturn.toFixed(2)}%`}
                  color="text-accent-primary"
                  tooltip="연평균 복리 수익률"
                />
                <StatMetric
                  label="MDD"
                  value={`${stats.maxDrawdown.toFixed(2)}%`}
                  color="text-text-strong"
                  tooltip="최대 낙폭"
                />
              </div>

              {/* 하단 자산 정보 */}
              <div className="grid grid-cols-3 gap-8">
                <StatMetric
                  label="투자 원금"
                  value={`${initialCapital.toLocaleString()}원`}
                  size="large"
                />
                <StatMetric
                  label="총 손익"
                  value={`${totalProfit.toLocaleString()}원`}
                  color="text-accent-primary"
                  size="large"
                  tooltip="총 수익금"
                />
                <StatMetric
                  label="현재 총 자산"
                  value={`${finalAssets.toLocaleString()}원`}
                  size="large"
                />
              </div>
            </div>

            {/* 오른쪽: 수익률 바 차트 */}
            <div className="w-[500px] ml-8">
              <h3 className="text-sm font-semibold text-text-strong mb-3">
                수익률 (%)
              </h3>
              <div className="flex items-end gap-2 h-32">
                {periodReturns.map((item, i) => {
                  const isPositive = item.value >= 0;
                  const barHeight = Math.abs(item.value) * 3;

                  return (
                    <div key={i} className="flex-1 flex flex-col items-center">
                      <div className="w-full h-24 flex items-end justify-center">
                        <div
                          className={`w-full rounded-t transition-all ${
                            isPositive
                              ? "bg-accent-primary"
                              : i < 3
                                ? "bg-blue-500"
                                : "bg-red-500"
                          }`}
                          style={{
                            height: `${barHeight}px`,
                            minHeight: "4px",
                          }}
                        />
                      </div>
                      <div className="text-[10px] text-text-body mt-2 text-center leading-tight">
                        {item.value > 0 ? "+" : ""}
                        {item.value.toFixed(2)}%
                      </div>
                      <div className="text-[10px] text-text-muted mt-1 text-center leading-tight">
                        {item.label}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="flex gap-3 mb-6">
          <TabButton
            label="거래내역"
            active={activeTab === "history"}
            onClick={() => setActiveTab("history")}
          />
          <TabButton
            label="수익률"
            active={activeTab === "returns"}
            onClick={() => setActiveTab("returns")}
          />
          <TabButton
            label="매매결과"
            active={activeTab === "statistics"}
            onClick={() => setActiveTab("statistics")}
          />
          <TabButton
            label="설정 조건"
            active={activeTab === "settings"}
            onClick={() => setActiveTab("settings")}
          />
        </div>

        {/* 탭 컨텐츠 */}
        {activeTab === "history" && <TradingHistoryTab trades={finalResult.trades} />}
        {activeTab === "returns" && <ReturnsTab yieldPoints={finalResult.yieldPoints} />}
        {activeTab === "statistics" && <StatisticsTabWrapper statistics={finalResult.statistics} />}
        {activeTab === "settings" && (
          <SettingsTab
            settings={
              {
                // 임시 설정 데이터 (실제로는 백테스트 결과에 포함되어야 함)
                user_id: "temp_user",
                strategy_name: "테스트 전략",
                is_day_or_month: "일봉",
                start_date: "20240101",
                end_date: "20241231",
                initial_investment: 5000,
                commission_rate: 0.015,
                slippage: 0.01,
                buy_conditions: [
                  {
                    name: "A",
                    exp_left_side: "{PER}",
                    inequality: "<",
                    exp_right_side: 15,
                  },
                ],
                buy_logic: "A",
                priority_factor: "{PBR}",
                priority_order: "asc",
                per_stock_ratio: 10,
                max_holdings: 10,
                max_buy_value: null,
                max_daily_stock: null,
                buy_price_basis: "전일 종가",
                buy_price_offset: 0,
                target_and_loss: {
                  target_gain: 20,
                  stop_loss: 10,
                },
                hold_days: null,
                condition_sell: null,
                trade_targets: {
                  use_all_stocks: false,
                  selected_universes: ["KOSPI_LARGE"],
                  selected_themes: [],
                  selected_stocks: [],
                },
              } as BacktestRunRequest
            }
          />
        )}
      </div>
    </div>
  );
}

/**
 * 통계 지표 컴포넌트
 */
function StatMetric({
  label,
  value,
  color = "text-text-strong",
  size = "normal",
  tooltip,
}: {
  label: string;
  value: string;
  color?: string;
  size?: "normal" | "large";
  tooltip?: string;
}) {
  return (
    <div>
      <div
        className={`font-bold ${color} mb-1 ${
          size === "large" ? "text-xl" : "text-2xl"
        }`}
      >
        {value}
      </div>
      <div className="text-sm text-text-body flex items-center gap-1">
        {label}
        {tooltip && (
          <span className="text-text-muted cursor-help" title={tooltip}>
            ⓘ
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * 탭 버튼 컴포넌트
 */
function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-6 py-2.5 rounded-sm font-medium transition-colors ${
        active
          ? "bg-accent-primary text-white"
          : "bg-bg-surface text-text-body hover:bg-bg-muted"
      }`}
    >
      {label}
    </button>
  );
}
