"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "./common";
import { Icon } from "./common/Icon";

interface SideNavProps {
}

export function SideNav({ }: SideNavProps) {
    const pathname = usePathname();
    const segments = pathname.split("/").filter(Boolean);
    const rootSegment = "/" + (segments[0] ?? "");

    const navItems = [
        { href: "/", label: "홈", icon: "/icons/home.svg" },
        { href: "/quant", label: "퀀트 투자", icon: "/icons/function.svg" },
        { href: "/market-price", label: "시세", icon: "/icons/bar-chart.svg" },
        { href: "/news", label: "뉴스", icon: "/icons/news.svg" },
        { href: "/mypage", label: "마이페이지", icon: "/icons/account-circle.svg" },
    ];

    return (
        <aside className="fixed left-0 top-0 z-40 flex h-full w-64 flex-col overflow-hidden border-r border-border-default bg-white">
            <div className="flex flex-col pt-40 pb-8 h-full justify-between">
                <nav className="flex flex-1 flex-col gap-3 px-6">
                    {navItems.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`relative flex h-12 items-center gap-3 rounded-lg px-4 transition-colors ${rootSegment == item.href ? "bg-bg-muted" : "hover:bg-slate-50"
                                }`}
                        >
                            <Icon
                                src={item.icon}
                                color={
                                    rootSegment == item.href
                                        ? "var(--color-accent-primary)"
                                        : "var(--color-border-default)"
                                }
                                size={20}
                            />
                            <span
                                className={`text-xl font-sans ${rootSegment == item.href
                                    ? "font-semibold text-accent-primary"
                                    : "font-light text-tag-neutral"
                                    }`}
                            >
                                {item.label}
                            </span>
                        </Link>
                    ))}
                </nav>
                <Button variant="tertiary" className="flex w-56 h-12 self-center gap-3 pr-[38px] justify-start">
                    <Icon
                        src={'icons/help.svg'}
                    />
                    <span>가이드 시작하기</span>
                </Button>
            </div>
        </aside>
    );
}
