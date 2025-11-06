import { Header } from "@/components/Header";
import { SideNav } from "@/components/SideNav";
import "@/styles/globals.css";
import type { Metadata } from "next";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Stock Lab - 퀀트 투자 백테스트",
  description: "입문자를 위한 퀀트 투자 백테스트 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="relative antialiased">
        <Providers>
          <Header />
          <SideNav />
          <main className="relative min-h-screen pt-24 pl-64">
            <div className="relative z-10">{children}</div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
