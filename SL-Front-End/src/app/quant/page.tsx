// 1. External imports (라이브러리)
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

// 2. Internal imports (프로젝트 내부)
import { strategyApi } from "@/lib/api/strategy";
import { formatDateToCard } from "@/lib/date-utils";
import { PortfolioPageClient } from "./PortfolioPageClient";

// 포트폴리오 타입 정의 (PortfolioPageClient의 Portfolio 타입과 동일)
interface Portfolio {
  id: string;
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
    // API 호출 - 서버 사이드 axios 인스턴스 사용 (토큰 수동 전달)
    const data = await strategyApi.getMyStrategiesServer(token);

    // API 응답을 PortfolioPageClient가 필요로 하는 형태로 변환
    const portfolios: Portfolio[] = data.strategies.map((strategy) => ({
      id: strategy.sessionId,
      title: strategy.strategyName,
      profitRate: strategy.totalReturn ?? 0,
      isActive: strategy.isActive,
      lastModified: formatDateToCard(strategy.updatedAt),
      createdAt: formatDateToCard(strategy.createdAt),
    }));

    // 대시보드 통계 계산
    // TODO: 실제로는 서버에서 별도 API로 받아와야 하지만,
    // 현재는 전략 목록 데이터로부터 계산
    const activeCount = portfolios.filter((p) => p.isActive).length;

    // 총 수익률 계산 (활성 포트폴리오들의 평균)
    const activePortfolios = portfolios.filter((p) => p.isActive);
    const avgReturn = activePortfolios.length > 0
      ? activePortfolios.reduce((sum, p) => sum + p.profitRate, 0) / activePortfolios.length
      : 0;

    // 임시 대시보드 데이터 (향후 별도 API로 교체 필요)
    const totalAssets = 10000000; // 초기 자산
    const totalAssetsChange = avgReturn;
    const weeklyProfit = totalAssets * (avgReturn / 100);
    const weeklyProfitChange = avgReturn;

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
  } catch (error: any) {
    // 401 에러 (인증 실패): 토큰 만료 또는 유효하지 않음 -> 로그인 페이지로 리다이렉트
    if (error?.response?.status === 401) {
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
