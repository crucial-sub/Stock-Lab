import type { ReactNode } from "react";

/**
 * Title 컴포넌트 Props 타입
 */
interface TitleProps {
  /** 타이틀 텍스트 또는 요소 */
  children: ReactNode;
  /** 타이틀 크기 (기본: md) */
  size?: "sm" | "md" | "lg";
  /** 추가 CSS 클래스 */
  className?: string;
  /** 하단 여백 (기본: 크기에 따라 자동 설정) */
  marginBottom?: string;
}

/**
 * 재사용 가능한 Title 컴포넌트
 * Pretendard:Bold 폰트와 일관된 스타일을 제공합니다.
 *
 * @example
 * ```tsx
 * // 기본 타이틀 (18px)
 * <Title>투자 금액</Title>
 *
 * // 중간 크기 타이틀 (24px)
 * <Title size="lg">기본 설정</Title>
 *
 * // 커스텀 여백
 * <Title size="md" marginBottom="mb-[35px]">매수 조건 설정</Title>
 *
 * // 컬러 포함
 * <Title size="lg">
 *   <span className="text-[#ff6464]">매수</span>
 *   <span> 조건 설정</span>
 * </Title>
 * ```
 */
export function Title({
  children,
  size = "md",
  className = "",
  marginBottom,
}: TitleProps) {
  // size에 따른 기본 스타일 선택
  const sizeStyles = {
    sm: "text-[18px] tracking-[-0.54px]",
    md: "text-[18px] tracking-[-0.54px]",
    lg: "text-[24px] tracking-[-0.72px]",
  };

  // size에 따른 기본 여백 설정
  const defaultMargin = {
    sm: "mb-[15px]",
    md: "mb-[19px]",
    lg: "mb-[35px]",
  };

  const margin = marginBottom || defaultMargin[size];

  return (
    <div
      className={`flex flex-col font-['Pretendard:Bold',sans-serif] justify-center leading-[0] not-italic text-nowrap text-white ${sizeStyles[size]} ${margin} ${className}`}
    >
      <p className="leading-[normal] whitespace-pre">{children}</p>
    </div>
  );
}
