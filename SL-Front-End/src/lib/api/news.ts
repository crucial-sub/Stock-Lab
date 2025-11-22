import type { NewsItem, NewsListParams } from "@/types/news";
import { axiosInstance } from "../axios";

interface NewsListResponse {
  total: number;
  news: NewsItem[];
}

/**
 * DB에서 뉴스 목록 조회
 * - 키워드 검색: 제목, 내용, 회사명, 출처에서 검색
 * - 테마 필터: 테마명으로 필터링
 */
export async function fetchNewsList(
  params?: NewsListParams,
): Promise<NewsItem[]> {
  try {
    const limit = params?.limit ?? 100;

    // 테마 필터만 있는 경우 (리스트로 한번에 요청)
    if (params?.themes?.length && !params.themes.includes("전체")) {
      const response = await axiosInstance.get<NewsListResponse>(
        "/news/db/theme",
        {
          params: {
            themes: params.themes,
            limit,
          },
          paramsSerializer: {
            indexes: null, // themes=val1&themes=val2 형식으로 직렬화
          },
        },
      );
      return response.data.news ?? [];
    }

    // 키워드가 있으면 검색 API 사용
    if (params?.keyword?.trim()) {
      const response = await axiosInstance.get<NewsListResponse>(
        "/news/db/search",
        {
          params: {
            keyword: params.keyword,
            limit,
          },
        },
      );

      let filtered = response.data.news ?? [];

      //  키워드 + 테마 필터링
      if (params.themes?.length && !params.themes.includes("전체")) {
        filtered = filtered.filter((item: NewsItem) =>
          params.themes?.some(
            (theme) => item.themeName?.includes(theme) ?? false,
          ),
        );
      }

      return filtered;
    }

    // 기본: 모든 뉴스 조회 (최근 뉴스부터)
    const response = await axiosInstance.get<NewsListResponse>(
      "/news/db/search",
      {
        params: {
          keyword: "뉴스",
          limit,
        },
      },
    );

    return response.data.news ?? [];
  } catch (error) {
    console.error("Failed to fetch news list:", error);
    return [];
  }
}

/**
 * 최신 뉴스 조회 (id desc)
 */
export async function fetchLatestNews(limit = 5): Promise<NewsItem[]> {
  try {
    const response = await axiosInstance.get<NewsListResponse>(
      "/news/db/latest",
      {
        params: { limit },
      },
    );
    return response.data.news ?? [];
  } catch (error) {
    console.error("Failed to fetch latest news:", error);
    return [];
  }
}

/**
 * 뉴스 상세 조회
 */
export async function fetchNewsById(id: string): Promise<NewsItem | undefined> {
  try {
    const response = await axiosInstance.get<NewsItem>(`/news/db/detail/${id}`);
    return response.data;
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
