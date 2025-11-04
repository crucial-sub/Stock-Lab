import type { SelectHTMLAttributes } from "react";
import type { SelectOption } from "@/types";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
}

export function Select({ options, className = "", ...props }: SelectProps) {
  return (
    <select {...props} className={`quant-input ${className}`}>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
