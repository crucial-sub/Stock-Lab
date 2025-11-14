"use client";

import type { BacktestSettings } from "@/types/api";

/**
 * 설정 조건 탭 컴포넌트
 * - 백테스트 실행 시 사용된 설정값 표시
 * - 기본 설정, 전략 정보, 팩터 설정, 매매 규칙으로 구분
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
        <p className="text-text-muted text-center">설정 정보를 찾을 수 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 기본 설정 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-primary">
        <h3 className="text-lg font-bold text-accent-primary mb-4">기본 설정</h3>

        <div className="space-y-4">
          <SettingSection title="전략 정보">
            {settings.sessionName && (
              <SettingItem label="세션명" value={settings.sessionName} />
            )}
            <SettingItem label="전략명" value={settings.strategyName} />
            {settings.strategyType && (
              <SettingItem label="전략 유형" value={formatStrategyType(settings.strategyType)} />
            )}
            {settings.strategyDescription && (
              <div className="text-sm text-text-body">
                <span className="font-medium">전략 설명:</span>
                <p className="mt-1 pl-2 border-l-2 border-border-default">
                  {settings.strategyDescription}
                </p>
              </div>
            )}
          </SettingSection>

          <SettingSection title="백테스트 기간">
            <SettingItem label="시작일" value={formatDate(settings.startDate)} />
            <SettingItem label="종료일" value={formatDate(settings.endDate)} />
            <SettingItem
              label="초기 자본"
              value={`${settings.initialCapital.toLocaleString()}원`}
            />
            {settings.benchmark && (
              <SettingItem label="벤치마크" value={settings.benchmark} />
            )}
          </SettingSection>

          <SettingSection title="매매 대상">
            {settings.universeType && (
              <SettingItem label="유니버스" value={formatUniverseType(settings.universeType)} />
            )}
            {settings.marketCapFilter && (
              <SettingItem label="시가총액 필터" value={formatMarketCapFilter(settings.marketCapFilter)} />
            )}
            {settings.sectorFilter && settings.sectorFilter.length > 0 && (
              <div className="text-sm text-text-body">
                <span className="font-medium">섹터 필터:</span>
                <ul className="mt-1 pl-6 space-y-1 list-disc">
                  {settings.sectorFilter.slice(0, 5).map((sector, idx) => (
                    <li key={idx}>{sector}</li>
                  ))}
                  {settings.sectorFilter.length > 5 && (
                    <li className="text-text-muted">외 {settings.sectorFilter.length - 5}개</li>
                  )}
                </ul>
              </div>
            )}
          </SettingSection>
        </div>
      </div>

      {/* 팩터 설정 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-blue-500">
        <h3 className="text-lg font-bold text-blue-500 mb-4">팩터 설정</h3>

        {settings.factors.length === 0 ? (
          <p className="text-text-muted text-sm">설정된 팩터가 없습니다.</p>
        ) : (
          <div className="space-y-4">
            {/* Screening Factors */}
            {settings.factors.filter(f => f.usageType === "SCREENING").length > 0 && (
              <SettingSection title="스크리닝 팩터">
                <div className="space-y-2">
                  {settings.factors
                    .filter(f => f.usageType === "SCREENING")
                    .map((factor, idx) => (
                      <div key={idx} className="text-sm text-text-body bg-bg-muted p-2 rounded">
                        <p className="font-medium">{factor.factorName}</p>
                        {factor.operator && factor.thresholdValue !== undefined && (
                          <p className="text-xs text-text-muted">
                            {formatOperator(factor.operator)} {factor.thresholdValue}
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              </SettingSection>
            )}

            {/* Ranking Factors */}
            {settings.factors.filter(f => f.usageType === "RANKING").length > 0 && (
              <SettingSection title="랭킹 팩터">
                <div className="space-y-2">
                  {settings.factors
                    .filter(f => f.usageType === "RANKING")
                    .map((factor, idx) => (
                      <div key={idx} className="text-sm text-text-body bg-bg-muted p-2 rounded">
                        <p className="font-medium">{factor.factorName}</p>
                        {factor.direction && (
                          <p className="text-xs text-text-muted">
                            방향: {factor.direction === "POSITIVE" ? "높은 순" : "낮은 순"}
                          </p>
                        )}
                        {factor.weight !== undefined && (
                          <p className="text-xs text-text-muted">
                            가중치: {(factor.weight * 100).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              </SettingSection>
            )}

            {/* Scoring Factors */}
            {settings.factors.filter(f => f.usageType === "SCORING").length > 0 && (
              <SettingSection title="스코어링 팩터">
                <div className="space-y-2">
                  {settings.factors
                    .filter(f => f.usageType === "SCORING")
                    .map((factor, idx) => (
                      <div key={idx} className="text-sm text-text-body bg-bg-muted p-2 rounded">
                        <p className="font-medium">{factor.factorName}</p>
                        {factor.weight !== undefined && (
                          <p className="text-xs text-text-muted">
                            가중치: {(factor.weight * 100).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              </SettingSection>
            )}
          </div>
        )}
      </div>

      {/* 매매 규칙 - Full Width */}
      <div className="lg:col-span-2 bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-green-500">
        <h3 className="text-lg font-bold text-green-500 mb-4">매매 규칙</h3>

        {settings.tradingRules.length === 0 ? (
          <p className="text-text-muted text-sm">설정된 매매 규칙이 없습니다.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {settings.tradingRules.map((rule, idx) => (
              <div key={idx} className="space-y-3">
                <SettingSection title={formatRuleType(rule.ruleType)}>
                  {rule.rebalanceFrequency && (
                    <SettingItem
                      label="리밸런싱 주기"
                      value={formatRebalanceFrequency(rule.rebalanceFrequency)}
                    />
                  )}
                  {rule.rebalanceDay !== undefined && rule.rebalanceDay !== null && (
                    <SettingItem label="리밸런싱 일" value={`${rule.rebalanceDay}일`} />
                  )}
                  {rule.positionSizing && (
                    <SettingItem
                      label="포지션 크기"
                      value={formatPositionSizing(rule.positionSizing)}
                    />
                  )}
                  {rule.maxPositions !== undefined && rule.maxPositions !== null && (
                    <SettingItem label="최대 보유 종목" value={`${rule.maxPositions}개`} />
                  )}
                  {rule.minPositionWeight !== undefined && rule.minPositionWeight !== null && (
                    <SettingItem
                      label="최소 종목 비중"
                      value={`${(rule.minPositionWeight * 100).toFixed(2)}%`}
                    />
                  )}
                  {rule.maxPositionWeight !== undefined && rule.maxPositionWeight !== null && (
                    <SettingItem
                      label="최대 종목 비중"
                      value={`${(rule.maxPositionWeight * 100).toFixed(2)}%`}
                    />
                  )}
                  {rule.stopLossPct !== undefined && rule.stopLossPct !== null && (
                    <SettingItem label="손절매 비율" value={`${rule.stopLossPct}%`} />
                  )}
                  {rule.takeProfitPct !== undefined && rule.takeProfitPct !== null && (
                    <SettingItem label="익절매 비율" value={`${rule.takeProfitPct}%`} />
                  )}
                  {rule.commissionRate !== undefined && rule.commissionRate !== null && (
                    <SettingItem
                      label="수수료율"
                      value={`${(rule.commissionRate * 100).toFixed(3)}%`}
                    />
                  )}
                  {rule.taxRate !== undefined && rule.taxRate !== null && (
                    <SettingItem label="세금율" value={`${(rule.taxRate * 100).toFixed(2)}%`} />
                  )}
                </SettingSection>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 설정 섹션 컴포넌트
 */
function SettingSection({
  title,
  badge,
  badgeColor = "text-accent-primary",
  children,
}: {
  title: string;
  badge?: string;
  badgeColor?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <h4 className="text-sm font-semibold text-text-strong">{title}</h4>
        {badge && <span className={`text-xs font-medium ${badgeColor}`}>({badge})</span>}
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

/**
 * 설정 아이템 컴포넌트
 */
function SettingItem({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-sm text-text-body">
      <span className="font-medium">{label}:</span> {value}
    </p>
  );
}

/**
 * 날짜 포맷 헬퍼 (YYYY-MM-DD -> YYYY.MM.DD)
 */
function formatDate(dateStr: string): string {
  return dateStr.replace(/-/g, ".");
}

/**
 * 전략 유형 포맷
 */
function formatStrategyType(type: string): string {
  const types: Record<string, string> = {
    VALUE: "가치주 전략",
    GROWTH: "성장주 전략",
    MOMENTUM: "모멘텀 전략",
    MULTI: "복합 전략",
  };
  return types[type] || type;
}

/**
 * 유니버스 타입 포맷
 */
function formatUniverseType(type: string): string {
  const types: Record<string, string> = {
    KOSPI: "코스피",
    KOSDAQ: "코스닥",
    KOSPI200: "코스피 200",
    ALL: "전체",
  };
  return types[type] || type;
}

/**
 * 시가총액 필터 포맷
 */
function formatMarketCapFilter(filter: string): string {
  const filters: Record<string, string> = {
    LARGE: "대형주",
    MID: "중형주",
    SMALL: "소형주",
    ALL: "전체",
  };
  return filters[filter] || filter;
}

/**
 * 연산자 포맷
 */
function formatOperator(operator: string): string {
  const operators: Record<string, string> = {
    GT: ">",
    LT: "<",
    EQ: "=",
    GTE: ">=",
    LTE: "<=",
    TOP_N: "상위",
    BOTTOM_N: "하위",
  };
  return operators[operator] || operator;
}

/**
 * 규칙 타입 포맷
 */
function formatRuleType(type: string): string {
  const types: Record<string, string> = {
    REBALANCE: "리밸런싱",
    STOP_LOSS: "손절매",
    TAKE_PROFIT: "익절매",
  };
  return types[type] || type;
}

/**
 * 리밸런싱 주기 포맷
 */
function formatRebalanceFrequency(freq: string): string {
  const frequencies: Record<string, string> = {
    DAILY: "일별",
    WEEKLY: "주별",
    MONTHLY: "월별",
    QUARTERLY: "분기별",
  };
  return frequencies[freq] || freq;
}

/**
 * 포지션 크기 포맷
 */
function formatPositionSizing(sizing: string): string {
  const sizings: Record<string, string> = {
    EQUAL_WEIGHT: "균등 비중",
    MARKET_CAP: "시가총액 가중",
    RISK_PARITY: "리스크 패리티",
  };
  return sizings[sizing] || sizing;
}
