import { useState, useEffect, useRef } from "react";
import { useBacktestConfigStore } from "@/stores";

/**
 * 매매 대상 선택 커스텀 훅
 * - 산업(테마) 선택 로직 캡슐화
 * - 전체 선택/개별 선택 관리
 * - 백테스트 설정 스토어와 동기화
 */
export function useTradeTargetSelection(
  industries: string[],
  _unused: Array<{ id: string; name: string }>,
  individualStocks: string[] = [],
  selectedStockCount: number = 0,
  totalStockCount: number = 0
) {
  const { setTradeTargets } = useBacktestConfigStore();
  const individualStocksRef = useRef<string[]>(individualStocks);

  // individualStocks 참조 업데이트
  useEffect(() => {
    individualStocksRef.current = individualStocks;
  }, [individualStocks]);

  // 선택된 산업 (초기에는 모두 선택됨)
  const [selectedIndustries, setSelectedIndustries] = useState<Set<string>>(
    new Set()
  );
  const [isInitialized, setIsInitialized] = useState(false);

  // industries가 로드되면 모두 선택 상태로 초기화 (최초 1회만)
  useEffect(() => {
    if (industries.length > 0 && !isInitialized) {
      setSelectedIndustries(new Set(industries));
      setIsInitialized(true);
    }
  }, [industries, isInitialized]);

  // 전체선택 여부 확인
  const isAllIndustriesSelected = industries.every((ind) =>
    selectedIndustries.has(ind)
  );

  // 선택된 산업과 개별 종목을 전역 스토어에 업데이트
  useEffect(() => {
    const themes = Array.from(selectedIndustries);
    const allSelected = industries.every((ind) => selectedIndustries.has(ind));

    setTradeTargets({
      use_all_stocks: allSelected && individualStocksRef.current.length === 0,
      selected_universes: [], // 유니버스는 사용하지 않음
      selected_themes: themes, // 산업을 테마로 전달
      selected_stocks: individualStocksRef.current, // 개별 선택된 종목
      selected_stock_count: selectedStockCount, // 선택된 종목 수 (ref 대신 직접 사용)
      total_stock_count: totalStockCount, // 전체 종목 수 (ref 대신 직접 사용)
    });
  }, [selectedIndustries, industries, setTradeTargets, selectedStockCount, totalStockCount]);

  // 전체선택 토글
  const toggleAllIndustries = () => {
    if (isAllIndustriesSelected) {
      setSelectedIndustries(new Set());
    } else {
      setSelectedIndustries(new Set(industries));
    }
  };

  // 산업 토글
  const toggleIndustry = (industry: string) => {
    const newSelected = new Set(selectedIndustries);
    if (newSelected.has(industry)) {
      newSelected.delete(industry);
    } else {
      newSelected.add(industry);
    }
    setSelectedIndustries(newSelected);
  };

  return {
    selectedIndustries,
    isAllIndustriesSelected,
    toggleAllIndustries,
    toggleIndustry,
  };
}
