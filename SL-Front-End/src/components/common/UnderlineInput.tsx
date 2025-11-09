import type { InputHTMLAttributes, ReactNode } from "react";

/**
 * UnderlineInput 컴포넌트 Props 타입
 */
interface UnderlineInputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** 입력 필드 너비 (기본: w-[90%]) */
  inputWidth?: string;
  /** 접미사 텍스트 또는 요소 */
  suffix?: ReactNode;
  /** 테두리 색상 (기본: border-[#a0a0a0]) */
  borderColor?: "white" | "gray";
  /** 텍스트 색상 (기본: text-[#a0a0a0]) */
  textColor?: "white" | "gray";
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 재사용 가능한 UnderlineInput 컴포넌트
 * border-bottom 스타일과 suffix를 지원합니다.
 *
 * @example
 * ```tsx
 * // 기본 입력 필드
 * <UnderlineInput
 *   value={value}
 *   onChange={handleChange}
 *   suffix="만원"
 * />
 *
 * // 흰색 테두리 & 텍스트
 * <UnderlineInput
 *   value={value}
 *   onChange={handleChange}
 *   borderColor="white"
 *   textColor="white"
 *   suffix="만원"
 * />
 *
 * // 커스텀 너비
 * <UnderlineInput
 *   value={value}
 *   onChange={handleChange}
 *   inputWidth="w-[80px]"
 *   suffix="%"
 * />
 * ```
 */
export function UnderlineInput({
  inputWidth = "w-[90%]",
  suffix,
  borderColor = "gray",
  textColor = "gray",
  className = "",
  ...inputProps
}: UnderlineInputProps) {
  const borderColorClass =
    borderColor === "white" ? "border-white" : "border-text-muted";
  const textColorClass =
    textColor === "white" ? "text-white" : "text-text-muted";

  return (
    <div className={`relative h-[40px] border-b ${borderColorClass} ${className}`}>
      <input
        {...inputProps}
        className={`absolute left-0 top-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] ${textColorClass} tracking-[-0.6px] ${inputWidth}`}
      />
      {suffix && (
        <div className={`absolute right-0 top-1/2 -translate-y-1/2 flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[20px] text-nowrap ${textColorClass} tracking-[-0.6px]`}>
          <p className="leading-[normal] whitespace-pre">{suffix}</p>
        </div>
      )}
    </div>
  );
}
