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
  /** 추가 CSS 클래스 */
  className?: string;
}

/**
 * 3가지 형태를 지닌 공용 커스텀 드롭다운 컴포넌트
 * - large: 88px 너비, 48px 높이, 20px 폰트, 28px 아이콘
 * - medium: 200px 너비, 36px 높이, 일반 폰트, 28px 아이콘
 * - small: 104px 너비, 22px 높이, 12px 폰트, 14px 아이콘
 *
 * @example
 * ```tsx
 * // Large variant
 * <Dropdown
 *   value={value}
 *   options={[{ value: "1", label: "옵션 1" }]}
 *   onChange={setValue}
 *   variant="large"
 * />
 *
 * // Medium variant
 * <Dropdown
 *   value={value}
 *   options={options}
 *   onChange={setValue}
 *   variant="medium"
 * />
 *
 * // Small variant
 * <Dropdown
 *   value={value}
 *   options={options}
 *   onChange={setValue}
 *   variant="small"
 * />
 * ```
 */
export function Dropdown({
  value,
  options,
  onChange,
  variant = "medium",
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

  // Variant별 스타일 설정
  const variantStyles = {
    large: {
      button:
        "w-[88px] h-12 border-[0.5px] border-tag-neutral rounded-md p-[10px]",
      text: "text-[20px] font-semibold",
      icon: { width: 28, height: 28 },
      menu: "w-[88px] mt-1",
      option: "px-[10px] py-2 text-[20px] font-semibold",
    },
    medium: {
      button: "w-[200px] h-9 border-[0.5px] border-tag-neutral rounded-md p-1",
      text: "font-normal",
      icon: { width: 28, height: 28 },
      menu: "w-[200px] mt-1",
      option: "px-1 py-2 font-normal",
    },
    small: {
      button:
        "w-[104px] h-[22px] border-[0.5px] border-tag-neutral rounded-md p-1",
      text: "font-normal text-[12px]",
      icon: { width: 14, height: 14 },
      menu: "w-[104px] mt-1",
      option: "px-1 py-1 font-normal text-[12px]",
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
          className={`flex-1 text-left text-text-strong ${currentVariant.text}`}
        >
          {selectedOption?.label || "선택"}
        </span>

        {/* 오른쪽 화살표 영역 */}
        <Image
          src={isOpen ? "/icons/arrow_up.svg" : "/icons/arrow_down.svg"}
          alt=""
          width={currentVariant.icon.width}
          height={currentVariant.icon.height}
          className="opacity-60"
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
