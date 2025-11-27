/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/hooks/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
    "./src/contexts/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: {
        sm: "1rem /* 16px */",
        md: "2rem /* 32px */",
        lg: "3rem /* 48px */",
      },
    },
    extend: {
      /* 폰트 패밀리 */
      fontFamily: {
        sans: ["Pretendard Variable", "system-ui", "sans-serif"],
        pretendard: ["Pretendard Variable", "sans-serif"],
        circular: ["Circular Std", "sans-serif"],
      },

      /* 1) 팔레트 레이어: 필요하면 직접 text-navy-900 이런 걸로도 쓸 수 있음 */
      colors: {
        // Base
        "base-0": "rgb(var(--color-base-0) / <alpha-value>) /* #FFFFFF */",
        "base-soft-blue":
          "rgb(var(--color-base-soft-blue) / <alpha-value>) /* #EFF4FF */",

        // Nav / Gray
        "navy-900": "rgb(var(--color-navy-900) / <alpha-value>) /* #182234 */",
        "gray-400": "rgb(var(--color-gray-400) / <alpha-value>) /* #C8C8C8 */",
        "gray-600": "rgb(var(--color-gray-600) / <alpha-value>) /* #646464 */",
        "gray-700": "rgb(var(--color-gray-700) / <alpha-value>) /* #505050 */",

        // Brand / State
        "brand-purple":
          "rgb(var(--color-brand-purple) / <alpha-value>) /* #AC64FF */",
        "red-500": "rgb(var(--color-red-500) / <alpha-value>) /* #FF6464 */",
        "blue-500": "rgb(var(--color-blue-500) / <alpha-value>) /* #007DFC */",
        "orange-400":
          "rgb(var(--color-orange-400) / <alpha-value>) /* #FFAC64 */",
        "green-600":
          "rgb(var(--color-green-600) / <alpha-value>) /* #1A8F00 */",
        black: "rgb(var(--color-black) / <alpha-value>) /* #000000 */",

        // 그라데이션 stop용 (semantic → from/via/to에 사용)
        "app-main-from":
          "rgb(var(--bg-app-main-from) / <alpha-value>) /* #FFFFFF */",
        "app-main-via":
          "rgb(var(--bg-app-main-via) / <alpha-value>) /* #EFF4FF */",
        "app-main-to":
          "rgb(var(--bg-app-main-to) / <alpha-value>) /* #EFF4FF */",
      },

      /* 2) 역할 기반 Background 색 */
      backgroundColor: (theme) => ({
        ...theme("colors"),

        // 레이아웃
        sidebar: "rgb(var(--bg-sidebar) / <alpha-value>) /* #182234 */",
        "sidebar-item-active": "var(--bg-sidebar-item-active) /* #FFFFFF33 */",
        "sidebar-item-sub-active":
          "var(--bg-sidebar-item-sub-active) /* #FFFFFF0D */",

        surface: "var(--bg-surface) /* navy-900 5% → #1822340D 근사값 */",
        "button-primary-soft": "var(--bg-button-primary-soft) /* #AC64FF80 */",
        "brand-soft": "var(--bg-brand-soft) /* #AC64FF0D */",
        "price-up": "var(--bg-price-up) /* #FF6464 */",
        "price-up-soft": "var(--bg-price-up-soft) /* #FFF6F6 */",
        "price-down": "var(--bg-price-down) /* #007DFC */",
        "price-down-soft": "var(--bg-price-down-soft) /* #007DFC33 */",

        "tag-portfolio-active": "var(--bg-tag-portfolio-active) /* #FFAC64 */",

        overlay: "var(--bg-overlay) /* #00000033 */", // 모달 뒷배경
      }),

      /* 3) 역할 기반 Text 색 */
      textColor: (theme) => ({
        ...theme("colors"),

        body: "rgb(var(--text-body) / <alpha-value>) /* #000000 */",

        "sidebar-item":
          "rgb(var(--text-sidebar-item) / <alpha-value>) /* #C8C8C8 */",
        "sidebar-item-active":
          "rgb(var(--text-sidebar-item-active) / <alpha-value>) /* #FFFFFF */",

        muted: "rgb(var(--text-muted) / <alpha-value>) /* #646464 */",

        brand: "rgb(var(--text-brand) / <alpha-value>) /* #AC64FF */",

        "price-up": "rgb(var(--text-price-up) / <alpha-value>) /* #FF6464 */",
        "price-down":
          "rgb(var(--text-price-down) / <alpha-value>) /* #007DFC */",

        "tag-portfolio-active":
          "rgb(var(--text-tag-portfolio-active) / <alpha-value>) /* #FFFFFF */",

        positive: "rgb(var(--text-positive) / <alpha-value>) /* #1A8F00 */",
      }),

      /* 4) 역할 기반 Border 색 */
      borderColor: (theme) => ({
        ...theme("colors"),

        sidebar: "rgb(var(--border-sidebar) / <alpha-value>) /* #505050 */",
        "sidebar-item-active":
          "rgb(var(--border-sidebar-item-active) / <alpha-value>) /* #FFFFFF */",

        surface: "var(--border-surface) /* #18223433 */",
        "brand-soft": "var(--border-brand-soft) /* #AC64FF33 */",
      }),

      /* 5) 역할 기반 Box Shadow */
      boxShadow: {
        // shadow-elev-sm
        "elev-sm":
          "var(--shadow-elev-sm) /* 0px 0px 8px 0px rgba(0, 0, 0, 0.05) */",

        // 브랜드 포커스/호버용
        "elev-brand":
          "var(--shadow-elev-brand) /* 0px 0px 8px 0px rgba(172, 100, 255, 0.2) */",

        // 메인 카드/패널
        "elev-card":
          "var(--shadow-elev-card) /* 0px 0px 8px 4px rgba(0, 0, 0, 0.1) */",

        // 서브 카드/인풋
        "elev-card-soft":
          "var(--shadow-elev-card-soft) /* 0px 0px 8px 0px rgba(0, 0, 0, 0.1) */",

        // 강한 강조(모달 등)
        "elev-strong":
          "var(--shadow-elev-strong) /* 0px 0px 8px 0px rgba(0, 0, 0, 0.2) */",
      },

      /* 6) 역할 기반 Border Radius */
      borderRadius: {
        xs: "var(--radius-xs) /* 2px */",
        sm: "var(--radius-sm) /* 4px */",
        md: "var(--radius-md) /* 8px */",
        lg: "var(--radius-lg) /* 12px */",
        xl: "var(--radius-xl) /* 16px */",
      },

      /* 7) 커서 깜빡임 애니메이션 (StreamingMarkdownRenderer용) */
      animation: {
        blink: "blink 1s step-end infinite",
      },
      keyframes: {
        blink: {
          "0%, 50%": { opacity: "1" },
          "50.01%, 100%": { opacity: "0" },
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
