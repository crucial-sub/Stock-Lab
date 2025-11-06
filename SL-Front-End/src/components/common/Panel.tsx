import type { ReactNode } from "react";

/**
 * Panel 컴포넌트 Props 타입
 */
interface PanelProps {
  /** 패널 내부 컨텐츠 */
  children: ReactNode;
  /** 추가 CSS 클래스 */
  className?: string;
  /** 패널 스타일 변형 (기본: quant, 유리형태: glass) */
  variant?: "quant" | "glass";
}

/**
 * 재사용 가능한 Panel 컴포넌트
 * - variant="quant": 기본 quant-panel 스타일 (기존 매수/매도 조건 패널)
 * - variant="glass": 유리 효과 패널 스타일 (매매 대상 설정 패널)
 *
 * @example
 * ```tsx
 * // 기본 패널
 * <Panel className="p-6">
 *   <h3>매수 조건</h3>
 * </Panel>
 *
 * // 유리 효과 패널
 * <Panel variant="glass" className="p-[28px]">
 *   <div>매매 대상 설정</div>
 * </Panel>
 * ```
 */
export function Panel({
  children,
  className = "",
  variant = "quant",
}: PanelProps) {
  // variant에 따른 기본 스타일 선택
  const baseStyle =
    variant === "glass"
      ? "bg-[rgba(255,255,255,0.2)] rounded-[8px] border-[0.5px] border-solid border-white shadow-[0px_0px_8px_2px_rgba(255,255,255,0.3)]"
      : "quant-panel relative";

  return <div className={`${baseStyle} ${className}`}>{children}</div>;
}
