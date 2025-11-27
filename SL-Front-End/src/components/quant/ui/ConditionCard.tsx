import Image from "next/image";
import { Dropdown, UnderlineInput } from "@/components/common";

// API 명세 확정 후 수정 예정
interface Condition {
  id: string;
  factorName: string | null;
  subFactorName: string | null;
  operator: string;
  value: string;
  argument?: string;
}

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
  onValueChange: (value: string) => void; // API 명세 확정 후 수정 예정
  onRemove: () => void;
  /** 조건 타입 (매수: buy, 매도: sell) - 색상 결정에 사용 */
  conditionType: "buy" | "sell";
}

export function ConditionCard({
  condition,
  expressionText,
  onFactorSelect,
  onOperatorChange,
  onValueChange,
  onRemove,
  conditionType,
}: ConditionCardProps) {
  // 조건 타입에 따른 배경색 결정
  const bgColor = conditionType === "buy" ? "bg-price-up" : "bg-price-down";

  return (
    <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 sm:gap-3">
      {/* 조건식 표시 영역 */}
      <div className="relative flex-1 min-w-0 max-w-full sm:max-w-[31.25rem] h-12 flex items-center gap-2 sm:gap-3 rounded-md border-[0.5px]">
        {/* 조건식 ID */}
        <div
          className={`w-10 sm:w-12 h-12 shrink-0 rounded-tl-md rounded-bl-md flex items-center justify-center ${bgColor} text-white text-sm sm:text-base`}
        >
          {condition.id}
        </div>

        {/* 텍스트 (클릭 가능) */}
        <button
          type="button"
          onClick={onFactorSelect}
          className="flex-1 text-left truncate pr-10 text-sm sm:text-base min-w-0"
        >
          {expressionText}
        </button>

        {/* 삭제 아이콘 */}
        <button
          type="button"
          onClick={onRemove}
          className="absolute right-2 sm:right-3 flex items-center justify-center hover:opacity-100 transition-opacity shrink-0"
        >
          <Image
            src="/icons/trash.svg"
            alt="삭제"
            width={20}
            height={20}
            className="opacity-30 sm:w-6 sm:h-6"
          />
        </button>
      </div>

      {/* 부등호 선택 */}
      <div className="shrink-0">
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
      </div>

      {/* 값 입력 */}
      <UnderlineInput
        value={condition.value}
        onChange={(e) => onValueChange(e.target.value)}
        className="!w-16 sm:!w-20 text-center shrink-0"
      />
    </div>
  );
}
