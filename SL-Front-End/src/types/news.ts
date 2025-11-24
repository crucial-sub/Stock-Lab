export type NewsSentiment = "positive" | "neutral" | "negative";

export interface NewsItem {
  id: string;
  title: string;
  subtitle?: string;
  llm_summary?: string;
  summary: string;
  content: string;
  tickerLabel: string;
  stockCode?: string;
  themeName?: string;
  sentiment: NewsSentiment;
  publishedAt: string;
  source: string;
  link: string;
  theme: string;
  pressName?: string;
}

export interface NewsListParams {
  keyword?: string;
  themes?: string[];
  filter?: string;
  limit?: number;
}
