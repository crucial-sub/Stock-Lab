"use client";

import { Button } from "@/components/common";
import { useRouter } from "next/navigation";

/**
 * 최종 조건 확인 페이지로 이동하는 버튼 컴포넌트
 * - 매매 대상 선택 완료 후 사용
 * - /quant/confirm 페이지로 라우팅
 * - 설정한 모든 백테스트 조건을 최종 확인할 수 있도록 함
 *
 * @example
 * ```tsx
 * <ShowBacktestStrategyButton />
 * ```
 */
export function ShowBacktestStrategyButton() {
  const router = useRouter();

  /**
   * 최종 조건 확인 페이지로 이동
   * - /quant/confirm 페이지로 라우팅
   */
  const handleClick = () => {
    router.push("/quant/confirm");
  };

  return (
    <Button
      variant="primary"
      onClick={handleClick}
      className="px-8 py-3 text-base font-medium"
    >
      최종 조건 확인하기
    </Button>
  );
}
