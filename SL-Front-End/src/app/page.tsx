import { cookies } from "next/headers";
import { HomePageClient } from "./HomePageClient";
import { authApi } from "@/lib/api/auth";
import { autoTradingApi } from "@/lib/api/auto-trading";
import { kiwoomApi } from "@/lib/api/kiwoom";

/**
 * 홈 페이지 (서버 컴포넌트)
 *
 * @description 메인 홈 화면의 진입점입니다.
 * 서버에서 로그인 상태를 확인하고 클라이언트 컴포넌트에 전달합니다.
 */
export default async function HomePage() {
  // 쿠키에서 토큰 확인하여 로그인 여부 판단
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const isLoggedIn = !!token;

  let userName = "게스트";
  let hasKiwoomAccount = false;
  let kiwoomAccountData = null;
  let dashboardData = {
    total_assets: 0,
    total_return: 0,
    total_profit: 0,
    active_strategy_count: 0,
    total_positions: 0,
    total_trades_today: 0,
  };

  if (isLoggedIn && token) {
    try {
      // 1. 사용자 정보 가져오기
      const userInfo = await authApi.getCurrentUserServer(token);
      userName = userInfo.nickname || "사용자";
      hasKiwoomAccount = userInfo.has_kiwoom_account || false;

      // 2. 키움 계좌 연동되어 있으면 잔고 조회
      if (hasKiwoomAccount) {
        try {
          const kiwoomStatus = await kiwoomApi.getStatusServer(token);
          if (kiwoomStatus.is_connected) {
            const accountResponse = await kiwoomApi.getAccountBalanceServer(token);
            // API 응답이 { data, message } 형태일 수 있어 데이터 필드 우선 사용
            kiwoomAccountData = (accountResponse as { data?: unknown }).data ?? accountResponse;
          }
        } catch (error) {
          console.warn("키움 계좌 데이터 조회 실패:", error);
        }
      }

      // 3. 포트폴리오 대시보드 데이터 가져오기
      try {
        dashboardData = await autoTradingApi.getPortfolioDashboardServer(token);
      } catch (error) {
        console.warn("대시보드 데이터 조회 실패:", error);
      }
    } catch (error) {
      console.error("Failed to fetch user info:", error);
    }
  }

  return (
    <HomePageClient
      userName={userName}
      isLoggedIn={isLoggedIn}
      hasKiwoomAccount={hasKiwoomAccount}
      kiwoomAccountData={kiwoomAccountData}
      dashboardData={dashboardData}
    />
  );
}
