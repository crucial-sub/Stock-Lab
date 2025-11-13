import { axiosInstance } from "../axios";
import type { NewsItem, NewsListParams } from "@/types/news";

interface NewsListResponse {
  total: number;
  news: NewsItem[];
}

/**
 * DB에서 뉴스 목록 조회
 * - 키워드 검색: 제목, 내용, 회사명, 출처에서 검색
 * - 테마 필터: 테마명으로 필터링
 */
export async function fetchNewsList(params?: NewsListParams): Promise<NewsItem[]> {
  try {
    // 테마 필터만 있는 경우 (우선순위 1)
    if (params?.themes && params.themes.length && !params.themes.includes("전체")) {
      // 모든 테마에 대해 데이터 수집
      const allNews: NewsItem[] = [];
      for (const theme of params.themes) {
        const response = await axiosInstance.get<NewsListResponse>("/news/db/theme", {
          params: {
            theme,
            limit: 100,
          },
        });
        allNews.push(...(response.data.news ?? []));
      }
      return allNews;
    }

    // 키워드가 있으면 검색 API 사용 (우선순위 2)
    if (params?.keyword && params.keyword.trim()) {
      const response = await axiosInstance.get<NewsListResponse>("/news/db/search", {
        params: {
          keyword: params.keyword,
          limit: 100,
        },
      });

      let filtered = response.data.news ?? [];

      // 테마로 추가 필터링 (키워드 + 테마)
      if (params.themes && params.themes.length && !params.themes.includes("전체")) {
        filtered = filtered.filter((item: NewsItem) =>
          params.themes?.some((theme) => item.themeName?.includes(theme) ?? false)
        );
      }

      return filtered;
    }

    // 기본: 모든 뉴스 조회 (최근 뉴스부터)
    const response = await axiosInstance.get<NewsListResponse>("/news/db/search", {
      params: {
        keyword: "뉴스",
        limit: 100,
      },
    });

    return response.data.news ?? [];
  } catch (error) {
    console.error("Failed to fetch news list:", error);
    return [];
  }
}

/**
 * 뉴스 상세 조회
 */
export async function fetchNewsById(id: string): Promise<NewsItem | undefined> {
  try {
    const response = await axiosInstance.get<NewsListResponse>("/news/db/search", {
      params: {
        keyword: "",
        limit: 1,
      },
    });

    // ID로 필터링 (실제로는 상세 조회 엔드포인트가 있으면 그걸 사용)
    const news = response.data.news?.find((item: NewsItem) => item.id === id);
    return news;
  } catch (error) {
    console.error("Failed to fetch news detail:", error);
    return undefined;
  }
}

/**
 * DB에 실제로 존재하는 테마 목록 조회
 */
export async function fetchAvailableThemes(): Promise<string[]> {
  try {
    const response = await axiosInstance.get<{
      themes: string[];
      count: number;
      retrieved_at: string;
    }>("/news/db/themes/available");
    return response.data.themes ?? [];
  } catch (error) {
    console.error("Failed to fetch available themes:", error);
    return [];
  }
}
