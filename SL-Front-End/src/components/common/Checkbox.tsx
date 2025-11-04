import type { ReactNode } from "react";

/**
 * Checkbox 컴포넌트 Props 타입
 */
interface CheckboxProps {
  /** 체크 상태 */
  checked: boolean;
  /** 체크 상태 변경 핸들러 */
  onChange?: (checked: boolean) => void;
  /** 라벨 텍스트 */
  label?: ReactNode;
  /** 비활성화 상태 */
  disabled?: boolean;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 재사용 가능한 Checkbox 컴포넌트
 * - Figma 디자인과 일치하는 체크박스 UI
 * - 체크 상태에 따라 색상과 체크 마크 표시 변경
 *
 * @example
 * ```tsx
 * <Checkbox
 *   checked={isChecked}
 *   onChange={(checked) => setIsChecked(checked)}
 *   label="건설"
 * />
 * ```
 */
export function Checkbox({
  checked,
  onChange,
  label,
  disabled = false,
  className = "",
}: CheckboxProps) {
  /**
   * SVG 패스 데이터
   * - p3b4f0880: 체크박스 외곽선
   * - p29256980: 체크 마크
   */
  const svgPaths = {
    outline:
      "M5 21C4.45 21 3.97917 20.8042 3.5875 20.4125C3.19583 20.0208 3 19.55 3 19V5C3 4.45 3.19583 3.97917 3.5875 3.5875C3.97917 3.19583 4.45 3 5 3H19C19.55 3 20.0208 3.19583 20.4125 3.5875C20.8042 3.97917 21 4.45 21 5V19C21 19.55 20.8042 20.0208 20.4125 20.4125C20.0208 20.8042 19.55 21 19 21H5ZM5 19H19V5H5V19Z",
    checkmark:
      "M10.6 16.2L17.65 9.15L16.25 7.75L10.6 13.4L7.75 10.55L6.35 11.95L10.6 16.2ZM5 21C4.45 21 3.97917 20.8042 3.5875 20.4125C3.19583 20.0208 3 19.55 3 19V5C3 4.45 3.19583 3.97917 3.5875 3.5875C3.97917 3.19583 4.45 3 5 3H19C19.55 3 20.0208 3.19583 20.4125 3.5875C20.8042 3.97917 21 4.45 21 5V19C21 19.55 20.8042 20.0208 20.4125 20.4125C20.0208 20.8042 19.55 21 19 21H5ZM5 19H19V5H5V19Z",
  };

  /**
   * 체크박스 클릭 핸들러
   */
  const handleClick = () => {
    if (!disabled && onChange) {
      onChange(!checked);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`flex items-center gap-[8px] ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer group"} ${className}`}
    >
      {/* 체크박스 아이콘 */}
      <div className="size-[24px]">
        <svg
          className="block size-full"
          fill="none"
          preserveAspectRatio="none"
          viewBox="0 0 24 24"
        >
          <g>
            <mask
              height="24"
              id="mask0_checkbox"
              maskUnits="userSpaceOnUse"
              style={{ maskType: "alpha" }}
              width="24"
              x="0"
              y="0"
            >
              <rect fill="#D9D9D9" height="24" width="24" />
            </mask>
            <g mask="url(#mask0_checkbox)">
              {/* 체크박스 외곽선 */}
              <path
                d={svgPaths.outline}
                fill={checked ? "white" : "#A0A0A0"}
              />
              {/* 체크 마크 (체크 상태일 때만 표시) */}
              {checked && (
                <g>
                  <mask
                    height="24"
                    id="mask1_checkbox"
                    maskUnits="userSpaceOnUse"
                    style={{ maskType: "alpha" }}
                    width="24"
                    x="0"
                    y="0"
                  >
                    <rect fill="#D9D9D9" height="24" width="24" />
                  </mask>
                  <g mask="url(#mask1_checkbox)">
                    <path d={svgPaths.checkmark} fill="white" />
                  </g>
                </g>
              )}
            </g>
          </g>
        </svg>
      </div>

      {/* 라벨 텍스트 */}
      {label && (
        <span
          className={`font-['Pretendard'] text-[18px] tracking-[-0.54px] whitespace-nowrap ${
            checked
              ? "font-medium text-white"
              : "font-extralight text-[#a0a0a0]"
          } ${!disabled && "group-hover:text-white transition-colors"}`}
        >
          {label}
        </span>
      )}
    </button>
  );
}
