/**
 * 통계 지표 컴포넌트
 * - 라벨과 값을 표시하는 재사용 가능한 컴포넌트
 * - 툴팁 및 색상 커스터마이징 지원
 */
interface StatMetricProps {
  label: string;
  value: string;
  color?: string;
  size?: "normal" | "large";
  tooltip?: string;
}

export function StatMetric({
  label,
  value,
  color = "text-text-strong",
  size = "normal",
  tooltip,
}: StatMetricProps) {
  return (
    <div>
      <div
        className={`font-bold ${color} mb-1 ${
          size === "large" ? "text-xl" : "text-2xl"
        }`}
      >
        {value}
      </div>
      <div className="text-sm text-text-body flex items-center gap-1">
        {label}
        {tooltip && (
          <span className="text-text-muted cursor-help" title={tooltip}>
            ⓘ
          </span>
        )}
      </div>
    </div>
  );
}
