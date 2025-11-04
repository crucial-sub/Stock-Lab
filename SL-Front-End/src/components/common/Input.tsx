import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  suffix?: string;
}

export function Input({ suffix, className = "", ...props }: InputProps) {
  if (suffix) {
    return (
      <div className="relative">
        <input {...props} className={`quant-input ${className}`} />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-text-tertiary">
          {suffix}
        </span>
      </div>
    );
  }

  return <input {...props} className={`quant-input ${className}`} />;
}
