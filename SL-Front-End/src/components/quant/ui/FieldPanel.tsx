import { ReactNode } from "react";
import ColorBorderLeft from "@/components/quant/common/ColorBorderLeft";

/**
 * FieldPanel - 퀀트 투자 생성 페이지 필드 공통 패널 컴포넌트
 * - 배경 흰색 패널
 * - 왼쪽 컬러 보더 (매수/매도/목표 조건에 따라 색상 변경)
 * - 그림자 효과
 */
interface FieldPanelProps {
  children: ReactNode;
  conditionType: "buy" | "sell" | "target";
  className?: string;
}

export function FieldPanel({
  children,
  conditionType,
  className = "",
}: FieldPanelProps) {
  return (
    <div
      className={`bg-bg-surface rounded-md shadow-card p-8 relative ${className}`}
    >
      <ColorBorderLeft conditionType={conditionType} />
      {children}
    </div>
  );
}
