import { useQuery } from "@tanstack/react-query";

import {
  fetchAvailableThemes,
  fetchNewsById,
  fetchNewsList,
} from "@/lib/api/news";
import type { NewsItem, NewsListParams } from "@/types/news";

const newsQueryKey = {
  all: ["news"] as const,
  list: (params: NewsListParams) =>
    [...newsQueryKey.all, "list", params] as const,
  detail: (id: string) => [...newsQueryKey.all, "detail", id] as const,
  themes: ["news", "themes"] as const,
};

export function useNewsListQuery(params: NewsListParams) {
  return useQuery<NewsItem[], Error>({
    queryKey: newsQueryKey.list(params),
    queryFn: () => fetchNewsList(params),
  });
}

export function useNewsDetailQuery(id?: string) {
  return useQuery<NewsItem | undefined, Error>({
    queryKey: id ? newsQueryKey.detail(id) : ["news-detail"],
    queryFn: () => (id ? fetchNewsById(id) : Promise.resolve(undefined)),
    enabled: !!id,
  });
}

export function useAvailableThemesQuery() {
  return useQuery<string[], Error>({
    queryKey: newsQueryKey.themes,
    queryFn: () => fetchAvailableThemes(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export { newsQueryKey };
