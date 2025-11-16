"use client";

/**
 * AI 어시스턴트 전략 카드
 *
 * @description 전략 정보를 표시하는 카드 컴포넌트입니다.
 * hover 시 브랜드 컬러 테두리로 변경됩니다.
 */

interface StrategyCardProps {
  /** 전략 제목 */
  title: string;
  /** 전략 설명 (멀티라인 지원) */
  description: string;
  /** 클릭 핸들러 */
  onClick?: () => void;
  /** 카드 크기 (기본: small) */
  size?: "small" | "large";
}

export function StrategyCard({
  title,
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
        "hover:border-brand-soft hover:shadow-elev-card",
        "text-left",
        isLarge
          ? "w-full max-w-[1000px] h-[112px] px-5 py-4"
          : "w-[480px] h-[112px] px-5 py-4",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <h3 className="text-xl font-semibold text-black mb-2">{title}</h3>
      <p className="text-base leading-[1.4] text-muted whitespace-pre-line">
        {description}
      </p>
    </button>
  );
}
