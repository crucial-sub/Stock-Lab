import { cookies } from "next/headers";
import { HomePageClient } from "./HomePageClient";

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

  // 로그인된 경우 사용자 정보 가져오기 (향후 구현)
  // TODO: 토큰으로 사용자 정보 API 호출
  let nickname = "게스트";

  if (isLoggedIn) {
    try {
      // 임시: 쿠키에서 사용자 닉네임 가져오기
      const nicknameCookie = cookieStore.get("nickname")?.value;
      nickname = nicknameCookie || "사용자";
    } catch (error) {
      console.error("Failed to fetch user info:", error);
    }
  }

  return <HomePageClient nickname={nickname} isLoggedIn={isLoggedIn} />;
}
