/**
 * Result 페이지 헤더 섹션
 * - 페이지 제목 및 액션 버튼
 */
interface PageHeaderProps {
  onRetryBacktest?: () => void;
  onLogout?: () => void;
}

export function PageHeader({ onRetryBacktest, onLogout }: PageHeaderProps) {
  return (
    <div className="flex justify-between items-center mb-6">
      <h1 className="text-[2rem] font-bold text-text-strong">매매 결과</h1>
      <div className="flex gap-3">
        <button
          onClick={onRetryBacktest}
          className="px-4 py-2 bg-accent-primary text-white rounded-sm font-medium hover:bg-accent-primary/90 transition-colors"
        >
          백테스트 다시하기
        </button>
        <button
          onClick={onLogout}
          className="px-4 py-2 bg-bg-surface text-text-body rounded-sm font-medium hover:bg-bg-muted transition-colors"
        >
          로그아웃
        </button>
      </div>
    </div>
  );
}
