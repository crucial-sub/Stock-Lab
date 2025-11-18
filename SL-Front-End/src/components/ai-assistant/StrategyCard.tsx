"use client";

/**
 * AI 어시스턴트 전략 카드
 *
 * @description 전략 정보를 표시하는 카드 컴포넌트입니다.
 * hover 시 브랜드 컬러 테두리로 변경됩니다.
 */

interface StrategyCardProps {
  /** 전략 제목 */
  question: string;
  /** 전략 설명 (멀티라인 지원) */
  description?: string;
  /** 클릭 핸들러 */
  onClick?: () => void;
  /** 카드 크기 (기본: small) */
  size?: "small" | "large";
}

export function StrategyCard({
  question,
  description,
  onClick,
  size = "small",
}: StrategyCardProps) {
  const isLarge = size === "large";

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "bg-surface border border-surface",
        "rounded-lg",
        "transition-all duration-200",
        "flex",
        "flex-col",
        "gap-2",
        "hover:bg-[#FFFFFF0D]",
        "hover:border-brand-purple",
        "hover:shadow-elev-brand",
        "hover:text-brand-purple",
        "text-left",
        "px-5 py-4",
        isLarge
          ? "w-full max-w-[62.5rem]"
          : "w-[30rem]",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <h3 className="text-[1.25rem] font-semibold">{question}</h3>
      {description && <p className="text-muted whitespace-pre-line">
        {description}
      </p>}

    </button>
  );
}
