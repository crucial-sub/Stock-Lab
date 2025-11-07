import type { InputHTMLAttributes, ReactNode } from "react";

/**
 * RadioButton 컴포넌트 Props 타입
 */
interface RadioButtonProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** 라벨 텍스트 또는 요소 */
  label: ReactNode;
  /** 체크 여부 */
  checked: boolean;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 재사용 가능한 RadioButton 컴포넌트
 * Pretendard:Bold 폰트와 일관된 스타일을 제공합니다.
 *
 * @example
 * ```tsx
 * // 기본 라디오 버튼
 * <RadioButton
 *   name="dataType"
 *   checked={value === "daily"}
 *   onChange={() => setValue("daily")}
 *   label="일봉"
 * />
 *
 * // 커스텀 스타일
 * <RadioButton
 *   name="option"
 *   checked={selected}
 *   onChange={handleChange}
 *   label="옵션 1"
 *   className="mr-4"
 * />
 * ```
 */
export function RadioButton({
  label,
  checked,
  className = "",
  ...inputProps
}: RadioButtonProps) {
  return (
    <label className={`flex items-center gap-2 cursor-pointer ${className}`}>
      <input
        type="radio"
        checked={checked}
        className="w-4 h-4 accent-white"
        {...inputProps}
      />
      <div className="flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-[18px] text-nowrap tracking-[-0.54px]">
        <p className={`leading-[normal] whitespace-pre ${checked ? "text-white" : "text-text-muted"}`}>
          {label}
        </p>
      </div>
    </label>
  );
}
