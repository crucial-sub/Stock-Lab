"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "./common";

interface HeaderProps {
  userName?: string;
}

export function Header({
  userName = "은따거",
}: HeaderProps) {
  const router = useRouter();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // 로그인 상태 확인
    const token = localStorage.getItem("access_token");
    setIsLoggedIn(!!token);
  }, []);

  const handleCreateStrategy = () => {
    router.push("/quant/new");
  };

  const handleLogin = () => {
    router.push("/login");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
    router.push("/");
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50 h-24 w-full bg-white shadow-header">
      <div className="relative flex h-full items-center px-12 py-6">
        {/* Logo */}
        <Link href="/" className="font-circular">
          <div className="flex h-12 items-start">
            <span className="text-3xl font-medium text-brand-primary">stock</span>
            <span className="self-end text-3xl font-medium text-accent-primary">
              lab
            </span>
          </div>
        </Link>

        <div className="absolute left-[252px] right-10 flex items-center justify-between">
          {/* Welcome message */}
          <div>
            <p className="font-sans text-xl font-normal text-black">
              {userName}님, 환영합니다!
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex gap-[21px]">
            {isLoggedIn && (
              <Button variant="primary" size="md" onClick={handleCreateStrategy}>
                새 전략 만들기
              </Button>
            )}
            {isLoggedIn ? (
              <Button variant="secondary" size="md" onClick={handleLogout}>
                로그아웃
              </Button>
            ) : (
              <Button variant="secondary" size="md" onClick={handleLogin}>
                로그인
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}