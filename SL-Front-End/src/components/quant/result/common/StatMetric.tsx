/**
 * 통계 지표 컴포넌트
 * - 라벨과 값을 표시하는 재사용 가능한 컴포넌트
 * - 툴팁 및 색상 커스터마이징 지원
 */
interface StatMetricProps {
  label: string;
  value: string;
  tone?: "positive" | "negative" | "neutral";
  tooltip?: string;
}

export function StatMetric({
  label,
  value,
  tone = "neutral",
  tooltip,
}: StatMetricProps) {
  const toneClass =
    tone === "positive"
      ? "text-price-up"
      : tone === "negative"
        ? "text-price-down"
        : "text-body";

  return (
    <div className="flex flex-col gap-1">
      <div className={`text-[1.125rem] text-nowrap font-semibold leading-tight ${toneClass}`}>
        {value}
      </div>
      <div className="text-[0.875rem] text-muted flex items-center gap-1">
        <span>{label}</span>
        {tooltip ? (
          <div className="relative inline-flex items-center">
            <span className="peer inline-flex h-4 w-4 items-center justify-center">
              <img src="/icons/help.svg" alt="tooltip" className="h-4 w-4 opacity-70" />
            </span>
            <div className="pointer-events-none absolute left-1/2 top-full z-10 mt-2 hidden min-w-[160px] -translate-x-1/2 rounded-md border border-gray-200 bg-white px-3 py-2 text-[0.75rem] text-muted peer-hover:block">
              {tooltip}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
