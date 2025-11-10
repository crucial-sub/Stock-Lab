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
    <div>
      <h2 className="text-2xl font-bold text-text-strong mb-2">
        매매 대상 설정
      </h2>
      <p className="text-sm text-text-body">
        매매할 대상을 선택합니다. 여러 대상을 한번에길 있는 종목을 배제할 수도
        있고 종목별로 배제할 수도 있습니다.
      </p>
    </div>
  );
}

/**
 * 종목 카운트 표시
 */
export function StockCount({
  selectedCount,
  totalCount,
}: TradeTargetHeaderProps) {
  return (
    <div className="mb-4">
      <span className="text-lg font-bold text-text-strong">매매 대상 종목</span>
      <span className="ml-3 text-accent-primary font-bold">
        {selectedCount} 종목 / {totalCount} 종목
      </span>
      <span className="ml-2 text-sm text-text-body">(선택 / 전체)</span>
    </div>
  );
}
