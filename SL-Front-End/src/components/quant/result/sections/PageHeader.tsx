/**
 * Result 페이지 헤더 섹션
 * - 페이지 제목 및 액션 버튼
 */
interface PageHeaderProps {
  onRetryBacktest?: () => void;
}

export function PageHeader({ onRetryBacktest }: PageHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-6">
      <h1 className="text-[2rem] font-bold text-text-strong">매매 결과</h1>
    </div>
  );
}
