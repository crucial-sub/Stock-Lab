/**
 * 토글 스위치 공통 컴포넌트
 * - Quant 프로젝트 전반에서 사용되는 on/off 토글 스위치
 * - 접근성을 고려한 버튼 기반 구현
 * - variant로 매수(빨간색)/매도(파란색) 구분
 */
interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  variant?: "buy" | "sell";
}

export function ToggleSwitch({
  checked,
  onChange,
  disabled = false,
  className = "",
  variant = "sell",
}: ToggleSwitchProps) {
  const activeColor = variant === "buy" ? "#FF4D4F" : "#007dfc";

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative w-8 h-[18px] rounded-full transition-colors duration-500 ease-in-out ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
        } ${className}`}
      style={{
        backgroundColor: checked ? activeColor : "#c8c8c8",
      }}
    >
      <div
        className={`absolute w-4 h-4 bg-white rounded-full transition-all duration-500 ease-in-out ${checked ? "right-[1px]" : "left-[1px]"
          }`}
        style={{
          top: "50%",
          transform: "translateY(-50%)",
        }}
      />
    </button>
  );
}
