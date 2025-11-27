"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useEffect, useState } from "react";

const sections = [
  { id: "landing-hero", label: "소개" },
  { id: "landing-features", label: "기능" },
  { id: "landing-ai", label: "AI" },
  { id: "landing-performance", label: "성능" },
  { id: "landing-cta", label: "시작" },
  { id: "landing-footer", label: "문의" },
];

export function LandingFloatingNav() {
  const [activeSection, setActiveSection] = useState(sections[0]?.id);

  useEffect(() => {
    const root = document.querySelector<HTMLElement>("[data-landing-root]");
    const observer = new IntersectionObserver(
      (entries) => {
        const mostVisible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (mostVisible?.target?.id) {
          setActiveSection(mostVisible.target.id);
        }
      },
      {
        root: root ?? null,
        threshold: [0.35, 0.6, 0.85],
      }
    );

    sections.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => observer.disconnect();
  }, []);

  const handleNavigate = (sectionId: string) => {
    const target = document.getElementById(sectionId);
    if (!target) return;

    target.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 w-full max-w-5xl -translate-x-1/2 px-4">
      <div className="pointer-events-auto flex items-center gap-3 rounded-2xl bg-white/85 px-4 py-3 shadow-2xl ring-1 ring-slate-200/80 backdrop-blur-xl dark:bg-slate-900/85 dark:ring-slate-700/70">
        <div className="flex flex-1 items-center gap-2 overflow-x-auto">
          {sections.map((section) => {
            const isActive = activeSection === section.id;

            return (
              <button
                key={section.id}
                type="button"
                onClick={() => handleNavigate(section.id)}
                className="relative overflow-hidden rounded-full border border-slate-200/80 px-4 py-2 text-sm font-semibold text-black transition-all hover:border-blue-400/80 hover:text-blue-600 dark:border-slate-700/80 dark:text-slate-200 dark:hover:border-blue-400/80 dark:hover:text-blue-300"
                aria-pressed={isActive}
              >
                {isActive && (
                  <motion.span
                    layoutId="landing-nav-active"
                    className="absolute inset-0 -z-10 bg-gradient-to-r from-blue-500/90 to-purple-500/90 shadow-lg"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative">{section.label}</span>
              </button>
            );
          })}
        </div>

        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 text-sm font-bold text-white shadow-lg transition-transform hover:scale-105"
        >
          시작하기
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
      </div>
    </div>
  );
}
