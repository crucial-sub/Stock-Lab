import type { CSSProperties } from "react";

interface IconProps {
  src: string;
  alt?: string;
  className?: string;
  color?: string;
  size?: number | string;
}

const maskBaseStyle: CSSProperties = {
  WebkitMaskRepeat: "no-repeat",
  maskRepeat: "no-repeat",
  WebkitMaskPosition: "center",
  maskPosition: "center",
  WebkitMaskSize: "contain",
  maskSize: "contain",
};

export function Icon({
  src,
  alt,
  className,
  color = "currentColor",
  size = 20,
}: IconProps) {
  const composedClassName = ["inline-block", className]
    .filter(Boolean)
    .join(" ");

  const dimension =
    typeof size === "number" ? `${size}px` : (size ?? "1.25rem");

  return (
    <span
      role={alt ? "img" : "presentation"}
      aria-label={alt}
      className={composedClassName}
      style={{
        ...maskBaseStyle,
        WebkitMaskImage: `url(${src})`,
        maskImage: `url(${src})`,
        backgroundColor: color,
        width: dimension,
        height: dimension,
      }}
    />
  );
}
