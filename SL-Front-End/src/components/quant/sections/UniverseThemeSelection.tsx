import { CheckboxGroup } from "../common";

/**
 * 유니버스 및 테마 선택 섹션
 * - 주식 유니버스 선택 (코스피 대형, 중형 등)
 * - 주식 테마 선택 (건설, 금융 등)
 */
interface UniverseThemeSelectionProps {
  industries: string[];
  themeOptions: Array<{ id: string; name: string }>;
  selectedIndustries: Set<string>;
  selectedThemes: Set<string>;
  isAllIndustriesSelected: boolean;
  isAllThemesSelected: boolean;
  onToggleIndustry: (industry: string) => void;
  onToggleTheme: (themeId: string) => void;
  onToggleAllIndustries: () => void;
  onToggleAllThemes: () => void;
}

export function UniverseThemeSelection({
  industries,
  themeOptions,
  selectedIndustries,
  selectedThemes,
  isAllIndustriesSelected,
  isAllThemesSelected,
  onToggleIndustry,
  onToggleTheme,
  onToggleAllIndustries,
  onToggleAllThemes,
}: UniverseThemeSelectionProps) {
  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      {/* 주식 유니버스 선택 */}
      <CheckboxGroup
        title="주식 유니버스 선택"
        items={industries.map((ind) => ({ id: ind, label: ind }))}
        selectedIds={selectedIndustries}
        onToggleItem={onToggleIndustry}
        onToggleAll={onToggleAllIndustries}
        columns={6}
        className="mb-6"
      />

      {/* 주식 테마 선택 */}
      <CheckboxGroup
        title="주식 테마 선택"
        items={themeOptions.map((theme) => ({ id: theme.id, label: theme.name }))}
        selectedIds={selectedThemes}
        onToggleItem={onToggleTheme}
        onToggleAll={onToggleAllThemes}
        columns={6}
      />
    </div>
  );
}
