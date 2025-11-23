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
      <div className={`text-[1.5rem] text-nowrap font-semibold leading-tight ${toneClass}`}>
        {value}
      </div>
      <div className="text-sm text-muted flex items-center gap-1">
        <span>{label}</span>
        {tooltip ? (
          <span className="text-muted cursor-help" title={tooltip}>
            ⓘ
          </span>
        ) : null}
      </div>
    </div>
  );
}
