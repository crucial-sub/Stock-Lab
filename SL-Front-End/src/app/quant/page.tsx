// 1. External imports (라이브러리)
import Image from "next/image";

// 2. Internal imports (프로젝트 내부)
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Title } from "@/components/common/Title";
import { SearchBar } from "@/components/quant/list/SearchBar";
import { StrategyActions } from "@/components/quant/list/StrategyActions";
import { StrategyList } from "@/components/quant/list/StrategyList";
import { useStrategyList } from "@/hooks/useStrategyList";

/**
 * 포트폴리오 페이지 (서버 컴포넌트)
 *
 * @description 사용자의 포트폴리오 목록과 대시보드를 표시하는 페이지
 * 서버에서 포트폴리오 데이터를 가져와 클라이언트 컴포넌트에 전달합니다.
 *
 * @future
 * - 실시간 HTS 연동: 장이 열렸을 때 실시간으로 잔고 및 수익 변화 반영
 * - API에서 포트폴리오 데이터 가져오기: const data = await fetchPortfolios();
 * - 사용자별 포트폴리오 필터링
 * - 포트폴리오 정렬 및 검색 기능
 */


export default async function PortfolioPage() {
  // TODO: API에서 데이터 가져오기
  // const dashboardData = await fetchDashboardData();
  // const portfolios = await fetchPortfolios();

  // 전략 목록 관리 훅 (서버 fetch, 선택, 검색, 삭제 모두 포함)
  const {
    strategies,
    selectedIds,
    searchKeyword,
    isLoading,
    error,
    toggleStrategy,
    toggleAllStrategies,
    updateSearchKeyword,
    deleteSelectedStrategies,
  } = useStrategyList();

  // 로딩 상태
  if (isLoading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-background pb-[3.25rem]">
          <Title className="mb-5">내가 만든 전략 목록</Title>
          <div className="bg-bg-surface rounded-md p-5">
            <div className="flex items-center justify-center h-64">
              <p className="text-text-muted">백테스트 목록을 불러오는 중...</p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-background pb-[3.25rem]">
          <Title className="mb-5">내가 만든 전략 목록</Title>
          <div className="bg-bg-surface rounded-md p-5">
            <div className="flex items-center justify-center h-64">
              <p className="text-error">백테스트 목록을 불러오는데 실패했습니다.</p>
            </div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background pb-[3.25rem]">
        <Title className="mb-5">내가 만든 전략 목록</Title>
        <div className="bg-bg-surface rounded-md p-5">
          {/* 액션 버튼 (새 전략 만들기, 선택 전략 삭제) */}
          <div className="flex mb-6 justify-between">
            <StrategyActions
              selectedCount={selectedIds.length}
              onDelete={deleteSelectedStrategies}
            />
            <SearchBar
              value={searchKeyword}
              onChange={updateSearchKeyword}
            />
          </div>

          {/* 전략 테이블 */}
          <StrategyList
            strategies={strategies}
            selectedIds={selectedIds}
            onToggleAll={toggleAllStrategies}
            onToggleItem={toggleStrategy}
          />

          {/* 페이지네이션 */}
          <div className="h-8 py-1 flex justify-center items-center gap-[22px]">
            <button className="hover:bg-bg-surface-hover rounded transition-colors">
              <Image src="/icons/arrow_left.svg" alt="이전" width={24} height={24} />
            </button>
            <div>
              <button className="font-normal">1</button>
            </div>
            <button className="hover:bg-bg-surface-hover rounded transition-colors">
              <Image
                src="/icons/arrow_right.svg"
                alt="다음"
                width={24}
                height={24}
              />
            </button>
          </div>
        </div>

        {/* 하단 가이드 카드 */}
        <div className="mt-5 grid grid-cols-3 gap-6">
          <GuideCard
            icon="📈"
            title="퀀트 투자에 대해 알아보기 #1"
            descriptions={[
              "퀀트 투자가 처음이라면, 왜? 가이드를 읽어보세요!",
              "개발자가 퀀트 투자에 대해 자세히 설명해드립니다 😊",
            ]}
          />
          <GuideCard
            icon="📊"
            title="퀀트 투자에 대해 알아보기 #2"
            descriptions={[
              "퀀트 투자에 어느 정도 익숙하신가요?",
              "그렇다면 본격적으로 전략을 짜면 피봇하세요! 😊",
            ]}
          />
          <GuideCard
            icon="🤔"
            title="퀀트 투자에서 수익을 내려면?"
            descriptions={[
              "퀀트 투자에서도 많았던 수익을 내기가 너무 어렵다구요?",
              "왜? 가이드를 통해 같이 수익을 내어보아요! 😎",
            ]}
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}

/**
 * 가이드 카드 컴포넌트
 */
interface GuideCardProps {
  icon: string;
  title: string;
  descriptions: string[];
}

function GuideCard({ icon, title, descriptions }: GuideCardProps) {
  return (
    <div className="flex flex-col gap-3 bg-bg-surface rounded-md p-6 shadow-card">
      <h3 className="flex text-[1.5rem] font-semibold">
        {icon} {title}
      </h3>
      <div className="flex flex-col gap-[18px]">
        {descriptions.map((desc, index) => (
          <div key={`${desc}-${index}`} className="text-[18px] font-normal">
            {desc}
          </div>
        ))}
      </div>
    </div>
  );
}
