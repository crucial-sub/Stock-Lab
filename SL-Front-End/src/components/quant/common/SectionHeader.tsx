import { ReactNode } from "react";
import { Title } from "@/components/common/Title";

/**
 * 섹션 헤더 공통 컴포넌트
 * - 제목과 설명을 포함하는 섹션 헤더
 * - 우측에 액션 버튼 또는 토글 등을 배치 가능
 */
interface SectionHeaderProps {
  title: string;
  description?: string;
  highlight?: "buy" | "sell" | "none";
  action?: ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  description,
  highlight = "none",
  action,
  className = "",
}: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="flex items-center gap-3">
        {highlight === "buy" && (
          <Title>
            <span className="text-brand-primary">매수</span>{" "}
            <span className="text-text-strong">{title}</span>
          </Title>
        )}
        {highlight === "sell" && (
          <Title>
            <span className="text-brand-primary">매도</span>{" "}
            <span className="text-text-strong">{title}</span>
          </Title>
        )}
        {highlight === "none" && <Title>{title}</Title>}
        {description && (
          <p className="text-sm text-text-body">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
