import { Header } from "@/components/Header";
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
      <body className="antialiased">
        <Providers>
          <div className="bg-empty-layer">
            <div className="bg-ellipse-1" />
            <div className="bg-ellipse-2" />
            <div className="bg-ellipse-3" />
          </div>
          <Header />
          <main className="relative">
            <div className="relative z-10">{children}</div>
          </main>
        </Providers>
      </body>
    </html>
  );
}
