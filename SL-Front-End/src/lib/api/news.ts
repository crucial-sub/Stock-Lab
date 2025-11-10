import type { NewsItem, NewsListParams } from "@/types/news";

const MOCK_NEWS: NewsItem[] = [
  {
    id: "news-1",
    title: "제목의 위치는 여기입니다.",
    subtitle: "여기에 부제목이 들어갑니다.",
    summary:
      "여기에 간단한 내용이 들어갑니다. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
    content:
      "Lorem Ipsum is simply dummy text of the printing and typesetting industry. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.",
    tickerLabel: "종목 이름",
    themeName: "테마명",
    sentiment: "positive",
    publishedAt: "2025년 12월 31일 14시 30분",
    source: "https://www.naver.com/example/link",
    link: "https://www.naver.com/example/link",
    pressName: "언론사 이름",
  },
  {
    id: "news-2",
    title: "테마와 관련된 뉴스 제목입니다.",
    subtitle: "서브 타이틀이 여기에 들어갑니다.",
    summary:
      "이 내용은 테마와 연관된 뉴스의 요약입니다. Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker.",
    content:
      "상세 본문입니다. Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
    tickerLabel: "테마 종목",
    themeName: "전기 / 전자",
    sentiment: "neutral",
    publishedAt: "2025년 12월 31일 13시 30분",
    source: "https://www.naver.com/example/link2",
    link: "https://www.naver.com/example/link2",
    pressName: "언론사 이름",
  },
  {
    id: "news-3",
    title: "시장의 흐름을 보여주는 기사입니다.",
    subtitle: "시장 관련 부제목",
    summary:
      "시장 전반에 대한 내용을 포함합니다. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.",
    content:
      "추가적인 설명이 들어갑니다. This provides more details about the article for modal display and can span multiple paragraphs.",
    tickerLabel: "시장 전체",
    themeName: "금속",
    sentiment: "negative",
    publishedAt: "2025년 12월 31일 12시 30분",
    source: "https://www.naver.com/example/link3",
    link: "https://www.naver.com/example/link3",
    pressName: "언론사 이름",
  },
];

function applyFilters(data: NewsItem[], params?: NewsListParams) {
  if (!params) return data;
  let filtered = [...data];

  if (params.keyword) {
    const keyword = params.keyword.toLowerCase();
    filtered = filtered.filter(
      (item) =>
        item.title.toLowerCase().includes(keyword) ||
        item.summary.toLowerCase().includes(keyword) ||
        item.content.toLowerCase().includes(keyword) ||
        item.tickerLabel.toLowerCase().includes(keyword),
    );
  }

  if (params.themes && params.themes.length) {
    filtered = filtered.filter((item) =>
      params.themes?.some((theme) => item.themeName?.includes(theme) ?? false),
    );
  }

  return filtered;
}

export async function fetchNewsList(params?: NewsListParams): Promise<NewsItem[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(applyFilters(MOCK_NEWS, params));
    }, 200);
  });
}

export async function fetchNewsById(id: string): Promise<NewsItem | undefined> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_NEWS.find((item) => item.id === id));
    }, 150);
  });
}
