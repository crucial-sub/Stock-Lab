/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{ts,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/hooks/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    container: {
      center: true,
      padding: {
        sm: "1rem /* 16px */",
        md: "2rem /* 32px */",
        lg: "3rem /* 48px */",
      },
      screens: {
        "2xl": "1320px /* 82.5rem */",
      },
    },
    borderRadius: {
      none: "0px /* 0px */",
      xs: "var(--radius-xs) /* 4px */",
      sm: "var(--radius-sm) /* 8px */",
      md: "var(--radius-md) /* 12px */",
      lg: "var(--radius-lg) /* 16px */",
      xl: "var(--radius-xl) /* 20px */",
      "2xl": "var(--radius-2xl) /* 24px */",
      full: "9999px /* full pill */",
    },
    extend: {
      fontFamily: {
        sans: [
          "Pretendard Variable /* main variable font */",
          "Pretendard /* static Pretendard */",
          "-apple-system /* macOS system font */",
          "BlinkMacSystemFont /* Safari system font */",
          "Segoe UI /* Windows system font */",
          "sans-serif /* generic fallback */",
        ],
      },
      colors: {
        bg: {
          app: "var(--bg-app) /* #000000 */",
          surface: "var(--bg-surface) /* #1a1a1a */",
          elevated: "var(--bg-surface-elevated) /* #2a2a2a */",
          muted: "var(--bg-surface-muted) /* rgba(40, 40, 40, 0.8) */",
          shine: "var(--bg-shine) /* rgba(255, 255, 255, 0.2) */",
        },
        text: {
          primary: "var(--text-primary) /* #ffffff */",
          secondary: "var(--text-secondary) /* #a0a0a0 */",
          tertiary: "var(--text-tertiary) /* #707070 */",
          quarternary: "var(--text-quarternary) /* #969696 */",
          disabled: "var(--text-disabled) /* #505050 */",
        },
        brand: {
          DEFAULT: "var(--brand) /* #ff8a3d */",
          strong: "var(--brand-strong) /* #ff9f4f */",
          weak: "var(--brand-weak) /* rgba(255, 138, 61, 0.2) */",
          ring: "var(--brand-ring) /* rgba(255, 138, 61, 0.4) */",
        },
        state: {
          success: "var(--state-positive) /* #ff5252 */",
          danger: "var(--state-negative) /* #4d9cff */",
          warning: "var(--state-warning) /* #f2b950 */",
          info: "var(--state-info) /* #4d78ff */",
        },
        border: {
          DEFAULT: "var(--border-default) /* rgba(255, 255, 255, 0.1) */",
          strong: "var(--border-strong) /* rgba(255, 255, 255, 0.2) */",
          highlight: "var(--border-highlight) /* rgba(255, 138, 61, 0.5) */",
        },
        overlay: {
          DEFAULT: "var(--bg-overlay) /* rgba(0, 0, 0, 0.9) */",
        },
      },
      boxShadow: {
        soft: "var(--shadow-soft) /* 0 4px 12px rgba(0, 0, 0, 0.5) */",
        hard: "var(--shadow-hard) /* 0 8px 24px rgba(0, 0, 0, 0.7) */",
        ring: "var(--shadow-ring) /* 0 0 0 1px rgba(255, 255, 255, 0.05) */",
      },
      backgroundImage: {
        "quant-panel":
          "linear-gradient(160deg, rgba(21,23,26,0.9), rgba(14,15,17,0.86)) /* 160deg dark panel gradient */",
        "quant-tab-active":
          "linear-gradient(140deg, rgba(255,138,61,0.18), rgba(255,177,106,0.12)) /* 140deg warm highlight */",
        "quant-button":
          "linear-gradient(140deg, #ffb36a, #ff8a3d) /* 140deg brand button gradient */",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": {
            boxShadow:
              "0 0 0 0 rgba(255, 138, 61, 0.35) /* initial glow strength */",
          },
          "50%": {
            boxShadow:
              "0 0 0 6px rgba(255, 138, 61, 0) /* expanded glow radius */",
          },
        },
      },
      animation: {
        "pulse-glow":
          "pulse-glow 2s ease-out infinite /* 2s cycle easing outward */",
      },
    },
  },
  plugins: [],
};
