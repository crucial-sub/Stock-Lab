"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { Header } from "./Header";
import { SideNav } from "./SideNav";

const BARE_LAYOUT_ROUTES = ["/login", "/signup"];

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const isBareLayout = BARE_LAYOUT_ROUTES.includes(pathname);

  if (isBareLayout) {
    return <main className="min-h-screen bg-bg-app">{children}</main>;
  }

  return (
    <>
      <Header />
      <SideNav />
      <main className="relative min-h-screen bg-bg-app pt-[12.5rem] lg:pl-64">
        <div className="relative z-10 w-full lg:px-[3.75rem]">{children}</div>
      </main>
    </>
  );
}
