import { CheckboxGroup } from "../common";

/**
 * 주식 테마 선택 섹션
 * - DB에서 가져온 산업 데이터를 테마로 표시
 */
interface UniverseThemeSelectionProps {
  industries: string[];
  selectedIndustries: Set<string>;
  isAllIndustriesSelected: boolean;
  onToggleIndustry: (industry: string) => void;
  onToggleAllIndustries: () => void;
}

export function UniverseThemeSelection({
  industries,
  selectedIndustries,
  isAllIndustriesSelected,
  onToggleIndustry,
  onToggleAllIndustries,
}: UniverseThemeSelectionProps) {
  return (
    <div className="bg-bg-surface rounded-lg shadow-card p-6">
      {/* 주식 테마 선택 (DB에서 가져온 산업 데이터) */}
      <CheckboxGroup
        title="주식 테마 선택"
        items={industries.map((ind) => ({ id: ind, label: ind }))}
        selectedIds={selectedIndustries}
        onToggleItem={onToggleIndustry}
        onToggleAll={onToggleAllIndustries}
        isAllSelected={isAllIndustriesSelected}
        columns={6}
      />
    </div>
  );
}
