import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
}

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const baseClass = "quant-button";
  const variantClass = `${baseClass}-${variant}`;

  return (
    <button type="button" {...props} className={`${variantClass} ${className}`}>
      {children}
    </button>
  );
}
