/**
 * 설문 진행 상태 Stepper 컴포넌트
 *
 * Phase 1.2: Stepper 컴포넌트 구현
 *
 * 기능:
 * - 고정 헤더 (position: sticky)
 * - 진행률 표시 (예: "2/5")
 * - 이전 단계 클릭 시 해당 메시지로 스크롤
 * - 완료된 단계는 다른 색상으로 표시
 *
 * 사용 시나리오:
 * - 설문 진행 중에만 표시
 * - 현재 단계와 전체 단계 수 표시
 * - 이전 단계 클릭 가능 (질문 수정)
 */

"use client";

interface StepperProps {
  /** 현재 진행 중인 단계 (1부터 시작) */
  currentStep: number;
  /** 전체 단계 수 */
  totalSteps: number;
  /** 각 단계 클릭 시 실행할 핸들러 (해당 질문으로 스크롤) */
  onStepClick?: (step: number) => void;
}

/**
 * 설문 진행 상태를 표시하는 Stepper 컴포넌트
 *
 * 디자인:
 * - 채팅 영역 상단에 고정 (sticky)
 * - 현재 단계는 강조 표시 (보라색)
 * - 완료된 단계는 클릭 가능 (회색)
 * - 미완료 단계는 비활성화 (옅은 회색)
 */
export function Stepper({ currentStep, totalSteps, onStepClick }: StepperProps) {
  /**
   * 단계 클릭 핸들러
   */
  function handleStepClick(step: number) {
    // 완료된 단계만 클릭 가능
    if (step <= currentStep && onStepClick) {
      onStepClick(step);
    }
  }

  /**
   * 단계별 상태 반환
   * - completed: 완료된 단계 (현재 단계 이전)
   * - current: 현재 진행 중인 단계
   * - pending: 아직 진행하지 않은 단계
   */
  function getStepStatus(step: number): "completed" | "current" | "pending" {
    if (step < currentStep) return "completed";
    if (step === currentStep) return "current";
    return "pending";
  }

  /**
   * 단계별 스타일 클래스 반환
   */
  function getStepClassName(step: number): string {
    const status = getStepStatus(step);
    const isClickable = status === "completed" || status === "current";

    const baseClasses = "flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold transition-all";

    // 상태별 스타일
    const statusClasses = {
      completed: "bg-gray-200 text-gray-700 hover:bg-gray-300",
      current: "bg-brand-purple text-white shadow-elev-brand",
      pending: "bg-gray-100 text-gray-400",
    };

    // 클릭 가능 여부
    const clickableClasses = isClickable ? "cursor-pointer" : "cursor-not-allowed";

    return `${baseClasses} ${statusClasses[status]} ${clickableClasses}`;
  }

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-surface shadow-elev-sm">
      <div className="w-full max-w-[1000px] mx-auto px-4 py-3">
        {/* 데스크톱: 단계 인디케이터 */}
        <div className="hidden md:flex items-center justify-center gap-3">
          {Array.from({ length: totalSteps }, (_, index) => {
            const step = index + 1;
            const isLast = step === totalSteps;

            return (
              <div key={step} className="flex items-center">
                {/* 단계 원 */}
                <button
                  type="button"
                  onClick={() => handleStepClick(step)}
                  className={getStepClassName(step)}
                  aria-label={`질문 ${step}단계`}
                  aria-current={step === currentStep ? "step" : undefined}
                >
                  {step}
                </button>

                {/* 연결선 (마지막 단계 제외) */}
                {!isLast && (
                  <div
                    className={[
                      "w-12 h-0.5 mx-2",
                      step < currentStep ? "bg-gray-300" : "bg-gray-200",
                    ].join(" ")}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* 모바일: 축약 표시 */}
        <div className="flex md:hidden items-center justify-center">
          <p className="text-sm font-semibold text-gray-700">
            질문 <span className="text-brand-purple">{currentStep}</span> / {totalSteps}
          </p>
        </div>

        {/* 진행률 텍스트 (선택 사항) */}
        <div className="mt-2 text-center">
          <p className="text-xs text-muted">
            {currentStep === totalSteps
              ? "마지막 질문입니다"
              : `${totalSteps - currentStep}개의 질문이 남았습니다`}
          </p>
        </div>
      </div>
    </div>
  );
}
