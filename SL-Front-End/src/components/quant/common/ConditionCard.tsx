import { Dropdown } from "@/components/common";
import type { Condition } from "@/stores";
import Image from "next/image";
import { UnderLineInput } from "./UnderLineInput";

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
    <div className="flex items-center gap-3">
      {/* 조건식 표시 영역 */}
      <div className="relative w-[31.25rem] h-12 flex items-center gap-3 rounded-md border-[0.5px]">
        {/* 조건식 ID */}
        <div className="w-12 h-12 rounded-tl-md rounded-bl-md flex items-center justify-center bg-brand-primary text-white">
          {condition.id}
        </div>

        {/* 텍스트 (클릭 가능) */}
        <button
          type="button"
          onClick={onFactorSelect}
          className="flex-1 text-left"
        >
          {expressionText}
        </button>

        {/* 삭제 아이콘 */}
        <button
          type="button"
          onClick={onRemove}
          className="absolute right-3 flex items-center justify-center hover:opacity-100 transition-opacity"
        >
          <Image
            src="/icons/trash.svg"
            alt="삭제"
            width={24}
            height={24}
            className="opacity-30"
          />
        </button>
      </div>

      {/* 부등호 선택 */}
      <Dropdown
        value={condition.operator}
        onChange={(value) =>
          onOperatorChange(value as ">=" | "<=" | ">" | "<" | "=" | "!=")
        }
        options={[
          { value: ">=", label: "≥" },
          { value: "<=", label: "≤" },
          { value: ">", label: ">" },
          { value: "<", label: "<" },
          { value: "=", label: "=" },
          { value: "!=", label: "≠" },
        ]}
        variant="large"
      />

      {/* 값 입력 */}
      <UnderLineInput
        value={condition.value}
        onChange={(e) => onValueChange(Number(e.target.value))}
        className="!w-20 text-center"
      />
    </div>
  );
}
