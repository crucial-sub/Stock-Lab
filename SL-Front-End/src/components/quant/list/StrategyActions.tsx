import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/common";
import { KiwoomConnectModal } from "@/components/modal/KiwoomConnectModal";
import { kiwoomApi } from "@/lib/api/kiwoom";

/**
 * 전략 액션 버튼 컴포넌트
 * - 증권사 연동하기 버튼
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
  const [isKiwoomModalOpen, setIsKiwoomModalOpen] = useState(false);
  const [isKiwoomConnected, setIsKiwoomConnected] = useState(false);

  const checkKiwoomStatus = useCallback(async () => {
    try {
      const status = await kiwoomApi.getStatus();
      setIsKiwoomConnected(status.is_connected);
    } catch (error) {
      console.error("키움증권 연동 상태 확인 실패:", error);
    }
  }, []);

  useEffect(() => {
    checkKiwoomStatus();
  }, [checkKiwoomStatus]);

  const handleCreateStrategy = () => {
    router.push("/quant/new");
  };

  const handleKiwoomSuccess = () => {
    setIsKiwoomConnected(true);
  };

  return (
    <>
      <div className="flex gap-3">
        {/* 증권사 연동하기 버튼 */}
        <Button
          variant={isKiwoomConnected ? "success" : "primary"}
          size="md"
          onClick={() => setIsKiwoomModalOpen(true)}
        >
          {isKiwoomConnected ? "✓ 증권사 연동됨" : "증권사 연동하기"}
        </Button>

        {/* 새 전략 만들기 버튼 */}
        <Button variant="primary" size="md" onClick={handleCreateStrategy}>
          새 전략 만들기
        </Button>

        <Button
          variant="secondary"
          size="md"
          onClick={onDelete}
          disabled={selectedCount === 0}
        >
          선택 전략 삭제하기
        </Button>
      </div>

      <KiwoomConnectModal
        isOpen={isKiwoomModalOpen}
        onClose={() => setIsKiwoomModalOpen(false)}
        onSuccess={handleKiwoomSuccess}
      />
    </>
  );
}
