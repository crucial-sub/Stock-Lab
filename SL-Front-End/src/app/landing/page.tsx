import { LandingHero } from "@/components/landing/LandingHero";
import { LandingFeatures } from "@/components/landing/LandingFeatures";
import { LandingAI } from "@/components/landing/LandingAI";
import { LandingPerformance } from "@/components/landing/LandingPerformance";
import { LandingCTA } from "@/components/landing/LandingCTA";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingFloatingNav } from "@/components/landing/LandingFloatingNav";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ThemeToggle } from "@/components/landing/ThemeToggle";

export default function LandingPage() {
  return (
    <ThemeProvider>
      <div
        data-landing-root
        className="relative h-full min-h-screen overflow-y-auto snap-y snap-mandatory scroll-smooth bg-gradient-to-b from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors duration-300"
      >
        <ThemeToggle />
        <LandingHero />
        <LandingFeatures />
        <LandingAI />
        <LandingPerformance />
        <LandingCTA />
        <LandingFooter />
        <LandingFloatingNav />
      </div>
    </ThemeProvider>
  );
}
