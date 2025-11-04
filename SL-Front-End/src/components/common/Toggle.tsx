interface ToggleProps {
  enabled: boolean;
  onChange: () => void;
  label?: string;
}

export function Toggle({ enabled, onChange, label }: ToggleProps) {
  return (
    <button
      type="button"
      onClick={onChange}
      className="quant-toggle"
      data-state={enabled ? "on" : "off"}
      aria-label={label}
    />
  );
}
