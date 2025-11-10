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
  return (
    <div className="w-[500px]">
      <h3 className="text-sm font-semibold text-text-strong mb-3">
        수익률 (%)
      </h3>
      <div className="flex items-end gap-2 h-32">
        {periodReturns.map((item, i) => {
          const isPositive = item.value >= 0;
          const barHeight = Math.abs(item.value) * 3;

          return (
            <div key={i} className="flex-1 flex flex-col items-center">
              <div className="w-full h-24 flex items-end justify-center">
                <div
                  className={`w-full rounded-t transition-all ${
                    isPositive
                      ? "bg-accent-primary"
                      : i < 3
                        ? "bg-blue-500"
                        : "bg-red-500"
                  }`}
                  style={{
                    height: `${barHeight}px`,
                    minHeight: "4px",
                  }}
                />
              </div>
              <div className="text-[10px] text-text-body mt-2 text-center leading-tight">
                {item.value > 0 ? "+" : ""}
                {item.value.toFixed(2)}%
              </div>
              <div className="text-[10px] text-text-muted mt-1 text-center leading-tight">
                {item.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
