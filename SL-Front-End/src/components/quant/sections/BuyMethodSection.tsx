import { Dropdown, Title } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";
import { FieldPanel, SectionHeader, UnderLineInput } from "../common";

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

      <FieldPanel conditionType="buy">
        <Title variant="subtitle" className="mb-3">
          매수 조건식 설정
        </Title>
        <div className="flex gap-4 items-center">
          <Dropdown
            value={buyCostBasisSelect}
            options={[
              { value: "전일 종가", label: "전일 종가" },
              { value: "당일 시가", label: "당일 시가" },
            ]}
            onChange={setBuyCostBasisSelect}
            variant="medium"
          />
          <div className="relative">
            <UnderLineInput
              value={buyCostBasisValue}
              onChange={(e) => setBuyCostBasisValue(Number(e.target.value))}
              className="w-32"
            />
            <span className="absolute right-0 bottom-[0.625rem]">
              %
            </span>
          </div>
        </div>
      </FieldPanel>
    </div>
  );
}
