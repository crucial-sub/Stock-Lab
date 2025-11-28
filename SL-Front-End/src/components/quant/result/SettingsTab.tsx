"use client";

import type { BacktestSettings } from "@/types/api";
import { FieldPanel } from "@/components/quant/ui/FieldPanel";

/**
 * 설정 조건 탭 컴포넌트
 * - 백테스트 실행 시 사용된 설정값을 젠포트 스타일로 상세 표시
 * - 매수조건, 매도조건, 매매대상으로 구분하여 표시
 */
interface SettingsTabProps {
  settings: BacktestSettings | null;
  isLoading?: boolean;
}

export function SettingsTab({ settings, isLoading = false }: SettingsTabProps) {
  if (isLoading) {
    return (
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <p className="text-text-muted text-center">설정을 불러오는 중...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <p className="text-text-muted text-center">
          설정 정보를 찾을 수 없습니다.
        </p>
      </div>
    );
  }

  // 첫 번째 거래 규칙에서 조건 추출 (주요 전략)
  const mainRule = settings.tradingRules?.[0];
  const buyCondition = mainRule?.buyCondition || {};
  const sellCondition = mainRule?.sellCondition || {};
  const tradeTargets = buyCondition?.trade_targets || {};

  return (
    <div className="space-y-6">
      {/* 기본 정보 헤더 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-1">전략명</h4>
            <p className="text-base font-semibold text-text-strong">
              {settings.strategyName}
            </p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-1">백테스트 기간</h4>
            <p className="text-base text-text-body">
              {formatDate(settings.startDate)} ~ {formatDate(settings.endDate)}
            </p>
          </div>
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-1">초기 자본</h4>
            <p className="text-base text-text-body">
              {settings.initialCapital.toLocaleString()}원
            </p>
          </div>
        </div>

        {/* 포트 기본 설정 - 한 줄로 표시 */}
        <div className="pt-4 border-t border-border-default">
          <p className="text-sm text-text-muted">
            <span className="font-medium">포트 기본 설정</span>
            <span className="ml-4">수수료율 {((mainRule?.commissionRate || 0.00015) * 100).toFixed(4)}%</span>
            <span className="ml-4">슬리피지 0.000%</span>
          </p>
        </div>
      </div>

      {/* 2x2 그리드 레이아웃 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. 매수조건 필드 (왼쪽 상단) */}
        <FieldPanel conditionType="buy">
          <BuyConditionsSection
            buyCondition={buyCondition}
            tradingRule={mainRule}
            factors={settings.factors}
          />
        </FieldPanel>

        {/* 2. 매도조건 필드 (오른쪽 상단) */}
        <FieldPanel conditionType="sell">
          <SellConditionsSection
            sellCondition={sellCondition}
            tradingRule={mainRule}
          />
        </FieldPanel>

        {/* 3. 매매대상 필드 (왼쪽 하단) */}
        <FieldPanel conditionType="target">
          <TradingTargetsSection tradeTargets={tradeTargets} />
        </FieldPanel>

        {/* 4. 빈 공간 (오른쪽 하단) */}
        <div></div>
      </div>
    </div>
  );
}

/**
 * 매수조건 섹션
 */
