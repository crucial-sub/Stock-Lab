import { Dropdown, Title } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";
import { FieldPanel, SectionHeader, ToggleSwitch, UnderLineInput } from "../common";
import ActiveConditionBtn from "../common/ActiveConditionBtn";

/**
 * 보유 기간 섹션
 * - 최소/최대 종목 보유일 설정
 * - 매도 가격 기준 및 조정
 */
export function HoldPeriodSection() {
  const { hold_days, setHoldDays } = useBacktestConfigStore();

  const [isOpen, setIsOpen] = useState(hold_days !== null);
  const [minHoldDays, setMinHoldDays] = useState<number>(
    hold_days?.min_hold_days ?? 10
  );
  const [maxHoldDays, setMaxHoldDays] = useState<number>(
    hold_days?.max_hold_days ?? 10
  );
  const [sellPriceBasis, setSellPriceBasis] = useState<string>(
    hold_days?.sell_price_basis ?? "전일 종가"
  );
  const [sellPriceOffset, setSellPriceOffset] = useState<number>(
    hold_days?.sell_price_offset ?? 10
  );

  // 전역 스토어 업데이트
  useEffect(() => {
    if (isOpen) {
      setHoldDays({
        min_hold_days: minHoldDays,
        max_hold_days: maxHoldDays,
        sell_price_basis: sellPriceBasis,
        sell_price_offset: sellPriceOffset,
      });
    } else {
      setHoldDays(null);
    }
  }, [
    isOpen,
    minHoldDays,
    maxHoldDays,
    sellPriceBasis,
    sellPriceOffset,
    setHoldDays,
  ]);

  return (
    <div id="section-hold-period" className="space-y-3">
      <SectionHeader
        title="보유 기간"
        description="최소 보유일 입력 시 매수 후 입력 기간 동안 어떤 상황에도 매도하지 않고, 최대 보유일 입력 시 매수 후 입력 기간 후 매도 주문을 합니다."
        action={<ToggleSwitch checked={isOpen} onChange={setIsOpen} />}
      />

      {isOpen ? (
        <FieldPanel conditionType="sell">
          <div className="grid grid-cols-[128fr_128fr_344fr] gap-x-[3.75rem]">
            {/* 최소 종목 보유일 */}
            <div className="flex flex-col justify-center gap-3">
              <Title variant="subtitle" className="mb-3">
                최소 종목 보유일
              </Title>
              <div className="relative max-w-32">
                <UnderLineInput
                  value={minHoldDays}
                  onChange={(e) => setMinHoldDays(Number(e.target.value))}
                  className="!h-full"
                />
                <span className="absolute right-0 top-[5px]">
                  일
                </span>
              </div>
            </div>

            {/* 최대 종목 보유일 */}
            <div className="flex flex-col justify-center gap-3">
              <Title variant="subtitle" className="mb-3">
                최대 종목 보유일
              </Title>
              <div className="relative max-w-32">
                <UnderLineInput
                  value={maxHoldDays}
                  onChange={(e) => setMaxHoldDays(Number(e.target.value))}
                  className="!h-full"
                />
                <span className="absolute right-0 top-[5px]">
                  일
                </span>
              </div>
            </div>

            {/* 매도 가격 기준 */}
            <div className="flex flex-col justify-center gap-3">
              <Title variant="subtitle" className="mb-3">
                매도 가격 기준
              </Title>
              <div className="flex gap-4">
                <Dropdown
                  value={sellPriceBasis}
                  onChange={setSellPriceBasis}
                  options={[
                    { value: "전일 종가", label: "전일 종가" },
                    { value: "당일 시가", label: "당일 시가" },
                  ]}
                />
                <div className="relative">
                  <UnderLineInput
                    value={sellPriceOffset}
                    onChange={(e) => setSellPriceOffset(Number(e.target.value))}
                    className=" !h-full"
                  />
                  <span className="absolute right-0 top-[5px]">
                    %
                  </span>
                </div>
              </div>
            </div>
          </div>
        </FieldPanel>
      ) : (
        <ActiveConditionBtn checked={isOpen} onChange={setIsOpen} />
      )}
    </div>
  );
}
