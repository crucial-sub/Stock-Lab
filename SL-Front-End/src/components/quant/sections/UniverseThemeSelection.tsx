import { Checkbox } from "@/components/common";
import type { UniverseInfo } from "@/types/universe";

/**
 * 주식 유니버스 & 테마 선택 섹션
 * - 시가총액 기준 유니버스 선택
 * - DB에서 가져온 산업 데이터를 테마로 표시
 * - 디자인 시안에 맞춘 UI 구성
 */
interface UniverseThemeSelectionProps {
  // 유니버스 관련
  universes?: UniverseInfo[];
  selectedUniverses?: Set<string>;
  isAllUniversesSelected?: boolean;
  onToggleUniverse?: (universeId: string) => void;
  onToggleAllUniverses?: () => void;
  // 산업 관련
  industries: string[];
  selectedIndustries: Set<string>;
  isAllIndustriesSelected: boolean;
  onToggleIndustry: (industry: string) => void;
  onToggleAllIndustries: () => void;
}

export function UniverseThemeSelection({
  universes = [],
  selectedUniverses = new Set(),
  isAllUniversesSelected = false,
  onToggleUniverse,
  onToggleAllUniverses,
  industries,
  selectedIndustries,
  isAllIndustriesSelected,
  onToggleIndustry,
  onToggleAllIndustries,
}: UniverseThemeSelectionProps) {
  // 유니버스를 시장별로 그룹화
  const kospiUniverses = universes.filter((u) => u.market === "KOSPI");
  const kosdaqUniverses = universes.filter((u) => u.market === "KOSDAQ");

  return (
    <div className="space-y-6">
      {/* 주식 유니버스 선택 섹션 */}
      {universes.length > 0 && onToggleUniverse && (
        <div>
          <div className="flex items-center gap-3 mb-3">
            <span className="font-semibold">주식 유니버스</span>
            {onToggleAllUniverses && (
              <Checkbox
                checked={isAllUniversesSelected}
                onChange={onToggleAllUniverses}
                label="전체선택"
                variant="danger"
              />
            )}
          </div>

          {/* 코스피 유니버스 */}
          {kospiUniverses.length > 0 && (
            <div className="mb-3">
              <div className="grid grid-cols-6 gap-3">
                {kospiUniverses.map((universe) => (
                  <Checkbox
                    key={universe.id}
                    checked={selectedUniverses.has(universe.id)}
                    onChange={() => onToggleUniverse(universe.id)}
                    label={universe.name}
                    variant="danger"
                  />
                ))}
              </div>
            </div>
          )}

          {/* 코스닥 유니버스 */}
          {kosdaqUniverses.length > 0 && (
            <div>
              <div className="grid grid-cols-6 gap-3">
                {kosdaqUniverses.map((universe) => (
                  <Checkbox
                    key={universe.id}
                    checked={selectedUniverses.has(universe.id)}
                    onChange={() => onToggleUniverse(universe.id)}
                    label={universe.name}
                    variant="danger"
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 주식 테마 선택 섹션 */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <span className="font-semibold">업종 (86)</span>
          <Checkbox
            checked={isAllIndustriesSelected}
            onChange={onToggleAllIndustries}
            label="전체선택"
            variant="danger"
          />
        </div>
        <div className="grid grid-cols-6 gap-3">
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
