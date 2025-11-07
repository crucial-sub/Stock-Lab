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
    },
    extend: {
      fontFamily: {
        sans: ["Pretendard Variable", "sans-serif"],
        circular: ["Circular Std", "sans-serif"],
      },
      colors: {
        bg: {
          app: "var(--color-bg-app) /* #f4f9ff */", /* 전체 페이지 공통 배경 */
          surface: "var(--color-surface) /* #ffffff */", /* 카드/패널 기본 표면 */
          muted: "var(--color-surface-muted) /* #eff6ff */", /* 옅은 구분 섹션 */
          positive: "var(--color-surface-positive) /* #fff6f6 */", /* 상승/알림 영역 */
        },
        text: {
          strong: "var(--color-text-strong) /* #000000 */", /* 제목/헤더 텍스트 */
          body: "var(--color-text-body) /* #505050 */", /* 일반 본문 텍스트 */
          muted: "var(--color-text-muted) /* #a0a0a0 */", /* 부가 설명/타임스탬프 */
        },
        brand: {
          primary: "var(--color-brand-primary) /* #ff6464 */", /* 주 브랜드/CTA */
        },
        accent: {
          primary: "var(--color-accent-primary) /* #007dfc */", /* 링크/포커스 */
          secondary: "var(--color-accent-secondary) /* #4c7cff */", /* 보조 블루 하이라이트 */
          success: "var(--color-success) /* #00cd00 */", /* 긍정 지표/태그 텍스트 */
        },
        tag: {
          neutral: "var(--color-tag-neutral) /* #c8c8c8 */", /* 중립 pill 테두리/텍스트 */
        },
        newsTag: {
          positive: "var(--color-news-positive-bg) /* #ddffe5 */", /* 뉴스 긍정 태그 배경 */
          positiveText: "var(--color-news-positive-text) /* #00cd00 */", /* 뉴스 긍정 태그 텍스트 */
          neutral: "var(--color-news-neutral-bg) /* #fff1d6 */", /* 뉴스 중립 태그 배경 */
          neutralText: "var(--color-news-neutral-text) /* #ffaa00 */", /* 뉴스 중립 태그 텍스트 */
          negative: "var(--color-news-negative-bg) /* #ffe5e5 */", /* 뉴스 부정 태그 배경 */
          negativeText: "var(--color-news-negative-text) /* #ff6464 */", /* 뉴스 부정 태그 텍스트 */
          theme: "var(--color-news-theme-bg) /* #f4e2ff */", /* 뉴스 테마 태그 배경 */
          themeText: "var(--color-news-theme-text) /* #a000fc */", /* 뉴스 테마 태그 텍스트 */
          press: "var(--color-news-press-bg) /* #eaf5ff */", /* 뉴스 언론사 태그 배경 */
          pressText: "var(--color-news-press-text) /* #007dfc */", /* 뉴스 언론사 태그 텍스트 */
        },
        border: {
          DEFAULT: "var(--color-border-default) /* #c8c8c8 */", /* 컴포넌트 외곽선 */
          subtle: "var(--color-border-subtle) /* #e1e1e1 */", /* 카드 내부 구분선 */
        },
      },
      boxShadow: {
        header: "var(--shadow-header) /* 0px 4px 16px rgba(150,150,150,0.10) */",
        card: "var(--shadow-card-soft) /* 0px 0px 8px rgba(0,0,0,0.10) */",
        "card-muted":
          "var(--shadow-card-muted) /* 0px 0px 8px rgba(0,0,0,0.08) */",
      },
      borderRadius: {
        xs: "var(--radius-xs) /* 2px */",
        sm: "var(--radius-sm) /* 4px */",
        md: "var(--radius-md) /* 8px */",
        lg: "var(--radius-lg) /* 12px */",
        xl: "var(--radius-xl) /* 16px */",
      },
    },
  },
  plugins: [],
};
