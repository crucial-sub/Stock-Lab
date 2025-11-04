"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "홈" },
    { href: "/quant", label: "퀀트 투자" },
    { href: "/mypage", label: "마이페이지" },
  ];

  return (
    <header className="border-border-default bg-bg-app px-[310px]">
      <div className="quant-container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold text-brand">Stock Lab</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-8">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-xl transition-colors ${
                pathname === item.href
                  ? "text-text-primary"
                  : "text-text-quarternary hover:text-text-primary"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Login Button */}
        <button type="button" className="text-sm text-text-primary">
          로그인
        </button>
      </div>
    </header>
  );
}
