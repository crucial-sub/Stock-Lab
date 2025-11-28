import type { InputHTMLAttributes } from "react";
import { twMerge } from "tailwind-merge";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** 입력 필드 우측에 표시할 접미사 (예: 원, %) */
  suffix?: string;
  /** 전체 너비 사용 여부 */
  fullWidth?: boolean;
  /** 입력 크기 */
  inputSize?: "sm" | "md" | "lg";
}

/**
 * 반응형 입력 컴포넌트
 *
 * @features
 * - 3가지 크기 지원 (sm, md, lg)
 * - 접미사 표시 지원
 * - fullWidth 옵션으로 전체 너비 사용 가능
 * - 터치 친화적인 최소 높이 (44px) 보장
 * - 모바일에서 16px 폰트로 iOS 줌 방지
 */

const SIZE_STYLES = {
  sm: "py-2 px-3 text-sm min-h-[2.5rem]",
  md: "py-2.5 px-4 text-base min-h-[2.75rem]",
  lg: "py-3 px-4 text-base sm:text-lg min-h-[3rem]",
};

export function Input({
  suffix,
  fullWidth = true,
  inputSize = "md",
  className = "",
  ...props
}: InputProps) {
  const baseClasses = twMerge(
    // 기본 스타일
    "quant-input",
    // 크기 스타일
    SIZE_STYLES[inputSize],
    // 너비
    fullWidth ? "w-full" : "w-auto",
    // iOS 줌 방지 (16px 이상)
    "text-base sm:text-sm",
    // 사용자 정의 클래스
    className,
  );

  if (suffix) {
    return (
      <div className={twMerge("relative", fullWidth ? "w-full" : "w-auto")}>
        <input {...props} className={twMerge(baseClasses, "pr-12")} />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-text-tertiary pointer-events-none">
          {suffix}
        </span>
      </div>
    );
  }

  return <input {...props} className={baseClasses} />;
}
