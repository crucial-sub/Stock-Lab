import { SVG_PATH } from "@/constants";
import type { SelectHTMLAttributes } from "react";

/**
 * CustomSelect 컴포넌트 Props 타입
 */
interface CustomSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** 입력 필드 너비 (기본: w-full) */
  width?: string;
  /** 테두리 색상 (기본: border-[#a0a0a0]) */
  borderColor?: "white" | "gray";
  /** 텍스트 색상 (기본: text-[#a0a0a0]) */
  textColor?: "white" | "gray";
  /** 추가 CSS 클래스 */
  className?: string;
  /** 왼쪽 패딩 (기본: left-5) */
  leftPadding?: string;
}

/**
 * 재사용 가능한 CustomSelect 컴포넌트
 * 커스텀 드롭다운 화살표 아이콘을 지원합니다.
 *
 * @example
 * ```tsx
 * // 기본 셀렉트
 * <CustomSelect value={value} onChange={handleChange}>
 *   <option value=">=">≥</option>
 *   <option value="<=">≤</option>
 * </CustomSelect>
 *
 * // 커스텀 너비 및 스타일
 * <CustomSelect
 *   value={value}
 *   onChange={handleChange}
 *   width="w-[92px]"
 *   leftPadding="left-5"
 * >
 *   <option value="1">옵션 1</option>
 *   <option value="2">옵션 2</option>
 * </CustomSelect>
 * ```
 */
export function CustomSelect({
  width = "w-full",
  borderColor = "gray",
  textColor = "gray",
  className = "",
  leftPadding = "left-5",
  children,
  ...selectProps
}: CustomSelectProps) {
  const borderColorClass =
    borderColor === "white" ? "border-white" : "border-text-muted";
  const textColorClass =
    textColor === "white" ? "text-white" : "text-text-muted";

  return (
    <div className={`relative h-[60px] ${width} border-b ${borderColorClass} ${className}`}>
      <select
        {...selectProps}
        className={`absolute ${leftPadding} top-[45%] -translate-y-1/2 bg-transparent border-none outline-none font-bold text-[20px] tracking-[-0.6px] w-full appearance-none cursor-pointer ${textColorClass}`}
      >
        {children}
      </select>
      <div className="absolute right-0 top-1/2 -translate-y-1/2 size-[32px] pointer-events-none">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 32 32">
          <path d={SVG_PATH.p2a094a00} fill="var(--color-text-muted)" />
        </svg>
      </div>
    </div>
  );
}
