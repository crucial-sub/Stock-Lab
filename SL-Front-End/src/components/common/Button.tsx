interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  disabled?: boolean;
}

export function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false
}: ButtonProps) {
  const variantStyles = {
    primary: "bg-red-400 text-white text-xl",
    secondary: 'bg-zinc-100 text-black text-xl',
    tertiary: "bg-pink-50 text-red-400 text-xl",
    ghost: 'bg-transparent text-black'
  };

  const sizeStyles = {
    sm: 'px-6 py-[5px] text-[16px]',
    md: 'px-6 py-2 text-xl',
    lg: 'px-[24px] py-[10px] text-[16px]',
    xlg: "py-3 w-24 h-12"
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        font-sans font-semibold rounded-lg 
        flex items-center justify-center gap-1 overflow-hidden
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        ${className}
      `}
    >   {children}
    </button>
  );
}
