import { SVG_PATH } from "@/constants";
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
                d={SVG_PATH.outline}
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
                    <path d={SVG_PATH.checkmark} fill="white" />
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
          className={`font-['Pretendard'] text-[18px] tracking-[-0.54px] whitespace-nowrap ${checked
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
