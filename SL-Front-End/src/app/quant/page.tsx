// 1. External imports (라이브러리)
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

// 2. Internal imports (프로젝트 내부)
import { strategyApi } from "@/lib/api/strategy";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { formatDateToCard } from "@/lib/date-utils";
import { PortfolioPageClient } from "./PortfolioPageClient";

// 포트폴리오 타입 정의 (PortfolioPageClient의 Portfolio 타입과 동일)
interface Portfolio {
  id: string;
  strategyId: string;
  title: string;
  profitRate: number;
  isActive: boolean;
  lastModified: string;
  createdAt: string;
}

/**
 * 포트폴리오 페이지 (서버 컴포넌트)
 *
 * @description 사용자의 포트폴리오 목록과 대시보드를 표시하는 페이지
 * 서버에서 포트폴리오 데이터를 가져와 클라이언트 컴포넌트에 전달합니다.
 *
 * @requires 로그인 필수 페이지
 */
export default async function PortfolioPage() {
  // 로그인 여부 확인 (redirect는 try-catch 밖에서 처리)
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;

  if (!token) {
    // 로그인 안 된 경우 로그인 페이지로 리다이렉트
    redirect("/login?redirect=/quant");
  }

  // 서버에서 전략 목록 데이터 가져오기
  try {
    // 1. 백테스트 전략 목록 가져오기
    const data = await strategyApi.getMyStrategiesServer(token);

    // 2. 자동매매 활성화된 전략 목록 가져오기
    let autoTradingStrategies: any[] = [];
    try {
      autoTradingStrategies = await autoTradingApi.getMyAutoTradingStrategiesServer(token);
    } catch (error) {
      console.warn("자동매매 전략 조회 실패:", error);
    }

    // 백테스트 전략을 Portfolio 형태로 변환
    const backtestPortfolios: Portfolio[] = data.strategies.map((strategy) => ({
      id: strategy.sessionId,
      strategyId: strategy.strategyId,
      title: strategy.strategyName,
      profitRate: strategy.totalReturn ?? 0,
      isActive: strategy.isActive,
      lastModified: formatDateToCard(strategy.updatedAt),
      createdAt: formatDateToCard(strategy.createdAt),
    }));

    // 자동매매 전략을 Portfolio 형태로 변환
    const autoTradingPortfolios: Portfolio[] = autoTradingStrategies
      .filter((s) => s.is_active) // 활성화된 것만
      .map((strategy) => ({
        id: `auto-${strategy.strategy_id}`, // 고유한 ID 생성
        strategyId: strategy.strategy_id,
        title: `🤖 자동매매 활성화됨`,
        profitRate: 0, // TODO: 실제 수익률 계산 필요
        isActive: true,
        lastModified: formatDateToCard(strategy.activated_at || strategy.created_at),
        createdAt: formatDateToCard(strategy.created_at),
      }));

    // 두 리스트 합치기
    const portfolios: Portfolio[] = [...backtestPortfolios, ...autoTradingPortfolios];

    // 3. 실제 자동매매 대시보드 데이터 가져오기
    let dashboardData = {
      total_assets: 0,
      total_return: 0,
      total_profit: 0,
      active_strategy_count: 0,
      total_positions: 0,
      total_trades_today: 0,
    };

    try {
      dashboardData = await autoTradingApi.getPortfolioDashboardServer(token);
    } catch (error) {
      console.warn("대시보드 데이터 조회 실패:", error);
    }

    const totalAssets = Number(dashboardData.total_assets) || 0;
    const totalAssetsChange = Number(dashboardData.total_return) || 0;
    const weeklyProfit = Number(dashboardData.total_profit) || 0;
    const weeklyProfitChange = Number(dashboardData.total_return) || 0;
    const activeCount = Number(dashboardData.active_strategy_count) || 0;

    return (
      <PortfolioPageClient
        totalAssets={totalAssets}
        totalAssetsChange={totalAssetsChange}
        weeklyProfit={weeklyProfit}
        weeklyProfitChange={weeklyProfitChange}
        activePortfolioCount={activeCount}
        portfolios={portfolios}
      />
    );
  } catch (error: unknown) {
    // 401 에러 (인증 실패): 토큰 만료 또는 유효하지 않음 -> 로그인 페이지로 리다이렉트
    if (
      (error as { response?: { status?: number } })?.response?.status === 401
    ) {
      redirect("/login?redirect=/quant");
    }

    console.error("Error fetching strategies:", error);

    // 기타 에러 발생 시 빈 데이터로 렌더링
    return (
      <PortfolioPageClient
        totalAssets={0}
        totalAssetsChange={0}
        weeklyProfit={0}
        weeklyProfitChange={0}
        activePortfolioCount={0}
        portfolios={[]}
      />
    );
  }
}
