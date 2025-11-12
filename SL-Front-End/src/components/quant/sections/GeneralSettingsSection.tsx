import { Title, UnderlineInput } from "@/components/common";
import { FormField } from "@/components/quant/common";
import { FieldPanel, SectionHeader } from "@/components/quant/ui";
import { useBacktestConfigStore } from "@/stores";

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
    <div id="section-general-settings" className="space-y-3">
      <SectionHeader title="일반 조건 설정" />
      <FieldPanel conditionType="buy">

        {/* 백테스트 데이터 기준 */}
        <div className="mb-8">
          <Title variant="subtitle" className="mb-3">
            백테스트 데이터 기준
          </Title>
          <div className="flex items-center gap-3">
            <button className={`font-normal ${is_day_or_month === "daily" ? "bg-bg-positive border-brand-primary border font-semibold text-brand-primary" : "bg-[#f5f5f5]"} rounded-md px-6 py-2`} onClick={() => setIsDayOrMonth("daily")}>일봉</button>
            <button className={`font-normal ${is_day_or_month === "monthly" ? "bg-bg-positive border-brand-primary border font-semibold text-brand-primary" : "bg-[#f5f5f5]"} rounded-md px-6 py-2`} onClick={() => setIsDayOrMonth("monthly")}>월봉</button>
          </div>
        </div>

        {/* 투자 설정 */}
        <div className="grid grid-cols-5 gap-6">
          <FormField
            label="투자 금액"
            type="number"
            value={initial_investment}
            onChange={(e) => setInitialInvestment(Number(e.target.value))}
            suffix="만원"
          />

          <div>
            <Title variant="subtitle" className="mb-2">
              투자 시작일
            </Title>
            <UnderlineInput
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
            <Title variant="subtitle" className="mb-2">
              투자 종료일
            </Title>
            <UnderlineInput
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
      </FieldPanel>
    </div>
  );
}
