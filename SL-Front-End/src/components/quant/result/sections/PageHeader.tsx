/**
 * Result 페이지 헤더 섹션
 * - 페이지 제목 및 액션 버튼
 */
interface PageHeaderProps {
  title?: string;
  subtitle?: string;
  onBack?: () => void;
  onRetryBacktest?: () => void;
}

export function PageHeader({
  title = "매매 결과",
  subtitle,
  onBack,
  onRetryBacktest,
}: PageHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-6">
      <div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-sm text-gray-500 hover:text-gray-700 mb-1"
          >
            ← 돌아가기
          </button>
        )}
        <h1 className="text-[2rem] font-bold text-text-strong leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
