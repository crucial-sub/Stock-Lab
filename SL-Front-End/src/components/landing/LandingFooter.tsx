"use client";

import Link from "next/link";

export function LandingFooter() {
  return (
    <footer
      id="landing-footer"
      className="relative snap-start py-12 px-6 border-t border-slate-200 dark:border-slate-800"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-black" />

      <div className="relative z-10 container mx-auto max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="inline-block mb-4">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Stock Lab
              </span>
            </Link>
            <p className="text-slate-400 text-sm max-w-md">
              고성능 백테스팅 엔진과 140여개 금융 팩터를 활용한 퀀트 투자 전략 시뮬레이션 플랫폼
            </p>
            <div className="mt-6 flex gap-4">
              <a
                href="https://github.com/Krafton-Jungle-10-Final-Project/Stock-Lab"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-blue-400 hover:border-blue-500 transition-all"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </a>
            </div>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">프로덕트</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/quant/backtest" className="text-slate-400 hover:text-blue-400 transition-colors">
                  백테스팅
                </Link>
              </li>
              <li>
                <Link href="/quant/strategies" className="text-slate-400 hover:text-blue-400 transition-colors">
                  전략 관리
                </Link>
              </li>
              <li>
                <Link href="/ai-assistant" className="text-slate-400 hover:text-blue-400 transition-colors">
                  AI 어시스턴트
                </Link>
              </li>
              <li>
                <Link href="/market-price" className="text-slate-400 hover:text-blue-400 transition-colors">
                  시장 시황
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-white font-semibold mb-4">회사</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/about" className="text-slate-400 hover:text-blue-400 transition-colors">
                  소개
                </Link>
              </li>
              <li>
                <Link href="/community" className="text-slate-400 hover:text-blue-400 transition-colors">
                  커뮤니티
                </Link>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">
                  블로그
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-blue-400 transition-colors">
                  문의하기
                </a>
              </li>
            </ul>
          </div>
        </div>
        <p className="text-slate-500 text-sm">
          © 2025 Stock Lab. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
