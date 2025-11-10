import React from "react";

/**
 * UnderLineInput - 하단 테두리만 있는 입력 필드
 * 디자인 시안에 따라 대부분의 텍스트/숫자 입력에 사용
 */
interface UnderLineInputProps {
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

export function UnderLineInput({
  type = "text",
  value,
  onChange,
  placeholder,
  className = "",
  disabled = false,
  min,
  max,
  step,
}: UnderLineInputProps) {
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
        w-full h-10 px-0 py-2
        bg-transparent
        border-b border-black
        text-text-body
        placeholder:text-text-muted
        focus:outline-none focus:border-accent-primary
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
        ${className}
      `}
    />
  );
}
