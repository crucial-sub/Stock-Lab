import type { ReactNode } from "react";
import { twMerge } from "tailwind-merge";

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "tertiary" | "ghost" | "success";
  size?: "sm" | "md" | "lg" | "responsive";
  /** 전체 너비 사용 여부 */
  fullWidth?: boolean;
  className?: string;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
}

/**
 * 반응형 버튼 컴포넌트
 *
 * @features
 * - 5가지 variant 지원 (primary, secondary, tertiary, ghost, success)
 * - 4가지 size 지원 (sm, md, lg, responsive)
 * - responsive 크기는 뷰포트에 따라 자동 조절
 * - fullWidth 옵션으로 전체 너비 사용 가능
 * - 터치 친화적인 최소 높이 (44px) 보장
 */

const VARIANT_STYLES: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-brand-primary text-white",
  secondary: "bg-zinc-100 text-black",
  tertiary: "bg-bg-positive text-brand-primary",
  ghost: "bg-transparent text-black",
  success: "bg-green-500 text-white hover:bg-green-600",
};

const SIZE_STYLES: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "py-2 px-4 text-sm sm:text-base min-h-[2.75rem]",
  md: "py-2.5 px-5 text-base sm:text-lg min-h-[2.75rem]",
  lg: "py-3 px-6 text-base sm:text-lg min-h-[3rem]",
  // 반응형: 모바일에서 더 큰 터치 영역
  responsive: "py-3 px-4 sm:py-2 sm:px-6 text-base min-h-[2.75rem]",
};

export function Button({
  children,
  onClick,
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
  disabled = false,
  type = "button",
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={twMerge(
        // 기본 스타일
        "flex items-center justify-center gap-1 overflow-hidden rounded-md font-sans font-semibold",
        // 트랜지션
        "transition-colors duration-200",
        // Variant 스타일
        VARIANT_STYLES[variant],
        // Size 스타일
        SIZE_STYLES[size],
        // 전체 너비
        fullWidth && "w-full",
        // 비활성화 상태
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
        // 사용자 정의 클래스
        className,
      )}
    >
      {children}
    </button>
  );
}
