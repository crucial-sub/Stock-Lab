import { HomePageClient } from "./HomePageClient";

/**
 * 홈 페이지 (서버 컴포넌트)
 *
 * @description 메인 홈 화면의 진입점입니다.
 * 서버에서 인증 상태를 확인하고, 적절한 화면을 렌더링합니다.
 *
 * @future
 * - 로그인 여부 확인: const session = await getServerSession();
 * - 로그인 안 되어 있으면: return <LoginPrompt />;
 * - 로그인 되어 있으면: return <HomePageClient userName={session.user.name} />;
 */

export default async function HomePage() {
  // TODO: 인증 구현 후 활성화
  // const session = await getServerSession();
  //
  // if (!session) {
  //   return <LoginPrompt />;
  // }

  // 임시로 하드코딩된 사용자 이름 (나중에 session.user.name으로 교체)
  return <HomePageClient userName="은따거" />;
}
