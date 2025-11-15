import { StrategyListItem } from "@/components/quant/list/StrategyListItem";
import type { Strategy } from "@/types/strategy";
import Image from "next/image";

/**
 * 전략 목록 테이블 컴포넌트
 * - 전략 목록 테이블 표시
 * - 전체 선택 기능
 */
interface StrategyListProps {
  /** 전략 목록 */
  strategies: Strategy[];
  /** 선택된 전략 ID 배열 */
  selectedIds: string[];
  /** 전체 선택/해제 핸들러 */
  onToggleAll: () => void;
  /** 개별 선택/해제 핸들러 */
  onToggleItem: (id: string) => void;
}

const STRATEGY_TH = [
  "전략 이름",
  "일평균 수익률",
  "누적 수익률",
  "투자 수익률",
  "생성일",
];

export function StrategyList({
  strategies,
  selectedIds,
  onToggleAll,
  onToggleItem,
}: StrategyListProps) {
  const isAllSelected =
    strategies.length > 0 && selectedIds.length === strategies.length;

  return (
    <div className="overflow-hidden">
      <table className="w-full border-separate border-spacing-3">
        <thead className="">
          <tr className="h-10 border-b-[0.5px] border-tag-neutral">
            {/* 전체 선택 체크박스 */}
            <th className="p-[10px] text-left">
              <Image
                src={`/icons/${isAllSelected ? "check-box-blue" : "check-box-blank"
                  }.svg`}
                alt="검색"
                width={20}
                height={20}
                onClick={onToggleAll}
              />
            </th>
            {STRATEGY_TH.map((st, index) => (
              <th
                key={`${st}-${index}`}
                className="p-[10px] text-left font-normal text-tag-neutral"
              >
                {st}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {strategies.map((strategy) => (
            <StrategyListItem
              key={strategy.id}
              strategy={strategy}
              isSelected={selectedIds.includes(strategy.id)}
              onToggle={onToggleItem}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
