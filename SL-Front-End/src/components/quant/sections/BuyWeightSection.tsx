import { Title } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";
import { useState } from "react";
import { FormField, SectionHeader, FieldPanel, ToggleSwitch } from "../common";

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
    <div id="section-buy-weight" className="space-y-3">
      <SectionHeader title="매수 비중 설정" />

      <FieldPanel conditionType="buy">
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
            <div className="flex items-center justify-between mb-3">
              <Title variant="subtitle">종목당 최대 매수 금액</Title>
              <ToggleSwitch
                checked={enableMaxBuyValue}
                onChange={(checked) => {
                  setEnableMaxBuyValue(checked);
                  if (!checked) setMaxBuyValue(null);
                  else setMaxBuyValue(0);
                }}
                variant="buy"
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
            <div className="flex items-center justify-between mb-3">
              <Title variant="subtitle">1일 최대 매수 종목 수</Title>
              <ToggleSwitch
                checked={enableMaxDailyStock}
                onChange={(checked) => {
                  setEnableMaxDailyStock(checked);
                  if (!checked) setMaxDailyStock(null);
                  else setMaxDailyStock(0);
                }}
                variant="buy"
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
      </FieldPanel>
    </div>
  );
}
