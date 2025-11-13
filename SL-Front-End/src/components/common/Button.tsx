import type { ReactNode } from "react";
import { twMerge } from "tailwind-merge";

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "tertiary" | "ghost";
  size?: "sm" | "md" | "lg";
  className?: string;
  disabled?: boolean;
}

const VARIANT_STYLES: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-brand-primary text-white text-xl",
  secondary: "bg-zinc-100 text-black text-xl",
  tertiary: "bg-bg-positive text-brand-primary text-xl",
  ghost: "bg-transparent text-black",
};

const SIZE_STYLES: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "py-[5px] text-[16px]",
  md: "py-2 text-base",
  lg: "py-3 text-[16px]",
};

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  className,
  disabled = false,
}: ButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={twMerge(
        "flex items-center justify-center gap-1 overflow-hidden rounded-md px-6 font-sans font-semibold",
        VARIANT_STYLES[variant],
        SIZE_STYLES[size],
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
        className,
      )}
    >
      {children}
    </button>
  );
}
