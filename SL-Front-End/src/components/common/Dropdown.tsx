"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

/**
 * Dropdown 컴포넌트 Props 타입
 */
interface DropdownProps {
  /** 선택된 값 */
  value: string;
  /** 드롭다운 옵션 목록 */
  options: Array<{ value: string; label: string }>;
  /** 값 변경 핸들러 */
  onChange: (value: string) => void;
  /** 드롭다운 variant (크기 및 스타일) */
  variant?: "large" | "medium" | "small";
  /** 전체 너비 사용 여부 (모바일 대응) */
  fullWidth?: boolean;
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 반응형 커스텀 드롭다운 컴포넌트
 *
 * @features
 * - 3가지 크기 variant 지원
 * - fullWidth 옵션으로 모바일에서 전체 너비 사용 가능
 * - 터치 친화적인 최소 높이 (44px) 보장
 * - 외부 클릭 시 자동 닫힘
 *
 * @example
 * ```tsx
 * // 반응형 드롭다운 (모바일에서 전체 너비)
 * <Dropdown
 *   value={value}
 *   options={options}
 *   onChange={setValue}
 *   fullWidth
 * />
 * ```
 */
export function Dropdown({
  value,
  options,
  onChange,
  variant = "medium",
  fullWidth = false,
  className = "",
}: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  // Variant별 스타일 설정 (반응형)
  const variantStyles = {
    large: {
      button: [
        // 기본: 모바일 친화적 높이
        "min-h-[2.75rem] sm:h-12",
        "border-[0.5px] border-tag-neutral rounded-md",
        "px-3 py-2 sm:p-[10px]",
        // 너비: fullWidth이면 전체, 아니면 고정
        fullWidth ? "w-full sm:w-[88px]" : "w-[88px]",
      ].join(" "),
      text: "text-base sm:text-[20px] font-semibold",
      icon: { width: 24, height: 24, smWidth: 28, smHeight: 28 },
      menu: fullWidth ? "w-full sm:w-[88px] mt-1" : "w-[88px] mt-1",
      option: "px-3 py-3 sm:px-[10px] sm:py-2 text-base sm:text-[20px] font-semibold min-h-[2.75rem]",
    },
    medium: {
      button: [
        "min-h-[2.75rem] sm:h-9",
        "border-[0.5px] border-tag-neutral rounded-md",
        "px-3 py-2 sm:p-1",
        fullWidth ? "w-full sm:w-[200px]" : "w-[200px]",
      ].join(" "),
      text: "text-base sm:text-sm font-normal",
      icon: { width: 24, height: 24, smWidth: 28, smHeight: 28 },
      menu: fullWidth ? "w-full sm:w-[200px] mt-1" : "w-[200px] mt-1",
      option: "px-3 py-3 sm:px-1 sm:py-2 font-normal min-h-[2.75rem] sm:min-h-0",
    },
    small: {
      button: [
        "min-h-[2.75rem] sm:min-h-0 sm:h-[22px]",
        "border-[0.5px] border-tag-neutral rounded-md",
        "px-3 py-2 sm:p-1",
        fullWidth ? "w-full sm:w-[104px]" : "w-[104px]",
      ].join(" "),
      text: "text-base sm:text-[12px] font-normal",
      icon: { width: 20, height: 20, smWidth: 14, smHeight: 14 },
      menu: fullWidth ? "w-full sm:w-[104px] mt-1" : "w-[104px] mt-1",
      option: "px-3 py-3 sm:px-1 sm:py-1 font-normal text-base sm:text-[12px] min-h-[2.75rem] sm:min-h-0",
    },
  };

  const currentVariant = variantStyles[variant];
  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* 드롭다운 버튼 */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center justify-between ${currentVariant.button} hover:border-accent-primary transition-colors`}
      >
        {/* 왼쪽 텍스트 영역 */}
        <span
          className={`flex-1 text-left text-text-strong truncate ${currentVariant.text}`}
        >
          {selectedOption?.label || "선택"}
        </span>

        {/* 오른쪽 화살표 영역 - 반응형 아이콘 크기 */}
        <Image
          src={isOpen ? "/icons/arrow_up.svg" : "/icons/arrow_down.svg"}
          alt=""
          width={currentVariant.icon.width}
          height={currentVariant.icon.height}
          className="opacity-60 shrink-0 sm:w-7 sm:h-7"
        />
      </button>

      {/* 드롭다운 메뉴 */}
      {isOpen && (
        <div
          className={`absolute z-20 ${currentVariant.menu} bg-base-0 border border-surface rounded-md shadow-elev-card-soft max-h-60 overflow-y-auto`}
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className={`w-full text-left ${currentVariant.option} transition-colors ${
                option.value === value
                  ? "bg-surface text-brand"
                  : "text-body hover:bg-surface"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
