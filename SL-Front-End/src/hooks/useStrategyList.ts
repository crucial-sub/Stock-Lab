import { useState, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { axiosInstance } from "@/lib/axios";
import type { Strategy } from "@/types/strategy";
import type { MyStrategiesResponse } from "@/lib/api/strategy";

/**
 * 전략 쿼리 키
 */
const strategyQueryKey = {
  all: ["strategies"] as const,
  lists: () => [...strategyQueryKey.all, "list"] as const,
  my: () => [...strategyQueryKey.lists(), "my"] as const,
};

/**
 * 전략 목록 관리 커스텀 훅
 * - 서버에서 직접 데이터 fetch
 * - 전략 목록 상태 관리
 * - 선택, 검색, 삭제 등의 로직 처리
 *
 * Note: React Compiler가 자동으로 메모이제이션을 처리하므로 useCallback 제거
 */
export function useStrategyList() {
  // 선택된 전략 ID 배열
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // 검색 키워드
  const [searchKeyword, setSearchKeyword] = useState("");

  // React Query Client (캐시 무효화용)
  const queryClient = useQueryClient();

  // 서버에서 데이터 fetch
  const { data: strategyData, isLoading, error } = useQuery<MyStrategiesResponse, Error>({
    queryKey: strategyQueryKey.my(),
    queryFn: async () => {
      const response = await axiosInstance.get<MyStrategiesResponse>("/strategies/my");
      return response.data;
    },
    staleTime: 1000 * 30, // 30초
  });

  // API 응답을 Strategy 타입으로 변환
  const allStrategies = useMemo<Strategy[]>(() => {
    if (!strategyData?.strategies) return [];

    return strategyData.strategies.map((item) => ({
      id: item.sessionId,
      name: item.strategyName,
      dailyAverageReturn: item.statistics?.annualizedReturn
        ? item.statistics.annualizedReturn / 365
        : 0,
      cumulativeReturn: item.statistics?.totalReturn ?? 0,
      maxDrawdown: item.statistics?.maxDrawdown ?? 0,
      createdAt: new Date(item.createdAt).toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).replace(/\. /g, ".").replace(/\.$/, ""),
      status: item.status,
      progress: item.progress,
    }));
  }, [strategyData]);

  // 검색 키워드에 따라 필터링된 전략 목록
  const strategies = useMemo(() => {
    if (!searchKeyword.trim()) {
      return allStrategies;
    }
    return allStrategies.filter((s) =>
      s.name.toLowerCase().includes(searchKeyword.toLowerCase())
    );
  }, [allStrategies, searchKeyword]);

  /**
   * 개별 전략 선택/해제
   */
  const toggleStrategy = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((strategyId) => strategyId !== id) : [...prev, id]
    );
  };

  /**
   * 전체 전략 선택/해제
   */
  const toggleAllStrategies = () => {
    if (selectedIds.length === strategies.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(strategies.map((s) => s.id));
    }
  };

  /**
   * 검색 키워드 업데이트
   */
  const updateSearchKeyword = (keyword: string) => {
    setSearchKeyword(keyword);
  };

  /**
   * 선택된 전략 삭제
   * - 서버 API 호출 및 캐시 무효화
   */
  const deleteSelectedStrategies = async () => {
    if (selectedIds.length === 0) return;

    const confirmed = window.confirm(
      `선택한 ${selectedIds.length}개의 백테스트를 삭제하시겠습니까?`
    );

    if (!confirmed) return;

    try {
      // API 호출 - 백테스트 세션 삭제
      await axiosInstance.delete("/strategies/sessions", {
        data: { session_ids: selectedIds }
      });

      // React Query 캐시 무효화 (목록 자동 갱신)
      queryClient.invalidateQueries({ queryKey: strategyQueryKey.my() });

      // 선택 상태 초기화
      setSelectedIds([]);

      alert("백테스트가 삭제되었습니다.");
    } catch (error) {
      console.error("백테스트 삭제 실패:", error);
      alert("백테스트 삭제 중 오류가 발생했습니다.");
    }
  };

  /**
   * 전략 목록 새로고침
   */
  const refreshStrategies = async () => {
    // React Query 캐시 무효화하여 재fetch
    queryClient.invalidateQueries({ queryKey: strategyQueryKey.my() });
  };

  return {
    // 상태
    strategies,
    selectedIds,
    searchKeyword,
    isLoading,
    error,

    // 액션
    toggleStrategy,
    toggleAllStrategies,
    updateSearchKeyword,
    deleteSelectedStrategies,
    refreshStrategies,
  };
}
