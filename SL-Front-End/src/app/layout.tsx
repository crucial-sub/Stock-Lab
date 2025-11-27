import { SideNav } from "@/components/SideNav";
import "@/styles/globals.css";
import type { Metadata } from "next";
import { cookies } from "next/headers";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Stock Lab - 퀀트 투자 백테스트",
  description: "입문자를 위한 퀀트 투자 백테스트 플랫폼",
};

/**
 * 루트 레이아웃 (반응형)
 *
 * @description 모든 페이지의 기본 레이아웃입니다.
 *
 * @features
 * - 모바일 (<640px): 전체 너비 메인 콘텐츠, 오버레이 사이드바
 * - 태블릿 (640-1024px): 사이드바 + 메인 콘텐츠
 * - 데스크톱 (>1024px): 확장 사이드바 + 메인 콘텐츠
 */
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const hasToken = !!token;

  return (
    <html lang="ko">
      <body className="flex h-screen overflow-hidden antialiased">
        <Providers>
          <SideNav serverHasToken={hasToken} />
          {/*
            메인 콘텐츠 영역
            - 모바일: 전체 너비, 상단 패딩 (햄버거 메뉴 공간)
            - 태블릿/데스크톱: 사이드바 옆 flex-1
          */}
          <main className="flex-1 h-full overflow-auto bg-background pt-16 sm:pt-0">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
