import type React from "react";

/**
 * UnderlineInput - 하단 테두리만 있는 입력 필드
 * 디자인 시안에 따라 대부분의 텍스트/숫자 입력에 사용
 */
interface UnderlineInputProps {
  type?: React.HTMLInputTypeAttribute;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  min?: string | number;
  max?: string | number;
  step?: string | number;
}

export function UnderlineInput({
  type = "text",
  value,
  onChange,
  placeholder,
  className = "",
  disabled = false,
  min,
  max,
  step,
}: UnderlineInputProps) {
  return (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      min={min}
      max={max}
      step={step}
      className={`
        w-[80%] h-10 px-0 py-2
        bg-transparent
        border-b
        ${disabled ? "border-tag-neutral" : "border-black"}
        placeholder:text-tag-neutral
        focus:outline-none
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    />
  );
}
