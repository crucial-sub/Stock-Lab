"use client";

import Image from "next/image";
import { useState } from "react";

/**
 * AI 검색 입력창 컴포넌트
 *
 * @description 홈 화면의 AI 전략 요청 입력창입니다.
 * 사용자가 입력한 텍스트를 AI에게 전송할 수 있습니다.
 *
 * @example
 * ```tsx
 * <AISearchInput
 *   placeholder="만들고 싶은 전략을 AI에게 요청하세요!"
 *   onSubmit={(value) => console.log("전송:", value)}
 * />
 * ```
 */

interface AISearchInputProps {
  /** 입력창 플레이스홀더 텍스트 */
  placeholder?: string;
  /** 전송 버튼 클릭 시 호출되는 콜백 함수 */
  onSubmit?: (value: string) => void;
  /** 추가 CSS 클래스 */
  className?: string;
  /** 입력창 비활성화 여부 */
  disabled?: boolean;
}

export function AISearchInput({
  placeholder = "만들고 싶은 전략을 AI에게 요청하세요!",
  onSubmit,
  className = "",
  disabled = false,
}: AISearchInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    if (value.trim() && onSubmit) {
      onSubmit(value.trim());
      setValue("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div
      className={[
        "relative flex items-center",
        "w-full max-w-[1000px] h-[60px]",
        "bg-surface border border-surface",
        "rounded-lg shadow-elev-card-soft",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={[
          "flex-1 h-full px-5",
          "bg-transparent",
          "text-body text-xl font-semibold",
          "placeholder:text-muted/50 placeholder:font-normal",
          "outline-none",
          "rounded-lg",
          disabled && "cursor-not-allowed opacity-50",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="AI 전략 요청 입력"
      />

      <button
        type="button"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        className={[
          "flex items-center justify-center",
          "w-10 h-10 mr-[10px]",
          "rounded-md",
          "bg-[#AC64FF]",
          "transition-all duration-200",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "hover:shadow-elev-brand",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="AI에게 전송"
      >
        <div className="relative w-6 h-6">
          <Image
            src="/icons/arrow-upward.svg"
            alt=""
            fill
            className="object-contain w-10 h-10"
            aria-hidden="true"
          />
        </div>
      </button>
    </div>
  );
}