function BuyConditionsSection({
  buyCondition,
  tradingRule,
  factors
}: {
  buyCondition: any;
  tradingRule: any;
  factors: any[];
}) {
  // 스크리닝 팩터를 매수 조건으로 사용
  const screeningFactors = factors.filter((f: any) => f.usageType === "SCREENING");
  const scoringFactors = factors.filter((f: any) => f.usageType === "SCORING");

  // buyCondition에서 논리 조건식 추출
  const buyConditions = buyCondition?.conditions || [];
  const buyLogic = buyCondition?.buy_logic || "AND";

  return (
    <div>
      <h3 className="text-lg font-bold text-price-up mb-4">
        매수조건
      </h3>

      <div className="space-y-4">
        {/* 매수 논리 조건식 - 우선 표시 */}
        {buyConditions.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">매수 조건식</h4>
            {/* 논리식 표현 (A and B and C...) */}
            <div className="mb-3">
              <div className="text-base font-bold text-text-strong">
                {buyConditions.map((_: any, idx: number) =>
                  String.fromCharCode(65 + idx) // A, B, C...
                ).join(buyLogic === "OR" ? ' or ' : ' and ')}
              </div>
            </div>

            {/* 각 조건 상세 */}
            <div className="space-y-1">
              {buyConditions.map((condition: any, idx: number) => {
                const label = String.fromCharCode(65 + idx); // A, B, C...
                return (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="font-bold text-price-up min-w-[20px]">
                      {label}:
                    </span>
                    <div className="flex-1 text-sm text-text-body">
                      <span>
                        ({parseFactorName(condition.exp_left_side || condition.factor || condition.name || "조건")})
                      </span>
                      <span className="mx-1 font-medium">
                        {formatOperator(condition.inequality || condition.operator || "GT")}
                      </span>
                      <span>
                        {condition.exp_right_side !== undefined ? condition.exp_right_side : condition.value || ""}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 매수 종목 선택 우선순위 */}
        {scoringFactors.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">매수 종목 선택 우선순위</h4>
            <div className="text-sm text-text-body">
              [내림차순] {scoringFactors.map((factor: any) => parseFactorName(factor.factorName)).join(', ')}
            </div>
          </div>
        )}

        {/* 매수 비중 */}
        <div>
          <h4 className="text-sm font-medium text-text-muted mb-2">매수 비중</h4>
          <div className="space-y-1 text-sm text-text-body">
            {tradingRule?.positionSizing && (
              <div>포지션 크기 전략: {formatPositionSizing(tradingRule.positionSizing)}</div>
            )}
            {tradingRule?.maxPositions !== undefined && tradingRule?.maxPositions !== null && (
              <div>최대 보유 종목 수: {tradingRule.maxPositions}개</div>
            )}
            {tradingRule?.minPositionWeight !== undefined && tradingRule?.minPositionWeight !== null && (
              <div>최소 종목 비중: {(tradingRule.minPositionWeight * 100).toFixed(2)}%</div>
            )}
            {tradingRule?.maxPositionWeight !== undefined && tradingRule?.maxPositionWeight !== null && (
              <div>최대 종목 비중: {(tradingRule.maxPositionWeight * 100).toFixed(2)}%</div>
            )}
          </div>
        </div>

        {/* 매수 방법 */}
        <div>
          <h4 className="text-sm font-medium text-text-muted mb-2">매수 방법</h4>
          <div className="space-y-1 text-sm text-text-body">
            <div>가격 기준: 전일 종가</div>
            {tradingRule?.rebalanceFrequency && (
              <div>리밸런싱 주기: {formatFrequency(tradingRule.rebalanceFrequency)}</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * 매도조건 섹션
 */
function SellConditionsSection({
  sellCondition,
  tradingRule
}: {
  sellCondition: any;
  tradingRule: any;
}) {
  // sell_condition 구조: { condition_sell: { sell_conditions: [...], sell_logic: "OR" } }
  const conditionSell = sellCondition?.condition_sell || {};
  const sellConditions = conditionSell?.sell_conditions || [];
  const sellLogic = conditionSell?.sell_logic || "OR";

  return (
    <div>
      <h3 className="text-lg font-bold text-blue-500 mb-4">
        매도조건
      </h3>

      <div className="space-y-4">
        {/* 매도 논리 조건식 - 맨 위에 표시 */}
        {sellConditions.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">매도 조건식</h4>
            {/* 논리식 표현 (A or B or C...) */}
            <div className="mb-3">
              <div className="text-base font-bold text-text-strong">
                {sellConditions.map((_: any, idx: number) =>
                  String.fromCharCode(65 + idx) // A, B, C...
                ).join(sellLogic === "AND" ? ' and ' : ' or ')}
              </div>
            </div>

            {/* 각 조건 상세 */}
            <div className="space-y-1">
              {sellConditions.map((condition: any, idx: number) => {
                const label = String.fromCharCode(65 + idx); // A, B, C...
                return (
                  <div key={idx} className="flex items-start gap-2">
                    <span className="font-bold text-blue-500 min-w-[20px]">
                      {label}:
                    </span>
                    <div className="flex-1 text-sm text-text-body">
                      <span>
                        ({parseFactorName(condition.exp_left_side || condition.factor || condition.name || "조건")})
                      </span>
                      <span className="mx-1 font-medium">
                        {formatOperator(condition.inequality || condition.operator || "GT")}
                      </span>
                      <span>
                        {condition.exp_right_side !== undefined ? condition.exp_right_side : condition.value || ""}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 목표가 / 손절가 */}
        {(tradingRule?.takeProfitPct !== undefined || tradingRule?.stopLossPct !== undefined) && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">목표가 / 손절가</h4>
            <div className="space-y-1 text-sm text-text-body">
              {tradingRule?.takeProfitPct !== undefined && tradingRule?.takeProfitPct !== null && (
                <div>목표 수익률: +{tradingRule.takeProfitPct}%</div>
              )}
              {tradingRule?.stopLossPct !== undefined && tradingRule?.stopLossPct !== null && (
                <div>손절 기준: -{tradingRule.stopLossPct}%</div>
              )}
            </div>
          </div>
        )}

        {/* 보유 기간 */}
        {(tradingRule?.minHoldDays !== undefined || tradingRule?.maxHoldDays !== undefined) && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">보유 기간</h4>
            <div className="space-y-1 text-sm text-text-body">
              {tradingRule?.minHoldDays !== undefined && tradingRule?.minHoldDays !== null && (
                <div>최소 보유 일수: {tradingRule.minHoldDays}일</div>
              )}
              {tradingRule?.maxHoldDays !== undefined && tradingRule?.maxHoldDays !== null && (
                <div>최대 보유 일수: {tradingRule.maxHoldDays}일</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 매매대상 섹션
 */
function TradingTargetsSection({ tradeTargets }: { tradeTargets: any }) {
  const hasTargets = tradeTargets && Object.keys(tradeTargets).length > 0;

  if (!hasTargets) {
    return null;
  }

  return (
    <div>
      <h3 className="text-lg font-bold text-brand-purple mb-4">
        매매대상
      </h3>

      <div className="space-y-4">
        {/* 선택한 테마 */}
        {tradeTargets.selected_themes && tradeTargets.selected_themes.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">선택한 테마</h4>
            <div className="flex flex-wrap gap-2">
              {tradeTargets.selected_themes.map((theme: string) => (
                <span
                  key={theme}
                  className="px-2 py-1 bg-bg-subtle rounded-md text-xs text-text-body"
                >
                  {theme}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 매매 대상 종목 수 */}
        <div>
          <h4 className="text-sm font-medium text-text-muted mb-2">매매 대상 종목</h4>
          <div className="text-sm text-text-body">
            {tradeTargets.use_all_stocks ? (
              <span>전체 종목 ({tradeTargets.total_stock_count || 0}개)</span>
            ) : (
              <span>
                선택 종목 (
                {tradeTargets.selected_stocks?.length || 0}개 /
                전체 {tradeTargets.total_stock_count || 0}개)
              </span>
            )}
          </div>
        </div>

        {/* 선택한 세부 종목 */}
        {tradeTargets.selected_stocks && tradeTargets.selected_stocks.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-text-muted mb-2">선택한 세부 종목</h4>
            <div className="text-xs text-text-body">
              {tradeTargets.selected_stocks.join(", ")}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 헬퍼 함수들
 */
function formatDate(dateStr: string): string {
  return dateStr.replace(/-/g, ".");
}

/**
 * 팩터명 파싱 (주가수익률(PER) 형식에서 PER 추출)
 */
function parseFactorName(factorString: string): string {
  // "주가수익률(PER)" 형식에서 한글 설명 제거
  const match = factorString.match(/\(([^)]+)\)/);
  if (match && match[1]) {
    return match[1];
  }

  // "분기/EPS성장률(YOY)" 같은 형식 처리
  if (factorString.includes('/')) {
    const parts = factorString.split('/');
    const lastPart = parts[parts.length - 1];
    const innerMatch = lastPart.match(/\(([^)]+)\)/);
    if (innerMatch && innerMatch[1]) {
      return `${parts[0]}/${innerMatch[1]}`;
    }
    return factorString;
  }

  return factorString;
}

function formatOperator(operator: string): string {
  const operators: Record<string, string> = {
    GT: ">",
    GTE: "≥",
    LT: "<",
    LTE: "≤",
    EQ: "=",
    NEQ: "≠",
  };
  return operators[operator] || operator;
}

function formatFrequency(freq: string): string {
  const frequencies: Record<string, string> = {
    DAILY: "일별",
    WEEKLY: "주별",
    MONTHLY: "월별",
    QUARTERLY: "분기별",
  };
  return frequencies[freq] || freq;
}

function formatPositionSizing(sizing: string): string {
  const sizings: Record<string, string> = {
    EQUAL_WEIGHT: "균등 비중",
    MARKET_CAP: "시가총액 가중",
    RISK_PARITY: "리스크 패리티",
  };
  return sizings[sizing] || sizing;
}