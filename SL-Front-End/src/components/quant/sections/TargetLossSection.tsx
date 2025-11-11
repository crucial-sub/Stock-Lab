import { Title } from "@/components/common";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";
import { FieldPanel, SectionHeader } from "@/components/quant/ui";
import { ToggleSwitch, UnderlineInput } from "@/components/common";
import ActiveConditionBtn from "@/components/quant/ui/ActivateConditionBtn";

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
    <div id="section-target-loss" className="space-y-3">
      <SectionHeader
        title="목표가 / 손절가"
        description="실시간 감시에 따라 일정 기준에서의 목표가 / 손절가에 도달 시 매도 주문을 합니다."
        action={
          <ToggleSwitch checked={isOpen} onChange={setIsOpen} />
        }
      />

      {isOpen ? (
        <FieldPanel conditionType="sell">
          <div className="grid grid-cols-2 gap-6">
            {/* 목표가 */}
            <div className="space-y-2">
              <div className="flex items-center gap-5">
                <Title variant="subtitle">목표가</Title>
                <ToggleSwitch
                  checked={profitTargetEnabled}
                  onChange={setProfitTargetEnabled}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-body">매수가 대비</span>
                <div className="relative">
                  <UnderlineInput
                    value={targetGain}
                    onChange={(e) => setTargetGain(Number(e.target.value))}
                    className="w-[3.75rem] !h-full"
                    disabled={!profitTargetEnabled}
                  />
                  <span className="absolute right-0 top-[5px]">
                    %
                  </span>
                </div>
                <span className="text-sm text-text-body">상승 시 매도 주문</span>
              </div>
            </div>

            {/* 손절가 */}
            <div className="space-y-2">
              <div className="flex items-center gap-5">
                <Title variant="subtitle">손절가</Title>
                <ToggleSwitch
                  checked={stopLossEnabled}
                  onChange={setStopLossEnabled}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-body">매수가 대비</span>
                <div className="relative">
                  <UnderlineInput
                    value={stopLoss}
                    onChange={(e) => setStopLoss(Number(e.target.value))}
                    className="w-[3.75rem] !h-full"
                    disabled={!stopLossEnabled}
                  />
                  <span className="absolute right-0 top-[5px]">
                    %
                  </span>
                </div>
                <span className="text-sm text-text-body">% 하락 시 매도 주문</span>
              </div>
            </div>
          </div>
        </FieldPanel>
      ) : (
        <ActiveConditionBtn checked={isOpen} onChange={setIsOpen} />
      )}
    </div>
  );
}
