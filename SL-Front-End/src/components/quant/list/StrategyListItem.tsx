import Image from "next/image";
import Link from "next/link";
import type { Strategy } from "@/types/strategy";

/**
 * 전략 목록 아이템 컴포넌트
 * - 개별 전략 정보 표시
 * - 체크박스 선택 기능
 * - 전략 이름 클릭 시 결과 페이지로 이동
 */
interface StrategyListItemProps {
  /** 전략 데이터 */
  strategy: Strategy;
  /** 선택 여부 */
  isSelected: boolean;
  /** 선택 상태 변경 핸들러 */
  onToggle: (id: string) => void;
}

export function StrategyListItem({
  strategy,
  isSelected,
  onToggle,
}: StrategyListItemProps) {
  return (
    <tr className={`${isSelected ? "rounded-md shadow-card" : ""}`}>
      {/* 체크박스 */}
      <td className="p-[10px] text-left">
        <Image
          src={`/icons/${isSelected ? "check-box-blue" : "check-box-blank"}.svg`}
          alt="체크"
          width={20}
          height={20}
          onClick={() => onToggle(strategy.id)}
        />
      </td>

      {/* 전략 이름 */}
      <td className="p-[10px] ">
        <Link
          href={`/quant/result/${strategy.id}`}
          className={`text-[18px] text-left font-semibold ${isSelected ? "text-accent-primary" : ""}`}
        >
          {strategy.name}
        </Link>
      </td>

      {/* 일평균 수익률 */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.dailyAverageReturn > 0
            ? "text-brand-primary"
            : "text-accent-primary"
        }`}
      >
        {strategy.dailyAverageReturn > 0 ? "+" : ""}
        {strategy.dailyAverageReturn.toFixed(2)}%
      </td>

      {/* 누적 수익률 */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.cumulativeReturn > 0
            ? "text-brand-primary"
            : "text-accent-primary"
        }`}
      >
        {strategy.cumulativeReturn > 0 ? "+" : ""}
        {strategy.cumulativeReturn.toFixed(2)}%
      </td>

      {/* MDD (Max Drawdown) */}
      <td
        className={`p-[10px] text-[18px] text-left font-semibold ${
          strategy.maxDrawdown < 0 ? "text-accent-primary" : "text-gray-500"
        }`}
      >
        {strategy.maxDrawdown.toFixed(2)}%
      </td>

      {/* 생성일 */}
      <td className="p-[10px] text-[18px] text-left font-semiboldd">
        {strategy.createdAt}
      </td>
    </tr>
  );
}
