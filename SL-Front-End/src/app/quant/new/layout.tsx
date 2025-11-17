"use client";

import { useState } from "react";
import { SecondarySideNav } from "@/components/quant/layout/SecondarySideNav";

/**
 * Quant 라우트 레이아웃
 *
 * @description
 * - 2차 사이드바를 모든 quant 하위 페이지에 공통으로 표시
 * - 포트폴리오 목록 페이지(/quant)와 전략 생성 페이지(/quant/new) 공유
 */
export default function QuantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSecondarySidebarOpen, setIsSecondarySidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-app">
      {/* 2차 사이드바 */}
      <SecondarySideNav
        isOpen={isSecondarySidebarOpen}
        setIsOpen={setIsSecondarySidebarOpen}
      />

      {/* 페이지 컨텐츠 */}
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  );
}
