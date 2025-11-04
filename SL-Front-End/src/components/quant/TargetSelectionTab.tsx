"use client";

import { Checkbox, Panel } from "@/components/common";
import { useThemesQuery } from "@/hooks/useThemesQuery";
import { useBacktestConfigStore } from "@/stores";
import { useEffect, useState } from "react";
import { ShowBacktestStrategyButton } from "./ShowBacktestStrategyButton";

/**
 * 매매 대상 선택 탭 컴포넌트
 *
 * - SSR로 prefetch된 테마 데이터 사용
 * - 선택된 테마들을 BacktestRunRequest의 target_stocks 형식으로 전역 상태에 저장
 * - target_stocks: string[] (테마명 배열)
 */
export function TargetSelectionTab() {
  // SSR로 prefetch된 테마 목록 사용
  const { data: themes, isLoading: isLoadingThemes } = useThemesQuery();

  // 전역 백테스트 설정 스토어
  const { target_stocks, getBacktestRequest } = useBacktestConfigStore();

  // 선택된 테마 ID를 Set으로 관리 (빠른 조회를 위함)
  const [selectedThemeIds, setSelectedThemeIds] = useState<Set<string>>(
    new Set(),
  );


  /**
   * 테마 선택/해제 토글 핸들러
   * @param themeId 테마 ID
   * @param themeName 테마 이름
   */
  const toggleTheme = (themeId: string, themeName: string) => {
    const newSelected = new Set(selectedThemeIds);
    if (newSelected.has(themeId)) {
      newSelected.delete(themeId);
    } else {
      newSelected.add(themeId);
    }
    setSelectedThemeIds(newSelected);
  };

  /**
   * 선택된 테마 목록이 변경될 때마다 전역 스토어에 업데이트
   * selectedThemeIds → target_stocks (테마명 배열)
   */
  useEffect(() => {
    if (!themes) return;

    // 선택된 테마 ID를 테마명으로 변환
    const selectedThemeNames = themes
      .filter((theme) => selectedThemeIds.has(theme.id))
      .map((theme) => theme.name);

    // 전역 스토어 업데이트 (BacktestRunRequest의 target_stocks 형식)
    useBacktestConfigStore.setState({ target_stocks: selectedThemeNames });
  }, [selectedThemeIds, themes]);

  // 로딩 중일 때
  if (isLoadingThemes) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-text-secondary">테마 데이터를 불러오는 중...</div>
      </div>
    );
  }

  // 테마 데이터가 없을 때
  if (!themes || themes.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-text-secondary">
          사용 가능한 테마가 없습니다.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 테마 선택 영역 */}
      <div className="relative flex justify-center mt-[40px]">
        <Panel variant="glass" className="w-[1000px] p-[28px]">
          <div className="grid grid-cols-5 gap-x-[35px] gap-y-[28px]">
            {themes.map((theme) => (
              <Checkbox
                key={theme.id}
                checked={selectedThemeIds.has(theme.id)}
                onChange={() => toggleTheme(theme.id, theme.name)}
                label={theme.name}
              />
            ))}
          </div>
        </Panel>
      </div>

      {/* 하단 버튼 영역 - 최종 조건 확인 버튼 */}
      <div className="flex justify-center pt-4">
        <ShowBacktestStrategyButton />
      </div>
    </div>
  );
}
