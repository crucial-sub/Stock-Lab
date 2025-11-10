/**
 * 토글 스위치 공통 컴포넌트
 * - Quant 프로젝트 전반에서 사용되는 on/off 토글 스위치
 * - 접근성을 고려한 버튼 기반 구현
 */
interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function ToggleSwitch({
  checked,
  onChange,
  disabled = false,
  className = "",
}: ToggleSwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative w-[50px] h-[28px] rounded-full transition-colors ${
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
      } ${className}`}
      style={{
        backgroundColor: checked ? "#0066FF" : "#6B7280",
      }}
    >
      <div
        className={`absolute w-[22px] h-[22px] bg-white rounded-full top-[3px] transition-all ${
          checked ? "left-[25px]" : "left-[3px]"
        }`}
      />
    </button>
  );
}
