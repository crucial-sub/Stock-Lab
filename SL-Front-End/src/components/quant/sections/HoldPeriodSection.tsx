import { Title } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";
import { SectionHeader, ToggleSwitch, FieldPanel } from "../common";

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
    <div className="space-y-3">
      <SectionHeader
        title="보유 기간"
        description="최소 보유일 만큼 시 매수 후 일정 기간 이상 매매 어떤 상황에도 매도되지 않습니다. 최대 보유일 경과 시 매매 주 후에도 주문을 합니다."
        action={<ToggleSwitch checked={isOpen} onChange={setIsOpen} />}
      />

      {isOpen && (
        <FieldPanel conditionType="sell">
          <div className="flex items-center gap-6">
            {/* 최소 종목 보유일 */}
            <div className="flex items-center gap-2">
              <Title variant="subtitle" className="mb-3">
                최소 종목 보유일
              </Title>
              <input
                type="number"
                value={minHoldDays}
                onChange={(e) => setMinHoldDays(Number(e.target.value))}
                className="w-24 px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong"
              />
              <span className="text-sm text-text-body">일</span>
            </div>

            {/* 최대 종목 보유일 */}
            <div className="flex items-center gap-2">
              <Title variant="subtitle" className="mb-3">
                최대 종목 보유일
              </Title>
              <input
                type="number"
                value={maxHoldDays}
                onChange={(e) => setMaxHoldDays(Number(e.target.value))}
                className="w-24 px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong"
              />
              <span className="text-sm text-text-body">일</span>
            </div>

            {/* 매도 가격 기준 */}
            <div className="flex items-center gap-2">
              <Title variant="subtitle" className="mb-3">
                매도 가격 기준
              </Title>
              <select
                value={sellPriceBasis}
                onChange={(e) => setSellPriceBasis(e.target.value)}
                className="px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong appearance-none cursor-pointer"
              >
                <option value="전일 종가">전일 종가</option>
                <option value="당일 시가">당일 시가</option>
              </select>
              <input
                type="number"
                value={sellPriceOffset}
                onChange={(e) => setSellPriceOffset(Number(e.target.value))}
                className="w-24 px-3 py-2 bg-transparent border border-border-default rounded-sm text-text-strong"
              />
              <span className="text-sm text-text-body">%</span>
            </div>
          </div>
        </FieldPanel>
      )}
    </div>
  );
}
