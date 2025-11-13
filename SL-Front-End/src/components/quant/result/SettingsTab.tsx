"use client";

import type { BacktestRunRequest } from "@/types/api";

/**
 * 설정 조건 탭 컴포넌트
 * - 백테스트 실행 시 사용된 설정값 표시
 * - 매수 조건, 매도 조건, 매매 대상 섹션으로 구분
 */
interface SettingsTabProps {
  settings: BacktestRunRequest;
}

export function SettingsTab({ settings }: SettingsTabProps) {
  return (
    <div className="grid grid-cols-3 gap-6">
      {/* 매수 조건 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-primary">
        <h3 className="text-lg font-bold text-accent-primary mb-4">매수 조건</h3>

        <div className="space-y-4">
          {/* 일반 조건 */}
          <SettingSection title="일반 조건">
            <SettingItem
              label="백테스트 데이터 기준"
              value={settings.is_day_or_month}
            />
            <SettingItem
              label="투자 금액"
              value={`${settings.initial_investment.toLocaleString()}만원`}
            />
            <SettingItem
              label="수수료율"
              value={`${settings.commission_rate}%`}
            />
            <SettingItem label="슬리피지" value={`${settings.slippage}%`} />
          </SettingSection>

          {/* 매수 조건식 */}
          <SettingSection title="매수 조건식">
            <div className="space-y-1 text-sm text-text-body">
              {settings.buy_conditions.map((condition, idx) => (
                <p key={idx}>
                  {condition.name}: {condition.exp_left_side}{" "}
                  {condition.inequality} {condition.exp_right_side}
                </p>
              ))}
            </div>
            <SettingItem label="논리 조건식" value={settings.buy_logic} />
          </SettingSection>

          {/* 투자 기간 */}
          <SettingSection title="투자 기간">
            <SettingItem label="시작일" value={formatDate(settings.start_date)} />
            <SettingItem label="종료일" value={formatDate(settings.end_date)} />
          </SettingSection>

          {/* 매수 비중 설정 */}
          <SettingSection title="매수 비중 설정">
            <SettingItem
              label="종목당 매수 비중"
              value={`${settings.per_stock_ratio}%`}
            />
            <SettingItem label="최대 보유 종목 수" value={`${settings.max_holdings}개`} />
            {settings.max_buy_value && (
              <SettingItem
                label="종목당 최대 매수 금액"
                value={`${settings.max_buy_value.toLocaleString()}만원`}
              />
            )}
            {settings.max_daily_stock && (
              <SettingItem
                label="일일 최대 매수 종목"
                value={`${settings.max_daily_stock}개`}
              />
            )}
          </SettingSection>

          {/* 매수 가격 설정 */}
          <SettingSection title="매수 가격 설정">
            <SettingItem label="매수 가격 기준" value={settings.buy_price_basis} />
            <SettingItem
              label="기준가 대비 증감"
              value={`${settings.buy_price_offset > 0 ? "+" : ""}${settings.buy_price_offset}%`}
            />
          </SettingSection>

          {/* 매수 우선순위 */}
          <SettingSection title="매수 우선순위">
            <SettingItem label="우선순위 팩터" value={settings.priority_factor} />
            <SettingItem
              label="우선순위 방향"
              value={settings.priority_order === "asc" ? "오름차순" : "내림차순"}
            />
          </SettingSection>
        </div>
      </div>

      {/* 매도 조건 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-blue-500">
        <h3 className="text-lg font-bold text-blue-500 mb-4">매도 조건</h3>

        <div className="space-y-4">
          {/* 목표가 / 손절가 */}
          {settings.target_and_loss && (
            <SettingSection
              title="목표가 / 손절가"
              badge={settings.target_and_loss ? "활성화" : "비활성화"}
              badgeColor={
                settings.target_and_loss ? "text-accent-primary" : "text-text-muted"
              }
            >
              {settings.target_and_loss.target_gain !== null && (
                <SettingItem
                  label="목표가"
                  value={`매수가 대비 ${settings.target_and_loss.target_gain}% 상승`}
                />
              )}
              {settings.target_and_loss.stop_loss !== null && (
                <SettingItem
                  label="손절가"
                  value={`매수가 대비 ${settings.target_and_loss.stop_loss}% 하락`}
                />
              )}
            </SettingSection>
          )}

          {/* 보유 기간 */}
          {settings.hold_days && (
            <SettingSection
              title="보유 기간"
              badge={settings.hold_days ? "활성화" : "비활성화"}
              badgeColor={settings.hold_days ? "text-accent-primary" : "text-text-muted"}
            >
              <SettingItem
                label="최소 종목 보유일"
                value={`${settings.hold_days.min_hold_days}일`}
              />
              <SettingItem
                label="최대 종목 보유일"
                value={`${settings.hold_days.max_hold_days}일`}
              />
              <SettingItem
                label="매도 가격 기준"
                value={`${settings.hold_days.sell_price_basis}, ${settings.hold_days.sell_price_offset > 0 ? "+" : ""}${settings.hold_days.sell_price_offset}%`}
              />
            </SettingSection>
          )}

          {/* 조건 매도 */}
          {settings.condition_sell && (
            <SettingSection
              title="조건 매도"
              badge={settings.condition_sell ? "활성화" : "비활성화"}
              badgeColor={
                settings.condition_sell ? "text-accent-primary" : "text-text-muted"
              }
            >
              <div className="space-y-1 text-sm text-text-body">
                <p className="font-medium">매도 조건식:</p>
                {settings.condition_sell.sell_conditions.map((condition, idx) => (
                  <p key={idx} className="ml-2">
                    {condition.name}: {condition.exp_left_side}{" "}
                    {condition.inequality} {condition.exp_right_side}
                  </p>
                ))}
              </div>
              <SettingItem
                label="논리 조건식"
                value={settings.condition_sell.sell_logic}
              />
              <SettingItem
                label="매도 가격 기준"
                value={`${settings.condition_sell.sell_price_basis}, ${settings.condition_sell.sell_price_offset > 0 ? "+" : ""}${settings.condition_sell.sell_price_offset}%`}
              />
            </SettingSection>
          )}
        </div>
      </div>

      {/* 매매 대상 */}
      <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-green-500">
        <h3 className="text-lg font-bold text-green-500 mb-4">매매 대상</h3>

        <div className="space-y-4">
          {/* 매매 대상 종목 */}
          <SettingSection title="매매 대상 종목">
            {settings.trade_targets.use_all_stocks ? (
              <SettingItem label="전체 종목 사용" value="예" />
            ) : (
              <>
                <SettingItem
                  label="선택한 유니버스"
                  value={`${settings.trade_targets.selected_universes.length}개`}
                />
                <SettingItem
                  label="선택한 테마"
                  value={`${settings.trade_targets.selected_themes.length}개`}
                />
                <SettingItem
                  label="개별 선택 종목"
                  value={`${settings.trade_targets.selected_stocks.length}개`}
                />
              </>
            )}
          </SettingSection>

          {/* 선택한 유니버스 목록 */}
          {!settings.trade_targets.use_all_stocks &&
            settings.trade_targets.selected_universes.length > 0 && (
              <SettingSection title="선택한 유니버스">
                <ul className="space-y-1 text-sm text-text-body list-disc list-inside">
                  {settings.trade_targets.selected_universes.map((universe, idx) => (
                    <li key={idx}>{universe}</li>
                  ))}
                </ul>
              </SettingSection>
            )}

          {/* 선택한 테마 */}
          {!settings.trade_targets.use_all_stocks &&
            settings.trade_targets.selected_themes.length > 0 && (
              <SettingSection title="선택한 테마">
                <div className="text-sm text-text-body">
                  선택한 테마 수: {settings.trade_targets.selected_themes.length}개
                </div>
              </SettingSection>
            )}

          {/* 선택한 개별 종목 */}
          {!settings.trade_targets.use_all_stocks &&
            settings.trade_targets.selected_stocks.length > 0 && (
              <SettingSection title="선택한 개별 종목">
                <ul className="space-y-1 text-sm text-text-body list-disc list-inside max-h-48 overflow-y-auto">
                  {settings.trade_targets.selected_stocks.slice(0, 10).map((stock, idx) => (
                    <li key={idx}>{stock}</li>
                  ))}
                  {settings.trade_targets.selected_stocks.length > 10 && (
                    <li className="text-text-muted">
                      외 {settings.trade_targets.selected_stocks.length - 10}개
                    </li>
                  )}
                </ul>
              </SettingSection>
            )}
        </div>
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
 * 날짜 포맷 헬퍼 (YYYYMMDD -> YYYY.MM.DD)
 */
function formatDate(dateStr: string): string {
  if (dateStr.length !== 8) return dateStr;
  return `${dateStr.slice(0, 4)}.${dateStr.slice(4, 6)}.${dateStr.slice(6, 8)}`;
}
