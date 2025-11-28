import { Checkbox } from "@/components/common";

/**
 * 업종(테마) 선택 섹션
 * - DB에서 가져온 산업 데이터를 테마로 표시
 * - 디자인 시안에 맞춘 UI 구성
 */
interface UniverseThemeSelectionProps {
  // 산업 관련
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
    <div className="space-y-6">
      {/* 업종(테마) 선택 섹션 */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <span className="font-semibold whitespace-nowrap">업종 (86)</span>
          <Checkbox
            checked={isAllIndustriesSelected}
            onChange={onToggleAllIndustries}
            label="전체선택"
            variant="danger"
          />
        </div>
        {/* 반응형 그리드 - 화면 크기에 따라 컬럼 수 조정 */}
        <div className="grid grid-cols-[repeat(auto-fill,minmax(100px,1fr))] gap-2 sm:gap-3">
          {industries.map((industry) => (
            <Checkbox
              key={industry}
              checked={selectedIndustries.has(industry)}
              onChange={() => onToggleIndustry(industry)}
              label={industry}
              variant="danger"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
