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
    <header className="border-border-default">
      <div className="quant-container flex h-[120px] pb-[8px] items-end justify-start">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-[1.8rem] font-bold text-brand mb-[-4px]">Stock Lab</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-6 pl-[60px]">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-[1.2rem] transition-colors ${
                pathname === item.href
                  ? "text-text-primary font-semibold hover:text-text-primary"
                  : "text-text-quarternary hover:text-text-primary hover:font-semibold"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Login Button */}
        <button type="button" className="ml-auto text-[1.2rem] font-medium text-text-primary">
          로그인
        </button>
      </div>
    </header>
  );
}
