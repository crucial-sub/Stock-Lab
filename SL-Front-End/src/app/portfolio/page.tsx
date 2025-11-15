import { PortfolioPageClient } from "./PortfolioPageClient";

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

// 임시 Mock 데이터
const MOCK_DASHBOARD_DATA = {
  totalAssets: 10000000,
  totalAssetsChange: 184.0,
  weeklyProfit: 23141122,
  weeklyProfitChange: 99.99,
  activePortfolioCount: 99,
};

const MOCK_PORTFOLIOS = [
  {
    id: "1",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: true,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
  {
    id: "2",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: false,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
  {
    id: "3",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: false,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
  {
    id: "4",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: false,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
  {
    id: "5",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: false,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
  {
    id: "6",
    title: "포트폴리오 이름",
    profitRate: 99.99,
    isActive: false,
    lastModified: "25.12.31",
    createdAt: "25.12.31",
  },
];

export default async function PortfolioPage() {
  // TODO: API에서 데이터 가져오기
  // const dashboardData = await fetchDashboardData();
  // const portfolios = await fetchPortfolios();

  return (
    <PortfolioPageClient
      {...MOCK_DASHBOARD_DATA}
      portfolios={MOCK_PORTFOLIOS}
    />
  );
}
