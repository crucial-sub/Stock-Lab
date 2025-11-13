import { Title, UnderlineInput } from "@/components/common";
import { InputHTMLAttributes } from "react";

/**
 * 입력 필드 공통 컴포넌트
 * - 라벨, 입력 필드, 후위 텍스트를 포함하는 wrapper
 * - UnderlineInput 사용 (하단 테두리만 있는 디자인)
 */
interface FormFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  label: string;
  suffix?: string;
  error?: string;
  containerClassName?: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function FormField({
  label,
  suffix,
  error,
  containerClassName = "",
  className = "",
  value,
  onChange,
  ...inputProps
}: FormFieldProps) {
  return (
    <div className={containerClassName}>
      <Title variant="subtitle" className="mb-2">
        {label}
      </Title>
      <div className="relative">
        <UnderlineInput
          {...inputProps}
          value={value}
          onChange={onChange}
          className={className}
        />
        {suffix && (
          <span className="absolute right-0 bottom-[0.625rem]">
            {suffix}
          </span>
        )}
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}

/**
 * 선택 필드 (드롭다운) 공통 컴포넌트
 */
interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  disabled?: boolean;
  containerClassName?: string;
  className?: string;
}

export function SelectField({
  label,
  value,
  onChange,
  options,
  disabled = false,
  containerClassName = "",
  className = "",
}: SelectFieldProps) {
  return (
    <div className={containerClassName}>
      <Title variant="subtitle" className="mb-2">
        {label}
      </Title>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`w-full px-3 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary disabled:opacity-50 ${className}`}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
