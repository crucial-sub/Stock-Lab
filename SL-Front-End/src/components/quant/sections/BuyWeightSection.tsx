import { useState } from "react";
import { useBacktestConfigStore } from "@/stores";
import { FormField, SectionHeader } from "../common";

/**
 * 매수 비중 설정 섹션
 * - 종목당 매수 비중
 * - 최대 보유 종목 수
 * - 종목당 최대 매수 금액 (선택)
 * - 1일 최대 매수 종목 수 (선택)
 */
export function BuyWeightSection() {
  const {
    per_stock_ratio,
    setPerStockRatio,
    max_holdings,
    setMaxHoldings,
    max_buy_value,
    setMaxBuyValue,
    max_daily_stock,
    setMaxDailyStock,
  } = useBacktestConfigStore();

  const [enableMaxBuyValue, setEnableMaxBuyValue] = useState(max_buy_value !== null);
  const [enableMaxDailyStock, setEnableMaxDailyStock] = useState(max_daily_stock !== null);

  return (
    <div className="space-y-3">
      <SectionHeader title="매수 비중 설정" />

      <div className="bg-bg-surface rounded-lg shadow-card p-8 border-l-4 border-brand-primary">
        <div className="grid grid-cols-4 gap-6">
        <FormField
          label="종목당 매수 비중"
          type="number"
          value={per_stock_ratio}
          onChange={(e) => setPerStockRatio(Number(e.target.value))}
          step={1}
          suffix="%"
        />

        <FormField
          label="최대 보유 종목 수"
          type="number"
          value={max_holdings}
          onChange={(e) => setMaxHoldings(Number(e.target.value))}
          step={1}
          suffix="종목"
        />

        <div>
          <div className="flex items-center gap-2 mb-2">
            <label className="text-sm font-medium text-text-strong">
              종목당 최대 매수 금액
            </label>
            <input
              type="checkbox"
              checked={enableMaxBuyValue}
              onChange={(e) => {
                setEnableMaxBuyValue(e.target.checked);
                if (!e.target.checked) setMaxBuyValue(null);
                else setMaxBuyValue(0);
              }}
              className="w-5 h-5 accent-brand-primary"
            />
          </div>
          <FormField
            type="number"
            value={max_buy_value ?? 0}
            onChange={(e) => setMaxBuyValue(Number(e.target.value))}
            disabled={!enableMaxBuyValue}
            suffix="만원"
            label=""
          />
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <label className="text-sm font-medium text-text-strong">
              1일 최대 매수 종목 수
            </label>
            <input
              type="checkbox"
              checked={enableMaxDailyStock}
              onChange={(e) => {
                setEnableMaxDailyStock(e.target.checked);
                if (!e.target.checked) setMaxDailyStock(null);
                else setMaxDailyStock(0);
              }}
              className="w-5 h-5 accent-brand-primary"
            />
          </div>
          <FormField
            type="number"
            value={max_daily_stock ?? 0}
            onChange={(e) => setMaxDailyStock(Number(e.target.value))}
            disabled={!enableMaxDailyStock}
            suffix="종목"
            label=""
          />
        </div>
      </div>
      </div>
    </div>
  );
}
