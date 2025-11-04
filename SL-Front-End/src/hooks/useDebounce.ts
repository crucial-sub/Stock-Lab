import { useEffect, useState } from "react";

/**
 * 디바운스(Debounce) 커스텀 훅
 *
 * 입력값이 변경될 때 일정 시간(delay) 후에만 값을 업데이트하여
 * 과도한 렌더링이나 API 호출을 방지한다.
 *
 * @param value - 디바운스를 적용할 값
 * @param delay - 지연 시간 (밀리초), 기본값 300ms
 * @returns 디바운스가 적용된 값
 *
 * @example
 * const [searchQuery, setSearchQuery] = useState("");
 * const debouncedQuery = useDebounce(searchQuery, 300);
 *
 * useEffect(() => {
 *   // debouncedQuery가 변경될 때만 검색 실행
 *   performSearch(debouncedQuery);
 * }, [debouncedQuery]);
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // 타이머 설정: delay 이후에 값 업데이트
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // 클린업: 값이 변경되면 이전 타이머 취소
    // 이를 통해 마지막 입력 후 delay 시간이 지난 후에만 값이 업데이트됨
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
