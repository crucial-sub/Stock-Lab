import { useQuery } from "@tanstack/react-query";

import { fetchNewsById, fetchNewsList } from "@/lib/api/news";
import type { NewsItem, NewsListParams } from "@/types/news";

const newsQueryKey = {
  all: ["news"] as const,
  list: (params: NewsListParams) => [...newsQueryKey.all, "list", params] as const,
  detail: (id: string) => [...newsQueryKey.all, "detail", id] as const,
};

export function useNewsListQuery(params: NewsListParams) {
  return useQuery<NewsItem[], Error>({
    queryKey: newsQueryKey.list(params),
    queryFn: () => fetchNewsList(params),
  });
}

export function useNewsDetailQuery(newsId?: string) {
  return useQuery<NewsItem | undefined, Error>({
    queryKey: newsQueryKey.detail(newsId ?? ""),
    queryFn: () => (newsId ? fetchNewsById(newsId) : Promise.resolve(undefined)),
    enabled: Boolean(newsId),
  });
}

export { newsQueryKey };
