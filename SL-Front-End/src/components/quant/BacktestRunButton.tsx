"use client";

/**
 * 백테스트 실행 버튼 컴포넌트
 * - 전역 상태 스토어에서 모든 설정값을 수집하여 BacktestRunRequest 형식으로 서버에 전송합니다.
 * - 실행 후 결과 페이지로 이동합니다.
 */

import { useRouter } from "next/navigation";
import { useRunBacktestMutation } from "@/hooks/useBacktestQuery";
import { Button } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";

/**
 * 백테스트 실행 버튼
 *
 * 이제 props를 받지 않고 전역 스토어에서 모든 설정값을 가져옵니다.
 */
export function BacktestRunButton() {
  const router = useRouter();
  const runBacktestMutation = useRunBacktestMutation();

  // 전역 백테스트 설정 스토어에서 BacktestRunRequest 가져오기
  const { getBacktestRequest } = useBacktestConfigStore();

  /**
   * 백테스트 실행 핸들러
   * 1. 전역 스토어에서 BacktestRunRequest 형식의 데이터를 가져옴
   * 2. 백엔드로 전송
   * 3. 백테스트 ID를 받아옴
   * 4. 결과 페이지로 이동
   */
  const handleRunBacktest = async () => {
    try {
      // 전역 스토어에서 BacktestRunRequest 형식으로 데이터 가져오기
      const backtestRequest = getBacktestRequest();

      // 유효성 검증 (선택적)
      if (backtestRequest.buy_conditions.length === 0) {
        alert("최소 하나 이상의 매수 조건을 설정해주세요.");
        return;
      }

      if (backtestRequest.target_stocks.length === 0) {
        alert("최소 하나 이상의 매매 대상 종목을 선택해주세요.");
        return;
      }

      // 백테스트 실행
      const result = await runBacktestMutation.mutateAsync(backtestRequest);

      // 결과 페이지로 이동
      router.push(`/quant/result?id=${result.backtestId}`);
    } catch (error) {
      console.error("백테스트 실행 실패:", error);
      alert("백테스트 실행에 실패했습니다. 설정을 확인해주세요.");
    }
  };

  return (
    <Button
      onClick={handleRunBacktest}
      disabled={runBacktestMutation.isPending}
      variant="secondary"
      className="px-8"
    >
      {runBacktestMutation.isPending ? "백테스트 실행 중..." : "백테스트 시작하기"}
    </Button>
  );
}
