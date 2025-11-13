import Image from "next/image";
import type { ReactNode } from "react";

/**
 * Checkbox 컴포넌트 Props 타입
 */
interface CheckboxProps {
  /** 체크 상태 */
  checked: boolean;
  /** 체크 상태 변경 핸들러 */
  onChange?: (checked: boolean) => void;
  /** 라벨 텍스트 */
  label?: ReactNode;
  /** 비활성화 상태 */
  disabled?: boolean;
  /** 추가 CSS 클래스 */
  className?: string;
  /** 색상 variant - primary(파란색), danger(빨간색) */
  variant?: "primary" | "danger";
}

/**
 * 재사용 가능한 Checkbox 컴포넌트
 * - public/icons 폴더의 SVG 아이콘 사용
 * - check-box-blank.svg: 체크 안 됨
 * - check-box-blue.svg: 파란색 체크
 * - check-box-red.svg: 빨간색 체크
 *
 * @example
 * ```tsx
 * <Checkbox
 *   checked={isChecked}
 *   onChange={(checked) => setIsChecked(checked)}
 *   label="건설"
 *   variant="danger"
 * />
 * ```
 */
export function Checkbox({
  checked,
  onChange,
  label,
  disabled = false,
  className = "",
  variant = "primary",
}: CheckboxProps) {
  /**
   * 체크박스 클릭 핸들러
   */
  const handleClick = () => {
    if (!disabled && onChange) {
      onChange(!checked);
    }
  };

  // variant에 따른 아이콘 파일명 결정
  const getIconName = () => {
    if (!checked) return "check-box-blank";
    return variant === "danger" ? "check-box-red" : "check-box-blue";
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={disabled}
      className={`flex items-center gap-[8px] ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer group"
        } ${className}`}
    >
      {/* 체크박스 아이콘 */}
      <Image
        src={`/icons/${getIconName()}.svg`}
        alt="checkbox"
        width={24}
        height={24}
        className="flex-shrink-0"
      />

      {/* 라벨 텍스트 */}
      {label && (
        <span
          className={`whitespace-nowrap`}
        >
          {label}
        </span>
      )}
    </button>
  );
}
