/**
 * GradientDivider 컴포넌트 Props 타입
 */
interface GradientDividerProps {
  /** divider 방향 (기본: horizontal) */
  direction?: "horizontal" | "vertical";
  /** 추가 CSS 클래스 */
  className?: string;
  /** gradient ID (여러 개 사용 시 고유 ID 필요) */
  gradientId?: string;
}

/**
 * 재사용 가능한 GradientDivider 컴포넌트
 * SVG gradient 라인을 제공합니다.
 *
 * @example
 * ```tsx
 * // 가로 구분선
 * <GradientDivider />
 *
 * // 세로 구분선
 * <GradientDivider direction="vertical" />
 *
 * // 커스텀 ID (여러 개 사용 시)
 * <GradientDivider gradientId="paint0_linear_divider1" />
 * <GradientDivider gradientId="paint0_linear_divider2" />
 * ```
 */
export function GradientDivider({
  direction = "horizontal",
  className = "",
  gradientId = "paint0_linear_divider",
}: GradientDividerProps) {
  if (direction === "vertical") {
    // 세로 구분선
    return (
      <div className={`h-[32px] w-[4px] ${className}`}>
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1 32">
          <line
            stroke={`url(#${gradientId})`}
            strokeLinecap="round"
            strokeWidth="0.2"
            x1="0.1"
            x2="0.1"
            y1="0"
            y2="32"
          />
          <defs>
            <linearGradient gradientUnits="userSpaceOnUse" id={gradientId} x1="0" x2="0" y1="0" y2="32">
              <stop stopColor="#282828" />
              <stop offset="0.2" stopColor="#737373" />
              <stop offset="0.8" stopColor="#737373" />
              <stop offset="1" stopColor="#282828" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    );
  }

  // 가로 구분선 (기본)
  return (
    <div className={`h-[1px] w-full mb-[30px] ${className}`}>
      <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 1000 1">
        <line stroke={`url(#${gradientId})`} strokeOpacity="0.4" x2="1000" y1="0.5" y2="0.5" />
        <defs>
          <linearGradient gradientUnits="userSpaceOnUse" id={gradientId} x1="0" x2="1000" y1="0.5" y2="0.5">
            <stop stopColor="#282828" />
            <stop offset="0.2" stopColor="#737373" />
            <stop offset="0.8" stopColor="#737373" />
            <stop offset="1" stopColor="#282828" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
