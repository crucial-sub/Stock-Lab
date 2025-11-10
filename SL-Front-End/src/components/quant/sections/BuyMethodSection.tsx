import { useState, useEffect } from "react";
import { useBacktestConfigStore } from "@/stores";
import { SelectField, FormField, SectionHeader } from "../common";

/**
 * 매수 방법 선택 섹션
 * - 매수 가격 기준 (전일 종가 / 당일 시가)
 * - 가격 조정 (%)
 */
export function BuyMethodSection() {
  const { buy_price_basis, buy_price_offset, setBuyPriceBasis, setBuyPriceOffset } =
    useBacktestConfigStore();

  const [buyCostBasisSelect, setBuyCostBasisSelect] = useState<string>(
    buy_price_basis || "전일 종가"
  );
  const [buyCostBasisValue, setBuyCostBasisValue] = useState<number>(
    buy_price_offset || 0
  );

  // Sync to global store
  useEffect(() => {
    setBuyPriceBasis(buyCostBasisSelect);
    setBuyPriceOffset(buyCostBasisValue);
  }, [buyCostBasisSelect, buyCostBasisValue, setBuyPriceBasis, setBuyPriceOffset]);

  return (
    <div className="space-y-3">
      <SectionHeader title="매수 방법 선택" />

      <div className="bg-bg-surface rounded-lg shadow-card p-8 border-l-4 border-brand-primary">
        <div className="grid grid-cols-2 gap-6">
        <SelectField
          label="매수 가격 기준"
          value={buyCostBasisSelect}
          onChange={setBuyCostBasisSelect}
          options={[
            { value: "{전일 종가}", label: "전일 종가" },
            { value: "{당일 시가}", label: "당일 시가" },
          ]}
        />

        <FormField
          label="가격 조정"
          type="number"
          value={buyCostBasisValue}
          onChange={(e) => setBuyCostBasisValue(Number(e.target.value))}
          suffix="%"
        />
      </div>
      </div>
    </div>
  );
}
