import Image from "next/image";
import type { Condition } from "@/stores";

/**
 * 조건식 카드 공통 컴포넌트
 * - 매수/매도 조건식을 표시하는 카드
 * - 팩터 선택, 부등호, 값 입력, 삭제 기능 포함
 */
interface ConditionCardProps {
  condition: Condition;
  expressionText: string;
  onFactorSelect: () => void;
  onOperatorChange: (operator: ">=" | "<=" | ">" | "<" | "=" | "!=") => void;
  onValueChange: (value: number) => void;
  onRemove: () => void;
}

export function ConditionCard({
  condition,
  expressionText,
  onFactorSelect,
  onOperatorChange,
  onValueChange,
  onRemove,
}: ConditionCardProps) {
  return (
    <div className="flex items-center gap-3 p-4 border border-border-default rounded-lg hover:border-accent-primary transition-colors">
      {/* 조건 ID */}
      <div className="w-12 h-12 flex items-center justify-center bg-brand-primary text-white font-bold text-lg rounded-md flex-shrink-0">
        {condition.id}
      </div>

      {/* 조건 표시 (클릭 가능) */}
      <div
        onClick={onFactorSelect}
        className="flex-1 text-text-body font-medium px-3 py-2 border border-border-default rounded-sm hover:border-accent-primary cursor-pointer transition-colors"
      >
        {expressionText}
      </div>

      {/* 부등호 선택 */}
      <select
        value={condition.operator}
        onChange={(e) =>
          onOperatorChange(
            e.target.value as ">=" | "<=" | ">" | "<" | "=" | "!="
          )
        }
        className="w-20 px-2 py-2 border border-border-default rounded-sm text-text-body focus:outline-none focus:border-accent-primary"
      >
        <option value=">=">≥</option>
        <option value="<=">≤</option>
        <option value=">">{">"}</option>
        <option value="<">{"<"}</option>
        <option value="=">=</option>
        <option value="!=">≠</option>
      </select>

      {/* 값 입력 */}
      <input
        type="number"
        value={condition.value}
        onChange={(e) => onValueChange(Number(e.target.value))}
        className="w-24 px-3 py-2 border border-border-default rounded-sm text-text-body text-center focus:outline-none focus:border-accent-primary"
      />

      {/* 삭제 버튼 */}
      <button
        type="button"
        onClick={onRemove}
        className="w-10 h-10 flex items-center justify-center border border-brand-primary text-brand-primary rounded-sm hover:bg-brand-primary hover:text-white transition-colors"
      >
        <Image src="/icons/trash.svg" alt="삭제" width={20} height={20} />
      </button>
    </div>
  );
}
