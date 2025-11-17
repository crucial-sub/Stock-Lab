/**
 * 추천 질문 카드 컴포넌트
 *
 * @description 홈 화면에 표시되는 AI 추천 질문 카드입니다.
 * 사용자가 클릭하면 해당 질문을 AI 입력창에 자동 입력합니다.
 *
 * @example
 * ```tsx
 * <QuestionCard
 *   title="요즘 뜨는 전략"
 *   description={`최신 유행하는 전략을 확인해보세요!\n저명한 주식 분석가들이 만든 신뢰도가 높은 전략이에요.`}
 *   onClick={() => handleQuestionClick("요즘 뜨는 전략")}
 * />
 * ```
 */

interface QuestionCardProps {
  /** 질문 카드 제목 */
  title: string;
  /** 질문 카드 설명 (멀티라인 지원) */
  description: string;
  /** 클릭 이벤트 핸들러 */
  onClick?: () => void;
  /** 추가 CSS 클래스 */
  className?: string;
}

export function QuestionCard({
  title,
  description,
  onClick,
  className = "",
}: QuestionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "w-full max-w-[800px] h-[112px]",
        "px-5 py-4",
        "bg-surface border border-surface",
        "rounded-lg shadow-elev-card-soft",
        "text-left",
        "transition-all duration-200",
        "hover:shadow-elev-card hover:border-brand-soft",
        "cursor-pointer",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label={`추천 질문: ${title}`}
    >
      <h3 className="text-xl font-semibold text-black mb-2">{title}</h3>
      <p className="text-base leading-[1.4] text-muted whitespace-pre-line">
        {description}
      </p>
    </button>
  );
}
