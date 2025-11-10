import { useBacktestConfigStore } from "@/stores";
import { FormField, UnderLineInput, SectionHeader } from "../common";

/**
 * 일반 조건 설정 섹션
 * - 백테스트 데이터 기준 (일봉/월봉)
 * - 투자 금액, 시작일, 종료일, 수수료율, 슬리피지
 */
export function GeneralSettingsSection() {
  const {
    is_day_or_month,
    setIsDayOrMonth,
    initial_investment,
    setInitialInvestment,
    start_date,
    setStartDate,
    end_date,
    setEndDate,
    commission_rate,
    setCommissionRate,
    slippage,
    setSlippage,
  } = useBacktestConfigStore();

  return (
    <div className="space-y-3">
      <SectionHeader title="일반 조건 설정" />

      <div className="bg-bg-surface rounded-lg shadow-card p-8 border-l-4 border-brand-primary">

      {/* 백테스트 데이터 기준 */}
      <div className="mb-8">
        <label className="block text-base font-medium text-text-strong mb-3">
          백테스트 데이터 기준
        </label>
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="dataType"
              checked={is_day_or_month === "daily"}
              onChange={() => setIsDayOrMonth("daily")}
              className="w-5 h-5 accent-accent-primary"
            />
            <span className="text-text-body">일봉</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="dataType"
              checked={is_day_or_month === "monthly"}
              onChange={() => setIsDayOrMonth("monthly")}
              className="w-5 h-5 accent-accent-primary"
            />
            <span className="text-text-body">월봉</span>
          </label>
        </div>
      </div>

      <div className="h-px bg-border-subtle mb-8" />

      {/* 투자 설정 */}
      <div className="grid grid-cols-4 gap-6">
        <FormField
          label="투자 금액"
          type="number"
          value={initial_investment}
          onChange={(e) => setInitialInvestment(Number(e.target.value))}
          suffix="만원"
        />

        <div>
          <label className="block text-sm font-medium text-text-strong mb-2">
            투자 시작일
          </label>
          <UnderLineInput
            type="date"
            value={
              start_date
                ? `${start_date.slice(0, 4)}-${start_date.slice(4, 6)}-${start_date.slice(6, 8)}`
                : ""
            }
            onChange={(e) => {
              const date = e.target.value.replace(/-/g, "");
              setStartDate(date);
            }}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-strong mb-2">
            투자 종료일
          </label>
          <UnderLineInput
            type="date"
            value={
              end_date
                ? `${end_date.slice(0, 4)}-${end_date.slice(4, 6)}-${end_date.slice(6, 8)}`
                : ""
            }
            onChange={(e) => {
              const date = e.target.value.replace(/-/g, "");
              setEndDate(date);
            }}
          />
        </div>

        <FormField
          label="수수료율"
          type="number"
          value={commission_rate}
          onChange={(e) => setCommissionRate(Number(e.target.value))}
          step={0.1}
          suffix="%"
        />

        <FormField
          label="슬리피지"
          type="number"
          value={slippage}
          onChange={(e) => setSlippage(Number(e.target.value))}
          step={0.1}
          suffix="%"
        />
      </div>
      </div>
    </div>
  );
}
