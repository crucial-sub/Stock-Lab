import { useState, useCallback } from "react";
import type { Strategy } from "@/types/strategy";

/**
 * 전략 목록 관리 커스텀 훅
 * - 전략 목록 상태 관리
 * - 선택, 검색, 삭제 등의 로직 처리
 * - 향후 서버 연동을 위한 구조 준비
 */
export function useStrategyList(initialStrategies: Strategy[] = []) {
  // 전략 목록 상태
  const [strategies, setStrategies] = useState<Strategy[]>(initialStrategies);

  // 선택된 전략 ID 배열
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // 검색 키워드
  const [searchKeyword, setSearchKeyword] = useState("");

  // 로딩 상태
  const [isLoading, setIsLoading] = useState(false);

  /**
   * 개별 전략 선택/해제
   */
  const toggleStrategy = useCallback((id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((strategyId) => strategyId !== id) : [...prev, id]
    );
  }, []);

  /**
   * 전체 전략 선택/해제
   */
  const toggleAllStrategies = useCallback(() => {
    if (selectedIds.length === strategies.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(strategies.map((s) => s.id));
    }
  }, [selectedIds.length, strategies]);

  /**
   * 검색 키워드 업데이트
   */
  const updateSearchKeyword = useCallback((keyword: string) => {
    setSearchKeyword(keyword);
  }, []);

  /**
   * 검색 실행
   * TODO: 향후 서버 API 연동 예정
   */
  const executeSearch = useCallback(async () => {
    setIsLoading(true);
    try {
      // TODO: API 호출
      // const response = await fetch(`/api/strategies?keyword=${searchKeyword}`);
      // const data = await response.json();
      // setStrategies(data.strategies);

      // 현재는 로컬 필터링
      if (searchKeyword.trim()) {
        const filtered = initialStrategies.filter((s) =>
          s.name.toLowerCase().includes(searchKeyword.toLowerCase())
        );
        setStrategies(filtered);
      } else {
        setStrategies(initialStrategies);
      }
    } catch (error) {
      console.error("검색 실패:", error);
    } finally {
      setIsLoading(false);
    }
  }, [searchKeyword, initialStrategies]);

  /**
   * 선택된 전략 삭제
   * TODO: 향후 서버 API 연동 예정
   */
  const deleteSelectedStrategies = useCallback(async () => {
    if (selectedIds.length === 0) return;

    const confirmed = window.confirm(
      `선택한 ${selectedIds.length}개의 전략을 삭제하시겠습니까?`
    );

    if (!confirmed) return;

    setIsLoading(true);
    try {
      // TODO: API 호출
      // await fetch('/api/strategies', {
      //   method: 'DELETE',
      //   body: JSON.stringify({ strategyIds: selectedIds }),
      // });

      // 현재는 로컬 상태만 업데이트
      setStrategies((prev) => prev.filter((s) => !selectedIds.includes(s.id)));
      setSelectedIds([]);
    } catch (error) {
      console.error("삭제 실패:", error);
      alert("전략 삭제 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [selectedIds]);

  /**
   * 전략 목록 새로고침
   * TODO: 향후 서버 API 연동 예정
   */
  const refreshStrategies = useCallback(async () => {
    setIsLoading(true);
    try {
      // TODO: API 호출
      // const response = await fetch('/api/strategies');
      // const data = await response.json();
      // setStrategies(data.strategies);

      setStrategies(initialStrategies);
    } catch (error) {
      console.error("목록 새로고침 실패:", error);
    } finally {
      setIsLoading(false);
    }
  }, [initialStrategies]);

  return {
    // 상태
    strategies,
    selectedIds,
    searchKeyword,
    isLoading,

    // 액션
    toggleStrategy,
    toggleAllStrategies,
    updateSearchKeyword,
    executeSearch,
    deleteSelectedStrategies,
    refreshStrategies,
  };
}
