import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import { AUTH_TOKEN_COOKIE_KEY } from "@/lib/auth/token";
import { MyPageClient } from "./MyPageClient";

export default async function MyPage() {
  // 서버에서 쿠키 읽기
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_TOKEN_COOKIE_KEY)?.value;

  // 토큰이 없으면 로그인 페이지로 리다이렉트
  if (!token) {
    redirect("/login");
  }

  // 서버에서 사용자 정보 확인
  try {
    const user = await authApi.getCurrentUserServer(token);

    // 서버에서 날짜 포맷팅 (Hydration 오류 방지)
    const formattedCreatedAt = new Date(user.created_at).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });

    // 인증 성공 - 클라이언트 컴포넌트로 사용자 정보 전달
    return <MyPageClient initialUser={user} formattedCreatedAt={formattedCreatedAt} />;
  } catch (error) {
    // 인증 실패 (토큰 만료 등) - 로그인 페이지로 리다이렉트
    redirect("/login");
  }
}
