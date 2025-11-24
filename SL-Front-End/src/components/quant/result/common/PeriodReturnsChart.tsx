/**
 * 기간별 수익률 바 차트 컴포넌트
 * - 기간별 수익률을 시각화하는 바 차트
 */
interface PeriodReturn {
  label: string;
  value: number;
}

interface PeriodReturnsChartProps {
  periodReturns: PeriodReturn[];
}

export function PeriodReturnsChart({ periodReturns }: PeriodReturnsChartProps) {
  const maxAbsReturn = periodReturns.reduce(
    (max, item) => Math.max(max, Math.abs(item.value)),
    0,
  );
  const maxBarHeight = 64;
  const minBarHeight = 6;

  const getBarHeight = (value: number) => {
    if (value === 0 || maxAbsReturn === 0) {
      return 0;
    }
    return Math.max(
      minBarHeight,
      (Math.abs(value) / maxAbsReturn) * maxBarHeight,
    );
  };

  const formatValue = (value: number) => {
    const sign = value > 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-end gap-1">
        <span className="text-[1.125rem] font-semibold">수익률</span>
      </div>

      <div className="relative w-full h-48">
        <div className="absolute inset-x-0 top-1/2 h-px bg-gray-400" />

        <div className="absolute inset-0 flex items-stretch gap-4 px-2">
          {periodReturns.map((item, index) => {
            const isPositive = item.value > 0;
            const isNegative = item.value < 0;
            const barHeight = getBarHeight(item.value);
            const toneClass = isPositive
              ? "text-price-up"
              : isNegative
                ? "text-price-down"
                : "text-muted";
            const barColor = isPositive
              ? "bg-price-up"
              : isNegative
                ? "bg-price-down"
                : "bg-gray-400";
            const valuePosition = isPositive
              ? { top: "calc(50% + 10px)" }
              : isNegative
                ? { top: "calc(50% - 26px)" }
                : { top: "calc(50% + 10px)" };

            return (
              <div key={`${index}-${item.label}`} className="relative flex-1 h-full">
                {barHeight > 0 ? (
                  <div
                    className={`${barColor} absolute left-1/2 -translate-x-1/2 w-4 rounded-sm`}
                    style={{
                      height: `${barHeight}px`,
                      bottom: isPositive ? "50%" : undefined,
                      top: isNegative ? "50%" : undefined,
                    }}
                  />
                ) : null}

                <div
                  className={`absolute left-1/2 -translate-x-1/2 text-sm font-semibold leading-tight ${toneClass}`}
                  style={valuePosition}
                >
                  {formatValue(item.value)}
                </div>

                <div className="absolute text-nowrap inset-x-0 bottom-2 text-center text-[0.75rem] font-normal">
                  {item.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
