import type React from "react";

/**
 * Title - 페이지 및 섹션 제목 컴포넌트
 * 모든 페이지에서 일관된 제목 스타일을 제공합니다
 *
 * @param variant - 제목 크기 변형
 *   - default: 섹션 제목 (1.75rem, font-semibold)
 *   - subtitle: 필드 항목 제목 (20px, font-normal)
 */
interface TitleProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "subtitle";
}

export function Title({
  children,
  className = "",
  variant = "default",
}: TitleProps) {
  const variantStyles = {
    default: "text-[1.75rem] font-semibold",
    subtitle: "text-[1.25rem] font-normal",
  };

  return (
    <h2 className={`${variantStyles[variant]} ${className}`}>{children}</h2>
  );
}
