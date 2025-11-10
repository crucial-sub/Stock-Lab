import { useState, useEffect } from "react";
import { useBacktestConfigStore } from "@/stores";
import { SectionHeader, ToggleSwitch } from "../common";

/**
 * 목표가 / 손절가 섹션
 * - 목표가 설정 (매수가 대비 % 상승 시 매도)
 * - 손절가 설정 (매수가 대비 % 하락 시 매도)
 */
export function TargetLossSection() {
  const { target_and_loss, setTargetAndLoss } = useBacktestConfigStore();

  const [isOpen, setIsOpen] = useState(target_and_loss !== null);
  const [profitTargetEnabled, setProfitTargetEnabled] = useState(
    target_and_loss?.target_gain !== null
  );
  const [stopLossEnabled, setStopLossEnabled] = useState(
    target_and_loss?.stop_loss !== null
  );
  const [targetGain, setTargetGain] = useState<number>(
    target_and_loss?.target_gain ?? 10
  );
  const [stopLoss, setStopLoss] = useState<number>(
    target_and_loss?.stop_loss ?? 10
  );

  // 전역 스토어 업데이트
  useEffect(() => {
    if (isOpen) {
      setTargetAndLoss({
        target_gain: profitTargetEnabled ? targetGain : null,
        stop_loss: stopLossEnabled ? stopLoss : null,
      });
    } else {
      setTargetAndLoss(null);
    }
  }, [
    isOpen,
    profitTargetEnabled,
    stopLossEnabled,
    targetGain,
    stopLoss,
    setTargetAndLoss,
  ]);

  return (
    <div className="space-y-3">
      <SectionHeader
        title="목표가 / 손절가"
        description="설사리 감사에 따라 목표 기준에서의 매수가 / 손절가에 도달 시 매도 주문을 합니다."
        action={
          <ToggleSwitch checked={isOpen} onChange={setIsOpen} />
        }
      />

      {isOpen && (
        <div className="bg-bg-surface rounded-lg shadow-card p-6 border-l-4 border-accent-secondary">
          <div className="grid grid-cols-2 gap-6">
            {/* 목표가 */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <h4 className="text-base font-semibold text-text-strong">
                  목표가
                </h4>
                <ToggleSwitch
                  checked={profitTargetEnabled}
                  onChange={setProfitTargetEnabled}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-body">매수가 대비</span>
                <input
                  type="number"
                  value={targetGain}
                  onChange={(e) => setTargetGain(Number(e.target.value))}
                  disabled={!profitTargetEnabled}
                  className="w-24 px-3 py-2 border border-border-default rounded-sm text-text-strong disabled:opacity-50"
                />
                <span className="text-sm text-text-body">% 상승 시 매도 주문</span>
              </div>
            </div>

            {/* 손절가 */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <h4 className="text-base font-semibold text-text-strong">
                  손절가
                </h4>
                <ToggleSwitch
                  checked={stopLossEnabled}
                  onChange={setStopLossEnabled}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-body">매수가 대비</span>
                <input
                  type="number"
                  value={stopLoss}
                  onChange={(e) => setStopLoss(Number(e.target.value))}
                  disabled={!stopLossEnabled}
                  className="w-24 px-3 py-2 border border-border-default rounded-sm text-text-strong disabled:opacity-50"
                />
                <span className="text-sm text-text-body">% 하락 시 매도 주문</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
