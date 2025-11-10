import React from "react";

/**
 * Title - 페이지 및 섹션 제목 컴포넌트
 * 모든 페이지에서 일관된 제목 스타일을 제공합니다
 */
interface TitleProps {
  children: React.ReactNode;
  className?: string;
}

export function Title({ children, className = "" }: TitleProps) {
  return (
    <h2 className={`text-[1.75rem] font-semibold ${className}`}>
      {children}
    </h2>
  );
}
