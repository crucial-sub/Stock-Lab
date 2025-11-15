import { SideNav } from "@/components/SideNav";
import "@/styles/globals.css";
import type { Metadata } from "next";
import { Providers } from "./providers";
import { cookies } from "next/headers";

export const metadata: Metadata = {
  title: "Stock Lab - 퀀트 투자 백테스트",
  description: "입문자를 위한 퀀트 투자 백테스트 플랫폼",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // 쿠키에서 로그인 상태 확인
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  const isLoggedIn = !!token;

  return (
    <html lang="ko">
      <body className="flex h-screen overflow-hidden antialiased">
        <Providers>
          <SideNav isLoggedIn={isLoggedIn} />
          <main className="flex-1 h-full overflow-auto bg-background">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
