"use client";

import { Panel } from "@/components/common";
import { BacktestRunButton } from "@/components/quant/BacktestRunButton";
import { formatDateFromServer } from "@/lib/date-utils";
import { useBacktestConfigStore } from "@/stores";

/**
 * 최종 조건 확인 페이지 클라이언트 컴포넌트
 * - 사용자가 설정한 모든 백테스트 조건을 보기 좋게 표시
 * - 기본 설정, 매수 조건, 매도 조건, 매매 대상을 섹션별로 구분
 * - 우측 상단에 백테스트 실행 버튼 배치
 */
export function QuantConfirmPageClient() {
  const config = useBacktestConfigStore();

  return (
    <div className="min-h-screen bg-bg-app">
      <div className="quant-container py-8 space-y-6 max-h-screen overflow-y-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">최종 조건 확인</h1>
          <BacktestRunButton />
        </div>

        {/* 기본 설정 */}
        <Panel className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white border-b border-border-default pb-2">
            기본 설정
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">백테스트 데이터 기준:</span>
              <span className="text-white font-medium">
                {config.is_day_or_month === "daily" ? "일봉" : "월봉"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">투자 금액:</span>
              <span className="text-white font-medium">
                {config.initial_investment?.toLocaleString()} 만원
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">투자 시작일:</span>
              <span className="text-white font-medium">
                {formatDateFromServer(config.start_date)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">투자 종료일:</span>
              <span className="text-white font-medium">
                {formatDateFromServer(config.end_date)}
              </span>
            </div>
            <div className="flex justify-between col-span-2">
              <span className="text-text-secondary">수수료율:</span>
              <span className="text-white font-medium">
                {config.commission_rate}%
              </span>
            </div>
          </div>
        </Panel>

        {/* 매수 조건 */}
        <Panel className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-state-positive border-b border-border-default pb-2">
            매수 조건
          </h2>

          {/* 매수 조건식 */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-white">매수 조건식</h3>
            {config.buy_conditions.length > 0 ? (
              <div className="space-y-2">
                {config.buy_conditions.map((condition) => (
                  <div
                    key={condition.name}
                    className="flex items-center gap-2 text-sm"
                  >
                    <span className="text-state-positive font-medium w-8">
                      {condition.name}:
                    </span>
                    <span className="text-white">{condition.expression}</span>
                  </div>
                ))}
                <div className="flex items-center gap-2 text-sm mt-2">
                  <span className="text-text-secondary">논리 조건식:</span>
                  <span className="text-white font-medium">
                    {config.buy_logic || "없음"}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-text-tertiary text-sm">
                설정된 조건식이 없습니다
              </div>
            )}
          </div>

          {/* 매수 종목 선택 우선순위 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">우선순위 팩터:</span>
              <span className="text-white font-medium">
                {config.priority_factor || "없음"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">우선순위 방향:</span>
              <span className="text-white font-medium">
                {config.priority_order === "desc" ? "내림차순" : "오름차순"}
              </span>
            </div>
          </div>

          {/* 매수 비중 설정 */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex justify-between">
              <span className="text-text-secondary">종목당 매수 비중:</span>
              <span className="text-white font-medium">
                {config.per_stock_ratio}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">최대 보유 종목 수:</span>
              <span className="text-white font-medium">
                {config.max_holdings} 종목
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">
                종목당 최대 매수 금액:
              </span>
              <span className="text-white font-medium">
                {config.max_buy_value
                  ? `${config.max_buy_value?.toLocaleString()} 만원`
                  : "제한 없음"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">
                일일 최대 매수 종목 수:
              </span>
              <span className="text-white font-medium">
                {config.max_daily_stock
                  ? `${config.max_daily_stock} 종목`
                  : "제한 없음"}
              </span>
            </div>
          </div>

          {/* 매수 가격 기준 */}
          <div className="flex justify-between text-sm">
            <span className="text-text-secondary">매수 가격 기준:</span>
            <span className="text-white font-medium">
              {config.buy_cost_basis}
            </span>
          </div>
        </Panel>

        {/* 매도 조건 */}
        <Panel className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-state-negative border-b border-border-default pb-2">
            매도 조건
          </h2>

          {/* 목표가/손절가 */}
          {config.target_and_loss && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-white">
                목표가 / 손절가
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">목표가:</span>
                  <span className="text-white font-medium">
                    {config.target_and_loss.target_gain !== null
                      ? `${config.target_and_loss.target_gain}%`
                      : "설정 안함"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">손절가:</span>
                  <span className="text-white font-medium">
                    {config.target_and_loss.stop_loss !== null
                      ? `${config.target_and_loss.stop_loss}%`
                      : "설정 안함"}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 보유 기간 */}
          {config.hold_days && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-white">보유 기간</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-text-secondary">
                    최소 종목 보유일:
                  </span>
                  <span className="text-white font-medium">
                    {config.hold_days.min_hold_days}일
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-secondary">
                    최대 종목 보유일:
                  </span>
                  <span className="text-white font-medium">
                    {config.hold_days.max_hold_days}일
                  </span>
                </div>
                <div className="flex justify-between col-span-2">
                  <span className="text-text-secondary">매도 가격 기준:</span>
                  <span className="text-white font-medium">
                    {config.hold_days.sell_cost_basis}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 조건 매도 */}
          {config.sell_conditions && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-white">조건 매도</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-state-negative font-medium w-8">
                    {config.sell_conditions.name}:
                  </span>
                  <span className="text-white">
                    {config.sell_conditions.expression}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-secondary">논리 조건식:</span>
                  <span className="text-white font-medium">
                    {config.sell_conditions.sell_logic || "없음"}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-secondary">매도 가격 기준:</span>
                  <span className="text-white font-medium">
                    {config.sell_conditions.sell_cost_basis}
                  </span>
                </div>
              </div>
            </div>
          )}

          {!config.target_and_loss &&
            !config.hold_days &&
            !config.sell_conditions && (
              <div className="text-text-tertiary text-sm">
                설정된 매도 조건이 없습니다
              </div>
            )}
        </Panel>

        {/* 매매 대상 */}
        <Panel className="p-6 space-y-4">
          <h2 className="text-lg font-semibold text-white border-b border-border-default pb-2">
            매매 대상
          </h2>
          {config.target_stocks.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {config.target_stocks.map((stock) => (
                <span
                  key={stock}
                  className="px-3 py-1 bg-white/10 rounded-full text-sm text-white border border-white/20"
                >
                  {stock}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-text-tertiary text-sm">
              선택된 매매 대상이 없습니다 (전체 종목 대상)
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
