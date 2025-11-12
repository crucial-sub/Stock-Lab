import { Button } from "@/components/common";
import { useRouter } from "next/navigation";

/**
 * 전략 액션 버튼 컴포넌트
 * - 새 전략 만들기 버튼
 * - 선택 전략 삭제하기 버튼
 */
interface StrategyActionsProps {
  /** 선택된 전략 개수 */
  selectedCount: number;
  /** 삭제 버튼 클릭 핸들러 */
  onDelete: () => void;
}

export function StrategyActions({
  selectedCount,
  onDelete,
}: StrategyActionsProps) {

  const router = useRouter();
  const handleCreateStrategy = () => {
    router.push("/quant/new");
  };

  return (
    <div className="flex gap-3">
      {/* 새 전략 만들기 버튼 */}
      <Button variant="primary" size="md" onClick={handleCreateStrategy}>
        새 전략 만들기
      </Button>

      <Button variant="secondary" size="md" onClick={onDelete} disabled={selectedCount === 0}>
        선택 전략 삭제하기
      </Button>
    </div>
  );
}
