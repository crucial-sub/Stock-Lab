import { Title } from "@/components/common/Title";
import { ReactNode } from "react";

/**
 * 섹션 헤더 공통 컴포넌트
 * - 제목과 설명을 포함하는 섹션 헤더
 * - 우측에 액션 버튼 또는 토글 등을 배치 가능
 */
interface SectionHeaderProps {
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  description,
  action,
  className = "",
}: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between ${className}`}>
      <div className="flex items-center gap-3">
        <Title>{title}</Title>
        {description && (
          <p className="text-[0.75rem] self-end mb-1">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
