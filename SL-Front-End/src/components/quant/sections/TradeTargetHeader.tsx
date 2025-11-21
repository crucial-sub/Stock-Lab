import { Title } from "@/components/common";

/**
 * 매매 대상 헤더 섹션
 * - 제목 및 선택된 종목 수 표시
 */
interface TradeTargetHeaderProps {
  selectedCount: number;
  totalCount: number;
}

export function TradeTargetHeader({
  selectedCount,
  totalCount,
}: TradeTargetHeaderProps) {
  return (
    <div className="flex gap-3">
      <Title>매매 대상 설정</Title>
      <p className="text-[0.75rem] self-end mb-1">
        매매할 대상을 선정합니다. 매매 대상에 포함되지 않는 종목은 매수 조건을
        충족했을 때도 매매르 하지 않습니다.
      </p>
    </div>
  );
}

/**
 * 종목 카운트 표시
 */
interface StockCountProps {
  selectedCount: number;
  totalCount: number;
  hasUniverseFilter?: boolean;
}

export function StockCount({
  selectedCount,
  totalCount,
  hasUniverseFilter = false,
}: StockCountProps) {
  return (
    <div className="mb-5">
      <div className="flex items-end">
        <Title variant="subtitle">매매 대상 종목</Title>
        <span className="text-[1.25rem] ml-3 text-brand-primary font-semibold">
          {selectedCount} 종목
        </span>
        <span className="text-[1.25rem] font-semibold">/ {totalCount} 종목</span>
        <span className="ml-1 mb-1 text-[0.75rem] ">(선택 / 전체)</span>
      </div>
      {hasUniverseFilter && selectedCount > 0 && (
        <div className="mt-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-xs text-blue-700">
            <strong>ℹ️ 유니버스 필터 적용됨</strong>
            <br />
            표시된 종목 수는 선택한 업종의 전체 종목 수입니다.
            실제 백테스트 실행 시 선택한 유니버스(시가총액 구간) 필터가 추가로 적용되어
            종목 수가 줄어들 수 있습니다.
          </p>
        </div>
      )}
    </div>
  );
}
