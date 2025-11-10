import { useState, useEffect } from "react";
import { useBacktestConfigStore } from "@/stores";

/**
 * 매매 대상 선택 커스텀 훅
 * - 유니버스 및 테마 선택 로직 캡슐화
 * - 전체 선택/개별 선택 관리
 * - 백테스트 설정 스토어와 동기화
 */
export function useTradeTargetSelection(
  industries: string[],
  themeOptions: Array<{ id: string; name: string }>
) {
  const { setTradeTargets } = useBacktestConfigStore();

  // 선택된 산업 및 테마 (초기에는 모두 선택됨)
  const [selectedIndustries, setSelectedIndustries] = useState<Set<string>>(
    new Set()
  );
  const [selectedThemes, setSelectedThemes] = useState<Set<string>>(
    new Set(themeOptions.map((t) => t.id))
  );

  // industries가 로드되면 모두 선택 상태로 초기화
  useEffect(() => {
    if (industries.length > 0 && selectedIndustries.size === 0) {
      setSelectedIndustries(new Set(industries));
    }
  }, [industries, selectedIndustries.size]);

  // 전체선택 여부 확인
  const isAllIndustriesSelected = industries.every((ind) =>
    selectedIndustries.has(ind)
  );
  const isAllThemesSelected = themeOptions.every((theme) =>
    selectedThemes.has(theme.id)
  );

  // 유니버스 전체선택 토글
  const toggleAllIndustries = () => {
    if (isAllIndustriesSelected) {
      setSelectedIndustries(new Set());
    } else {
      setSelectedIndustries(new Set(industries));
    }
  };

  // 테마 전체선택 토글
  const toggleAllThemes = () => {
    if (isAllThemesSelected) {
      setSelectedThemes(new Set());
    } else {
      setSelectedThemes(new Set(themeOptions.map((t) => t.id)));
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

  // 테마 토글
  const toggleTheme = (themeId: string) => {
    const newSelected = new Set(selectedThemes);
    if (newSelected.has(themeId)) {
      newSelected.delete(themeId);
    } else {
      newSelected.add(themeId);
    }
    setSelectedThemes(newSelected);
  };

  // 선택된 유니버스와 테마를 전역 스토어에 업데이트
  useEffect(() => {
    const universes = Array.from(selectedIndustries);
    const themes = Array.from(selectedThemes);

    setTradeTargets({
      use_all_stocks: isAllIndustriesSelected && isAllThemesSelected,
      selected_universes: universes,
      selected_themes: themes,
      selected_stocks: [], // 개별 종목 선택은 추후 구현
    });
  }, [
    selectedIndustries,
    selectedThemes,
    isAllIndustriesSelected,
    isAllThemesSelected,
    setTradeTargets,
  ]);

  return {
    selectedIndustries,
    selectedThemes,
    isAllIndustriesSelected,
    isAllThemesSelected,
    toggleAllIndustries,
    toggleAllThemes,
    toggleIndustry,
    toggleTheme,
  };
}
